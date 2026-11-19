"""Deterministic offline verifier for NON-NORMATIVE CONSULT proposal records.

TAXI-AGENT-CONSULT-STAGE-A-01 (Stage A, offline, disabled by default).

Scope
-----
* Records: CONSULT-REQUEST/1, CONSULT-REPLY/1, CONSULT-CLOSE/1. They are
  proposals outside active PROTOCOL v1 and are only ever evaluated here on
  synthetic input supplied by the caller.
* Output: ``Result(verdict, codes, effect)`` where ``verdict`` is one of
  ``PASS``, ``FAIL`` or ``NOT_VERIFIED`` and ``effect`` is always ``"NONE"``.
* Fail closed: missing authority, provenance, transport or identity evidence
  can never yield ``PASS``.
* Record text is untrusted data. It is parsed with regular expressions and
  compared; it is never executed, evaluated, followed or forwarded.

The module performs no I/O: no network, no filesystem, no subprocess, no
environment variables. Only the standard library modules imported below are
used. See ``docs/agents/consult/STAGE-A-PROPOSAL.md`` for the field tables
and the reason codes.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Verdicts, effect and reason codes
# ---------------------------------------------------------------------------

PASS = "PASS"
FAIL = "FAIL"
NOT_VERIFIED = "NOT_VERIFIED"
VERIFIED = "VERIFIED"
EFFECT_NONE = "NONE"

HEADER = "NON-NORMATIVE-CONSULT-PROPOSAL/1"

TYPE_REQUEST = "CONSULT-REQUEST"
TYPE_REPLY = "CONSULT-REPLY"
TYPE_CLOSE = "CONSULT-CLOSE"

MODE_COLLAB = "COLLABORATIVE_DEV"
MODE_INDEPENDENT_QA = "INDEPENDENT_QA"
SCOPE_ADVISORY = "advisory-only"

RISKS = ("LOW", "MEDIUM", "HIGH")
REPLY_STATUSES = ("ANSWERED", "CANNOT_ANSWER", "NEEDS_COORDINATOR")
CLOSE_STATES = ("ACCEPTED_AS_CONTEXT", "DECLINED", "EXPIRED", "CONFLICT", "ESCALATED")
KNOWN_AGENTS = ("claude-code", "claude-design", "deepseek-qa", "gpt")
COORDINATOR_AGENT = "gpt"
LEASE_ACTIVE = "ACTIVE"
SHARED_LOGINS = frozenset({"iprus2026-tech"})
DEFAULT_REPO = "iprus2026-tech/taxi-dashboard"

# Limits (bytes are UTF-8 bytes after NFC).
MAX_RECORD_BYTES = 16384
MAX_TEXT_BYTES = 4096
MAX_SCALAR_BYTES = 512
MAX_LIST_ITEMS = 16
DEFAULT_EXPIRY = timedelta(minutes=60)
MAX_EXPIRY = timedelta(hours=4)

# Severity of each reason code. Codes may carry a ``:detail`` suffix; the
# severity is looked up by the part before the first colon.
_FAIL_CODES = frozenset(
    {
        "ENCODING", "BOM", "NOT_NFC", "NOT_LF", "CONTROL_CHAR", "NON_CANONICAL",
        "RECORD_TOO_LARGE", "HEADER", "MALFORMED_LINE", "DUPLICATE_FIELD",
        "UNKNOWN_FIELD", "MISSING_FIELD", "FIELD_ORDER", "UNKNOWN_TYPE",
        "BAD_VERSION", "TEXT_TOO_LONG", "FIELD_TOO_LONG", "LIST_TOO_LONG",
        "BAD_TASK_ID", "BAD_CONSULT_ID", "BAD_SESSION",
        "BAD_SHA40", "BAD_SHA64", "BAD_TIMESTAMP", "BAD_ENUM", "BAD_PATH",
        "INVALID_LINK", "ROLE_UNKNOWN", "MODE_FORBIDDEN", "SCOPE_NOT_ADVISORY",
        "TS_IN_FUTURE", "EXPIRY_NOT_AFTER_TS", "EXPIRY_OVER_CAP",
        "EXPIRY_BEYOND_LEASE", "CONSULT_EXPIRED", "PARENT_LEASE_EXPIRED",
        "PARENT_LEASE_REVOKED", "CROSS_TASK", "SPEC_MISMATCH", "HEAD_MISMATCH",
        "SOURCE_REF_MISMATCH", "PATH_ESCALATION", "SOURCE_NOT_ASSIGNEE",
        "TARGET_NOT_AUTHORIZED", "SELF_CONSULT", "QA_FIREWALL",
        "QA_INDEPENDENCE_CONFLICT", "COMMENT_EDITED", "SNAPSHOT_MISMATCH",
        "REPLAYED_COMMENT", "CONFLICT", "CONSULT_ID_REUSED",
        "REQUEST_NOT_ACCEPTED", "REPLY_NOT_ACCEPTED", "REPLY_LINK_MISMATCH",
        "REQUEST_HASH_MISMATCH", "REPLY_HASH_MISMATCH", "REPLY_MISMATCH",
        "REPLY_OUTSIDE_WINDOW", "CLOSE_NOT_COORDINATOR", "CLOSE_STATE_INVALID",
        "FORGED_AUTHORITY", "PROMPT_INJECTION", "SECRET_DETECTED",
        "SENSITIVE_DATA", "IDENTITY_MISMATCH", "CONTEXT_INVALID",
    }
)
_NOT_VERIFIED_CODES = frozenset(
    {
        "AUTHORITY_NOT_VERIFIED", "PROVENANCE_NOT_VERIFIED",
        "TRANSPORT_NOT_VERIFIED", "IDENTITY_NOT_VERIFIED",
        "IDENTITY_SHARED_ACCOUNT", "TARGET_UNASSIGNED", "RISK_HIGH_ESCALATE",
        "CONSULT_TIMEOUT", "AWAITING_REPLY",
    }
)
_INFO_CODES = frozenset({"DUPLICATE_NOOP"})


def severity(code: str) -> str:
    """Return FAIL, NOT_VERIFIED or PASS (info) for a reason code."""
    base = code.split(":", 1)[0]
    if base in _FAIL_CODES:
        return FAIL
    if base in _NOT_VERIFIED_CODES:
        return NOT_VERIFIED
    if base in _INFO_CODES:
        return PASS
    # Unknown codes are a programming error; fail closed.
    return FAIL


@dataclass(frozen=True)
class Result:
    verdict: str
    codes: Tuple[str, ...]
    effect: str = EFFECT_NONE

    @property
    def ok(self) -> bool:
        return self.verdict == PASS


def _result(codes: Sequence[str]) -> Result:
    uniq: List[str] = []
    for c in codes:
        if c not in uniq:
            uniq.append(c)
    sev = {severity(c) for c in uniq}
    if FAIL in sev:
        verdict = FAIL
    elif NOT_VERIFIED in sev:
        verdict = NOT_VERIFIED
    else:
        verdict = PASS
    return Result(verdict=verdict, codes=tuple(uniq), effect=EFFECT_NONE)


# ---------------------------------------------------------------------------
# Field schema
# ---------------------------------------------------------------------------

S, T, L = "scalar", "text", "list"

REQUEST_FIELDS: Tuple[Tuple[str, str], ...] = (
    ("type", S), ("v", S), ("mode", S), ("task_id", S), ("consult_id", S),
    ("source_agent", S), ("source_session", S),
    ("target_agent", S), ("target_session", S),
    ("source_ref", S), ("source_head_sha", S), ("spec_sha256", S),
    ("ts_utc", S), ("expires_at_utc", S), ("risk", S), ("scope", S),
    ("question", T), ("source_paths", L), ("allowed_evidence", L),
)
REPLY_FIELDS: Tuple[Tuple[str, str], ...] = (
    ("type", S), ("v", S), ("mode", S), ("task_id", S), ("consult_id", S),
    ("source_agent", S), ("source_session", S),
    ("target_agent", S), ("target_session", S),
    ("in_reply_to", S), ("request_sha256", S),
    ("source_head_sha", S), ("spec_sha256", S), ("ts_utc", S),
    ("status", S), ("risk", S), ("scope", S),
    ("conflict_disclosure", T), ("prior_participation", T), ("answer", T),
    ("evidence", L),
)
CLOSE_FIELDS: Tuple[Tuple[str, str], ...] = (
    ("type", S), ("v", S), ("task_id", S), ("consult_id", S),
    ("source_agent", S), ("source_session", S),
    ("request_ref", S), ("request_sha256", S),
    ("reply_ref", S), ("reply_sha256", S),
    ("ts_utc", S), ("final_state", S), ("scope", S), ("rationale", T),
)
SCHEMAS: Mapping[str, Tuple[Tuple[str, str], ...]] = {
    TYPE_REQUEST: REQUEST_FIELDS,
    TYPE_REPLY: REPLY_FIELDS,
    TYPE_CLOSE: CLOSE_FIELDS,
}

# ---------------------------------------------------------------------------
# Regular expressions
# ---------------------------------------------------------------------------

TASK_ID_RE = re.compile(r"^TAXI-[A-Z0-9]+(-[A-Z0-9]+)*-[0-9]{2}(\.[0-9]+)?$")
CONSULT_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
SESSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{11,127}$")
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
SHA64_RE = re.compile(r"^[0-9a-f]{64}$")
TS_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_SEGMENT = r"[A-Za-z0-9_.][A-Za-z0-9._-]*"
PATH_RE = re.compile(r"^(?:%s/)*%s$" % (_SEGMENT, _SEGMENT))


def _repo_re(repo: str) -> str:
    owner, name = repo.split("/", 1)
    return re.escape(owner) + "/" + re.escape(name)


def blob_link(url: str, repo: str = DEFAULT_REPO) -> Optional[Tuple[str, str]]:
    """Return (sha, path) for an immutable blob permalink, else None."""
    m = re.match(
        r"^https://github\.com/%s/blob/([0-9a-f]{40})/(.+?)(?:#L[1-9][0-9]{0,5}(?:-L[1-9][0-9]{0,5})?)?$"
        % _repo_re(repo),
        url,
    )
    if not m or not valid_path(m.group(2)):
        return None
    return m.group(1), m.group(2)


def comment_link(url: str, repo: str = DEFAULT_REPO) -> Optional[Tuple[int, int]]:
    """Return (issue_number, comment_id) for an issue/PR comment permalink."""
    m = re.match(
        r"^https://github\.com/%s/(?:issues|pull)/([1-9][0-9]{0,6})#issuecomment-([1-9][0-9]{0,14})$"
        % _repo_re(repo),
        url,
    )
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def valid_path(p: str) -> bool:
    if not PATH_RE.match(p):
        return False
    return all(seg not in (".", "..") for seg in p.split("/"))


def glob_match(path: str, pattern: str) -> bool:
    """Match a repository path against a §4.2-style glob (``*``, ``?``, ``**``)."""
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.fullmatch("".join(out), path) is not None


def parse_ts(value: str) -> Optional[datetime]:
    """Strict RFC 3339 UTC ``YYYY-MM-DDTHH:MM:SSZ``; None if invalid."""
    if not isinstance(value, str) or not TS_RE.match(value):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def format_ts(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Untrusted-content scanners (heuristic, fail closed)
# ---------------------------------------------------------------------------

_AUTHORITY_PATTERNS = (
    re.compile(r"`{3}\s*(?:agent-msg|issue-spec)", re.I),
    re.compile(
        r"\btype\s*:\s*(?:ASSIGN|REASSIGN|RESUME|OWNER-DECISION|HANDOFF|QA-REPORT|SPEC|CLAIM|RELEASE|BLOCKED|CHECKPOINT|CONSULT-[A-Z]+)\b",
        re.I,
    ),
    re.compile(
        r"\b(?:decision|gate|lease_until|approved_sha|approved_sha256|approved_spec_sha256|claim_session|assignee|verdict)\s*:",
        re.I,
    ),
    re.compile(r"\b(?:ASSIGN|REASSIGN|RESUME|OWNER-DECISION)\b"),
    re.compile(r"\bG[0-3](?:-[a-z]+)?\b.{0,40}?\b(?:approve[sd]?|granted|passed)\b", re.I),
    re.compile(r"\b(?:approve[sd]?|grant(?:ed|s)?)\b.{0,40}?\bG[0-3]\b", re.I),
    re.compile(r"\b(?:push|merge|deploy|force-push|rebase)\b\s+(?:now|immediately|it|to\s+main)\b", re.I),
    re.compile(r"\b(?:extend|renew|prolong)\w*\s+(?:the\s+)?lease\b", re.I),
    re.compile(r"\bQA\s+(?:PASS|verdict)\b", re.I),
)

_INJECTION_PATTERNS = (
    re.compile(
        r"\b(?:ignore|disregard|forget|override|bypass)\b.{0,30}?\b(?:previous|prior|above|all|earlier|your|the)\b.{0,30}?\b(?:instructions?|rules|controls|polic(?:y|ies)|guardrails|protocol)\b",
        re.I,
    ),
    re.compile(r"\bsystem\s+prompt\b", re.I),
    re.compile(r"\byou\s+are\s+now\b", re.I),
    re.compile(r"\b(?:act|acting|speak|speaking)\s+as\s+(?:the\s+)?(?:owner|coordinator|admin)\b", re.I),
    re.compile(r"\bI\s+am\s+the\s+(?:owner|coordinator|admin)\b", re.I),
    re.compile(r"\b(?:developer|god|jailbreak)\s+mode\b", re.I),
    re.compile(r"</?\s*(?:system|assistant|tool)\s*>", re.I),
    re.compile(r"(?:__import__|\beval\s*\(|\bexec\s*\(|os\.system|subprocess|\brm\s+-rf\b|\bcurl\s+https?://)", re.I),
    re.compile(r"(?:игнорируй|забудь|отмени).{0,30}?(?:инструкц|правил|огранич)", re.I),
)

_SECRET_PATTERNS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"\b[ps]k\.eyJ[A-Za-z0-9_.-]{10,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token)\s*[=:]\s*\S{6,}", re.I),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{16,}=*", re.I),
)

_SENSITIVE_PATTERNS = (
    # Decimal-degree coordinate pairs with >= 4 decimals (GPS points).
    re.compile(r"(?<![\w.])-?[0-9]{1,2}\.[0-9]{4,}\s*[,; ]\s*-?[0-9]{1,3}\.[0-9]{4,}(?![\w.])"),
    re.compile(r"\b(?:lat|latitude|lon|lng|longitude)\s*[=:]\s*-?[0-9]{1,3}\.[0-9]{3,}", re.I),
    # E-mail addresses.
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    # Phone numbers (RU format and generic international).
    re.compile(r"(?<![\w])(?:\+7|8)[\s(-]*[0-9]{3}[\s)-]*[0-9]{3}[\s-]*[0-9]{2}[\s-]*[0-9]{2}(?![\w])"),
    re.compile(r"(?<![\w])\+[0-9]{10,14}(?![\w])"),
    # Production runtime data files.
    re.compile(r"\b(?:driver_state|shift_history|yandex_day)\.json\b"),
)


def scan_untrusted_text(text: str) -> List[str]:
    """Classify free text. Never executes or follows it."""
    codes: List[str] = []
    if any(p.search(text) for p in _AUTHORITY_PATTERNS):
        codes.append("FORGED_AUTHORITY")
    if any(p.search(text) for p in _INJECTION_PATTERNS):
        codes.append("PROMPT_INJECTION")
    if any(p.search(text) for p in _SENSITIVE_PATTERNS):
        codes.append("SENSITIVE_DATA")
    return codes


def scan_secrets(text: str) -> List[str]:
    return ["SECRET_DETECTED"] if any(p.search(text) for p in _SECRET_PATTERNS) else []


# ---------------------------------------------------------------------------
# Bounded UTF-8 / NFC / LF serialization
# ---------------------------------------------------------------------------


def normalize_text(value: str) -> str:
    """Normalize NEW free text for drafting: NFC, single spaces, trimmed.

    The verifier never calls this on received records; historical records
    that are not already canonical are rejected, not rewritten.
    """
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


def serialize(record: Mapping[str, object]) -> bytes:
    """Serialize a record dict to canonical bytes (fixed order, LF, NFC)."""
    rtype = record.get("type")
    if rtype not in SCHEMAS:
        raise ValueError("unknown record type")
    lines = [HEADER]
    for name, kind in SCHEMAS[rtype]:
        value = record.get(name)
        if kind == L:
            items = list(value or [])
            for item in items:
                if not isinstance(item, str) or "\n" in item or item != item.strip() or not item:
                    raise ValueError("bad list item in %s" % name)
            items = sorted(set(items), key=lambda s: s.encode("utf-8")) or ["none"]
            lines.append("%s:" % name)
            lines.extend("- %s" % i for i in items)
        else:
            if not isinstance(value, str) or "\n" in value or value != value.strip() or not value:
                raise ValueError("bad scalar %s" % name)
            lines.append("%s: %s" % (name, value))
    text = unicodedata.normalize("NFC", "\n".join(lines) + "\n")
    return text.encode("utf-8")


def content_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def parse(raw: bytes) -> Tuple[Optional[Dict[str, object]], List[str]]:
    """Strictly parse canonical record bytes. Returns (record|None, codes).

    Any deviation from the canonical byte form is a FAIL; the input is never
    rewritten.
    """
    codes: List[str] = []
    if not isinstance(raw, (bytes, bytearray)):
        return None, ["ENCODING"]
    raw = bytes(raw)
    if len(raw) > MAX_RECORD_BYTES:
        return None, ["RECORD_TOO_LARGE"]
    if raw.startswith(b"\xef\xbb\xbf"):
        return None, ["BOM"]
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None, ["ENCODING"]
    if "\r" in text:
        return None, ["NOT_LF"]
    if any((ord(ch) < 32 and ch != "\n") or 0x7F <= ord(ch) < 0xA0 or ch in "  ﻿" for ch in text):
        return None, ["CONTROL_CHAR"]
    if unicodedata.normalize("NFC", text) != text:
        return None, ["NOT_NFC"]
    if not text.endswith("\n") or text.endswith("\n\n"):
        return None, ["NON_CANONICAL:trailing_newline"]
    lines = text[:-1].split("\n")
    if lines[0] != HEADER:
        return None, ["HEADER"]

    record: Dict[str, object] = {}
    order: List[str] = []
    current_list: Optional[str] = None
    for line in lines[1:]:
        if line.startswith("- "):
            item = line[2:]
            if current_list is None or not item or item != item.strip():
                return None, ["MALFORMED_LINE"]
            lst = record[current_list]
            assert isinstance(lst, list)
            lst.append(item)
            continue
        m = re.match(r"^([^:\s]+):(?: (.*))?$", line)
        if not m or not KEY_RE.match(m.group(1)):
            return None, ["MALFORMED_LINE"]
        key, value = m.group(1), m.group(2)
        if key in record:
            return None, ["DUPLICATE_FIELD:%s" % key]
        order.append(key)
        if value is None:
            record[key] = []
            current_list = key
        else:
            if not value or value != value.strip():
                return None, ["MALFORMED_LINE"]
            record[key] = value
            current_list = None

    rtype = record.get("type")
    if rtype not in SCHEMAS:
        return None, ["UNKNOWN_TYPE"]
    if record.get("v") != "1":
        codes.append("BAD_VERSION")
    schema = SCHEMAS[rtype]
    names = [n for n, _ in schema]
    kinds = dict(schema)
    for key in order:
        if key not in kinds:
            codes.append("UNKNOWN_FIELD:%s" % key)
    for name in names:
        if name not in record:
            codes.append("MISSING_FIELD:%s" % name)
    if codes:
        return None, codes
    if order != names:
        return None, ["FIELD_ORDER"]
    for name, kind in schema:
        value = record[name]
        if kind == L:
            if not isinstance(value, list) or not value:
                return None, ["MALFORMED_LINE"]
            if value == ["none"]:
                record[name] = []
                value = []
            if len(value) > MAX_LIST_ITEMS:
                codes.append("LIST_TOO_LONG:%s" % name)
            for item in value:
                if len(item.encode("utf-8")) > MAX_SCALAR_BYTES:
                    codes.append("FIELD_TOO_LONG:%s" % name)
        else:
            if not isinstance(value, str):
                return None, ["MALFORMED_LINE"]
            limit = MAX_TEXT_BYTES if kind == T else MAX_SCALAR_BYTES
            if len(value.encode("utf-8")) > limit:
                codes.append(("TEXT_TOO_LONG:%s" if kind == T else "FIELD_TOO_LONG:%s") % name)
    if codes:
        return None, codes
    try:
        again = serialize(record)
    except ValueError:
        return None, ["NON_CANONICAL"]
    if again != raw:
        return None, ["NON_CANONICAL"]
    return record, []


# ---------------------------------------------------------------------------
# Field validation (schema level, context free)
# ---------------------------------------------------------------------------


def _check_session(value: str, allow_unassigned: bool = False) -> bool:
    return (allow_unassigned and value == "unassigned") or bool(SESSION_RE.match(value))


def validate_fields(record: Mapping[str, object], repo: str = DEFAULT_REPO) -> List[str]:
    codes: List[str] = []
    rtype = record["type"]

    def need(cond: bool, code: str) -> None:
        if not cond:
            codes.append(code)

    need(bool(TASK_ID_RE.match(str(record["task_id"]))), "BAD_TASK_ID")
    need(bool(CONSULT_ID_RE.match(str(record["consult_id"]))), "BAD_CONSULT_ID")
    need(record["scope"] == SCOPE_ADVISORY, "SCOPE_NOT_ADVISORY")
    need(parse_ts(str(record["ts_utc"])) is not None, "BAD_TIMESTAMP:ts_utc")
    need(record["source_agent"] in KNOWN_AGENTS, "ROLE_UNKNOWN:source_agent")
    need(_check_session(str(record["source_session"])), "BAD_SESSION:source_session")

    if rtype in (TYPE_REQUEST, TYPE_REPLY):
        mode = record["mode"]
        if mode != MODE_COLLAB:
            codes.append("MODE_FORBIDDEN:%s" % ("INDEPENDENT_QA" if mode == MODE_INDEPENDENT_QA else "unknown"))
        need(record["target_agent"] in KNOWN_AGENTS, "ROLE_UNKNOWN:target_agent")
        need(
            _check_session(str(record["target_session"]), allow_unassigned=(rtype == TYPE_REQUEST)),
            "BAD_SESSION:target_session",
        )
        need(bool(SHA40_RE.match(str(record["source_head_sha"]))), "BAD_SHA40:source_head_sha")
        need(bool(SHA64_RE.match(str(record["spec_sha256"]))), "BAD_SHA64:spec_sha256")
        need(record["risk"] in RISKS, "BAD_ENUM:risk")

    if rtype == TYPE_REQUEST:
        need(blob_link(str(record["source_ref"]), repo) is not None, "INVALID_LINK:source_ref")
        need(parse_ts(str(record["expires_at_utc"])) is not None, "BAD_TIMESTAMP:expires_at_utc")
        for p in record["source_paths"]:  # type: ignore[union-attr]
            need(valid_path(p), "BAD_PATH:%s" % p)
        need(bool(record["source_paths"]), "MISSING_FIELD:source_paths")
        for link in record["allowed_evidence"]:  # type: ignore[union-attr]
            need(blob_link(link, repo) is not None or comment_link(link, repo) is not None, "INVALID_LINK:allowed_evidence")
    elif rtype == TYPE_REPLY:
        need(comment_link(str(record["in_reply_to"]), repo) is not None, "INVALID_LINK:in_reply_to")
        need(bool(SHA64_RE.match(str(record["request_sha256"]))), "BAD_SHA64:request_sha256")
        need(record["status"] in REPLY_STATUSES, "BAD_ENUM:status")
        for link in record["evidence"]:  # type: ignore[union-attr]
            need(blob_link(link, repo) is not None or comment_link(link, repo) is not None, "INVALID_LINK:evidence")
    elif rtype == TYPE_CLOSE:
        need(comment_link(str(record["request_ref"]), repo) is not None, "INVALID_LINK:request_ref")
        need(bool(SHA64_RE.match(str(record["request_sha256"]))), "BAD_SHA64:request_sha256")
        reply_ref, reply_sha = record["reply_ref"], record["reply_sha256"]
        if reply_ref == "none" or reply_sha == "none":
            need(reply_ref == "none" and reply_sha == "none", "INVALID_LINK:reply_ref")
        else:
            need(comment_link(str(reply_ref), repo) is not None, "INVALID_LINK:reply_ref")
            need(bool(SHA64_RE.match(str(reply_sha))), "BAD_SHA64:reply_sha256")
        need(record["final_state"] in CLOSE_STATES, "BAD_ENUM:final_state")
    return codes


# ---------------------------------------------------------------------------
# Synthetic context and comment snapshots
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TaskContext:
    """Live facts about the parent task, supplied by the caller (synthetic).

    Evidence flags default to NOT_VERIFIED so that an incomplete context
    can never produce PASS.
    """

    task_id: str
    spec_sha256: str
    head_sha: str
    assignee_agent: str
    assignee_session: str
    lease_until: str
    now: str
    lease_state: str = LEASE_ACTIVE
    allowed_paths: Tuple[str, ...] = ()
    forbidden_paths: Tuple[str, ...] = ()
    advisers: FrozenSet[Tuple[str, str]] = frozenset()
    coordinator_sessions: FrozenSet[str] = frozenset()
    qa_assignments: FrozenSet[Tuple[str, str, str]] = frozenset()
    principals: Mapping[str, str] = field(default_factory=dict)
    authority_evidence: str = NOT_VERIFIED
    provenance_evidence: str = NOT_VERIFIED
    transport_evidence: str = NOT_VERIFIED
    repo: str = DEFAULT_REPO


@dataclass(frozen=True)
class CommentSnapshot:
    """A captured GitHub comment (synthetic in this prototype)."""

    url: str
    created_at: str
    updated_at: str
    body: bytes
    captured_sha256: str
    author_login: str


def snapshot(url: str, body: bytes, ts: str, author_login: str = "synthetic-principal") -> CommentSnapshot:
    """Build an unedited synthetic snapshot whose hash matches its body."""
    return CommentSnapshot(url, ts, ts, body, content_sha256(body), author_login)


def _context_codes(ctx: TaskContext, now: Optional[datetime]) -> List[str]:
    codes: List[str] = []
    if ctx.authority_evidence != VERIFIED:
        codes.append("AUTHORITY_NOT_VERIFIED")
    if ctx.provenance_evidence != VERIFIED:
        codes.append("PROVENANCE_NOT_VERIFIED")
    if ctx.transport_evidence != VERIFIED:
        codes.append("TRANSPORT_NOT_VERIFIED")
    if (
        now is None
        or parse_ts(ctx.lease_until) is None
        or not TASK_ID_RE.match(ctx.task_id)
        or not SHA64_RE.match(ctx.spec_sha256)
        or not SHA40_RE.match(ctx.head_sha)
        or not ctx.allowed_paths
        or not ctx.forbidden_paths
    ):
        codes.append("CONTEXT_INVALID")
    return codes


def _lease_codes(ctx: TaskContext, now: Optional[datetime]) -> List[str]:
    codes: List[str] = []
    lease = parse_ts(ctx.lease_until)
    if ctx.lease_state != LEASE_ACTIVE:
        codes.append("PARENT_LEASE_REVOKED:%s" % ctx.lease_state)
    if lease is None or now is None or now >= lease:
        codes.append("PARENT_LEASE_EXPIRED")
    return codes


def _snapshot_codes(snap: CommentSnapshot, ctx: TaskContext, record: Optional[Mapping[str, object]]) -> List[str]:
    codes: List[str] = []
    if comment_link(snap.url, ctx.repo) is None:
        codes.append("INVALID_LINK:comment")
    if snap.created_at != snap.updated_at or parse_ts(snap.created_at) is None:
        codes.append("COMMENT_EDITED")
    if content_sha256(snap.body) != snap.captured_sha256:
        codes.append("SNAPSHOT_MISMATCH")
    # Identity: a shared GitHub login cannot attribute a record (§0.1).
    if snap.author_login in SHARED_LOGINS:
        codes.append("IDENTITY_SHARED_ACCOUNT")
    elif record is not None:
        expected = ctx.principals.get(str(record.get("source_agent")))
        if expected is None:
            codes.append("IDENTITY_NOT_VERIFIED")
        elif expected != snap.author_login:
            codes.append("IDENTITY_MISMATCH")
    return codes


def _paths_codes(paths: Sequence[str], ctx: TaskContext) -> List[str]:
    codes: List[str] = []
    for p in paths:
        allowed = any(glob_match(p, pat) for pat in ctx.allowed_paths)
        forbidden = any(glob_match(p, pat) for pat in ctx.forbidden_paths)
        if not allowed or forbidden:
            codes.append("PATH_ESCALATION:%s" % p)
    return codes


def _qa_parties(ctx: TaskContext) -> Tuple[set, set]:
    agents = {a for (a, _s, _h) in ctx.qa_assignments}
    sessions = {s for (_a, s, _h) in ctx.qa_assignments}
    return agents, sessions


def _text_codes(record: Mapping[str, object], raw: bytes) -> List[str]:
    codes = scan_secrets(raw.decode("utf-8", errors="replace"))
    for name, kind in SCHEMAS[str(record["type"])]:
        if kind == T and record[name] != "none":
            codes.extend(scan_untrusted_text(str(record[name])))
    return codes


# ---------------------------------------------------------------------------
# Ledger (in-memory, caller-owned)
# ---------------------------------------------------------------------------


class Ledger:
    """Append-only, in-memory record of ACCEPTED (PASS) records.

    De-duplication key: (type, task_id, source_session, consult_id,
    source_head_sha). Nothing is persisted by this module; callers may
    export/import plain dicts.
    """

    def __init__(self) -> None:
        self._by_key: Dict[Tuple[str, ...], Tuple[str, str]] = {}
        self._by_id: Dict[Tuple[str, str, str], Tuple[str, ...]] = {}
        self._by_url: Dict[str, str] = {}
        self.participation: List[Tuple[str, str, str, str, str]] = []

    @staticmethod
    def key(record: Mapping[str, object], head: str) -> Tuple[str, ...]:
        return (
            str(record["type"]), str(record["task_id"]), str(record["source_session"]),
            str(record["consult_id"]), head,
        )

    def accepted_sha(self, url: str) -> Optional[str]:
        return self._by_url.get(url)

    def precheck(self, record: Mapping[str, object], head: str, url: str, sha: str) -> List[str]:
        key = self.key(record, head)
        if url in self._by_url:
            if self._by_url[url] == sha:
                return ["DUPLICATE_NOOP"]
            return ["CONFLICT:url"]
        if key in self._by_key:
            prev_sha, _prev_url = self._by_key[key]
            return ["REPLAYED_COMMENT"] if prev_sha == sha else ["CONFLICT:payload"]
        id_key = (str(record["type"]), str(record["task_id"]), str(record["consult_id"]))
        if id_key in self._by_id and self._by_id[id_key] != key:
            return ["CONSULT_ID_REUSED"]
        return []

    def accept(self, record: Mapping[str, object], head: str, url: str, sha: str) -> None:
        key = self.key(record, head)
        self._by_key[key] = (sha, url)
        self._by_id[(str(record["type"]), str(record["task_id"]), str(record["consult_id"]))] = key
        self._by_url[url] = sha
        task = str(record["task_id"])
        if record["type"] == TYPE_REQUEST:
            self.participation.append((task, head, str(record["source_agent"]), str(record["source_session"]), "requester"))
            self.participation.append((task, head, str(record["target_agent"]), str(record["target_session"]), "consultant"))
        elif record["type"] == TYPE_REPLY:
            self.participation.append((task, head, str(record["source_agent"]), str(record["source_session"]), "consultant"))

    def export(self) -> Dict[str, object]:
        return {
            "by_key": [[list(k), list(v)] for k, v in sorted(self._by_key.items())],
            "participation": [list(p) for p in self.participation],
        }

    @classmethod
    def from_export(cls, data: Mapping[str, object]) -> "Ledger":
        led = cls()
        for k, v in data.get("by_key", []):  # type: ignore[union-attr]
            key, (sha, url) = tuple(k), tuple(v)
            led._by_key[key] = (sha, url)
            led._by_id[(key[0], key[1], key[3])] = key
            led._by_url[url] = sha
        led.participation = [tuple(p) for p in data.get("participation", [])]  # type: ignore[misc]
        return led


# ---------------------------------------------------------------------------
# Verification entry points
# ---------------------------------------------------------------------------


def _load(snap: CommentSnapshot, expected_type: str, ctx: TaskContext) -> Tuple[Optional[Dict[str, object]], List[str]]:
    record, codes = parse(snap.body)
    if record is None:
        return None, codes + _snapshot_codes(snap, ctx, None)
    if record["type"] != expected_type:
        return None, ["UNKNOWN_TYPE"]
    codes = validate_fields(record, ctx.repo)
    codes += _snapshot_codes(snap, ctx, record)
    return record, codes


def _finish(codes: List[str], record: Optional[Mapping[str, object]], snap: CommentSnapshot,
            ledger: Optional[Ledger], head: str) -> Result:
    if record is not None and ledger is not None:
        sha = content_sha256(snap.body)
        dup = ledger.precheck(record, head, snap.url, sha)
        codes = codes + dup
        res = _result(codes)
        if res.verdict == PASS and "DUPLICATE_NOOP" not in res.codes:
            ledger.accept(record, head, snap.url, sha)
        return res
    return _result(codes)


def verify_request(snap: CommentSnapshot, ctx: TaskContext, ledger: Optional[Ledger] = None) -> Result:
    """Verify a CONSULT-REQUEST/1 snapshot against the live parent context."""
    now = parse_ts(ctx.now)
    record, codes = _load(snap, TYPE_REQUEST, ctx)
    codes = list(codes) + _context_codes(ctx, now)
    if record is None:
        return _result(codes)
    codes += _text_codes(record, snap.body)
    codes += _lease_codes(ctx, now)

    if record["task_id"] != ctx.task_id:
        codes.append("CROSS_TASK")
    if record["spec_sha256"] != ctx.spec_sha256:
        codes.append("SPEC_MISMATCH")
    if record["source_head_sha"] != ctx.head_sha:
        codes.append("HEAD_MISMATCH")
    blob = blob_link(str(record["source_ref"]), ctx.repo)
    if blob is not None:
        if blob[0] != record["source_head_sha"]:
            codes.append("SOURCE_REF_MISMATCH")
        codes += _paths_codes([blob[1]], ctx)
    codes += _paths_codes(list(record["source_paths"]), ctx)  # type: ignore[arg-type]

    src = (record["source_agent"], record["source_session"])
    tgt = (record["target_agent"], record["target_session"])
    if src != (ctx.assignee_agent, ctx.assignee_session):
        codes.append("SOURCE_NOT_ASSIGNEE")
    if record["target_agent"] == record["source_agent"] or record["target_session"] == record["source_session"]:
        codes.append("SELF_CONSULT")
    if record["target_session"] == "unassigned":
        codes.append("TARGET_UNASSIGNED")
        if not any(a == record["target_agent"] for (a, _s) in ctx.advisers):
            codes.append("TARGET_NOT_AUTHORIZED")
    elif tgt not in ctx.advisers:
        codes.append("TARGET_NOT_AUTHORIZED")
    qa_agents, qa_sessions = _qa_parties(ctx)
    if (
        record["target_agent"] in qa_agents or record["target_session"] in qa_sessions
        or record["source_agent"] in qa_agents or record["source_session"] in qa_sessions
    ):
        codes.append("QA_FIREWALL")
    if record["risk"] == "HIGH":
        codes.append("RISK_HIGH_ESCALATE")

    ts = parse_ts(str(record["ts_utc"]))
    exp = parse_ts(str(record["expires_at_utc"]))
    lease = parse_ts(ctx.lease_until)
    if ts and exp:
        if now and ts > now:
            codes.append("TS_IN_FUTURE")
        if exp <= ts:
            codes.append("EXPIRY_NOT_AFTER_TS")
        elif exp - ts > MAX_EXPIRY:
            codes.append("EXPIRY_OVER_CAP")
        if lease and exp > lease:
            codes.append("EXPIRY_BEYOND_LEASE")
        if now and now >= exp:
            codes.append("CONSULT_EXPIRED")
    return _finish(codes, record, snap, ledger, str(record["source_head_sha"]))


def verify_reply(snap: CommentSnapshot, request_snap: CommentSnapshot, ctx: TaskContext,
                 ledger: Optional[Ledger] = None) -> Result:
    """Verify a CONSULT-REPLY/1 against its (already accepted) request."""
    now = parse_ts(ctx.now)
    record, codes = _load(snap, TYPE_REPLY, ctx)
    codes = list(codes) + _context_codes(ctx, now)
    if record is None:
        return _result(codes)
    codes += _text_codes(record, snap.body)
    codes += _lease_codes(ctx, now)
    request, req_codes = parse(request_snap.body)
    if request is None or request.get("type") != TYPE_REQUEST:
        codes.append("REQUEST_NOT_ACCEPTED")
        return _result(codes)
    req_sha = content_sha256(request_snap.body)
    if ledger is None or ledger.accepted_sha(request_snap.url) != req_sha:
        codes.append("REQUEST_NOT_ACCEPTED")
    if record["in_reply_to"] != request_snap.url:
        codes.append("REPLY_LINK_MISMATCH")
    if record["request_sha256"] != req_sha or request_snap.captured_sha256 != req_sha:
        codes.append("REQUEST_HASH_MISMATCH")
    for name in ("task_id", "consult_id", "source_head_sha", "spec_sha256"):
        if record[name] != request[name]:
            codes.append("REPLY_MISMATCH:%s" % name)
    if record["task_id"] != ctx.task_id:
        codes.append("CROSS_TASK")
    if record["spec_sha256"] != ctx.spec_sha256:
        codes.append("SPEC_MISMATCH")
    if record["source_head_sha"] != ctx.head_sha:
        codes.append("HEAD_MISMATCH")
    if record["source_agent"] != request["target_agent"]:
        codes.append("REPLY_MISMATCH:source_agent")
    if request["target_session"] == "unassigned":
        if (record["source_agent"], record["source_session"]) not in ctx.advisers:
            codes.append("TARGET_NOT_AUTHORIZED")
    elif record["source_session"] != request["target_session"]:
        codes.append("REPLY_MISMATCH:source_session")
    if (record["target_agent"], record["target_session"]) != (request["source_agent"], request["source_session"]):
        codes.append("REPLY_MISMATCH:target")
    qa_agents, qa_sessions = _qa_parties(ctx)
    if record["source_agent"] in qa_agents or record["source_session"] in qa_sessions:
        codes.append("QA_FIREWALL")
    ts = parse_ts(str(record["ts_utc"]))
    rts = parse_ts(str(request["ts_utc"]))
    rexp = parse_ts(str(request["expires_at_utc"]))
    if ts and rts and rexp:
        if now and ts > now:
            codes.append("TS_IN_FUTURE")
        if not (rts <= ts < rexp):
            codes.append("REPLY_OUTSIDE_WINDOW")
        if now and now >= rexp:
            codes.append("CONSULT_EXPIRED")
    if record["status"] == "NEEDS_COORDINATOR" or record["risk"] == "HIGH":
        codes.append("RISK_HIGH_ESCALATE")
    return _finish(codes, record, snap, ledger, str(record["source_head_sha"]))


def verify_close(snap: CommentSnapshot, request_snap: CommentSnapshot, reply_snap: Optional[CommentSnapshot],
                 ctx: TaskContext, ledger: Optional[Ledger] = None) -> Result:
    """Verify a coordinator CONSULT-CLOSE/1. Closing never has any gate effect."""
    now = parse_ts(ctx.now)
    record, codes = _load(snap, TYPE_CLOSE, ctx)
    codes = list(codes) + _context_codes(ctx, now)
    if record is None:
        return _result(codes)
    codes += _text_codes(record, snap.body)
    if record["source_agent"] != COORDINATOR_AGENT or record["source_session"] not in ctx.coordinator_sessions:
        codes.append("CLOSE_NOT_COORDINATOR")
    if record["task_id"] != ctx.task_id:
        codes.append("CROSS_TASK")
    request, _ = parse(request_snap.body)
    if request is None or request.get("consult_id") != record["consult_id"]:
        codes.append("REPLY_MISMATCH:consult_id")
    req_sha = content_sha256(request_snap.body)
    if record["request_ref"] != request_snap.url:
        codes.append("REPLY_LINK_MISMATCH:request_ref")
    if record["request_sha256"] != req_sha:
        codes.append("REQUEST_HASH_MISMATCH")
    if ledger is None or ledger.accepted_sha(request_snap.url) != req_sha:
        codes.append("REQUEST_NOT_ACCEPTED")
    state = record["final_state"]
    if reply_snap is None:
        if record["reply_ref"] != "none":
            codes.append("REPLY_LINK_MISMATCH:reply_ref")
        if state == "ACCEPTED_AS_CONTEXT":
            codes.append("CLOSE_STATE_INVALID:no_reply")
    else:
        rep_sha = content_sha256(reply_snap.body)
        if record["reply_ref"] != reply_snap.url:
            codes.append("REPLY_LINK_MISMATCH:reply_ref")
        if record["reply_sha256"] != rep_sha:
            codes.append("REPLY_HASH_MISMATCH")
        if state == "ACCEPTED_AS_CONTEXT" and (ledger is None or ledger.accepted_sha(reply_snap.url) != rep_sha):
            codes.append("REPLY_NOT_ACCEPTED")
    if state == "ACCEPTED_AS_CONTEXT":
        codes += _lease_codes(ctx, now)
    if request is not None and state == "EXPIRED":
        rexp = parse_ts(str(request["expires_at_utc"]))
        if rexp is None or now is None or now < rexp:
            codes.append("CLOSE_STATE_INVALID:not_expired")
    ts = parse_ts(str(record["ts_utc"]))
    if ts and now and ts > now:
        codes.append("TS_IN_FUTURE")
    head = str(request["source_head_sha"]) if request is not None else ctx.head_sha
    return _finish(codes, record, snap, ledger, head)


def evaluate_timeout(request_snap: CommentSnapshot, reply_results: Sequence[Result], ctx: TaskContext) -> Result:
    """No accepted reply never means "yes": AWAITING_REPLY or CONSULT_TIMEOUT."""
    if any(r.verdict == PASS for r in reply_results):
        return _result([])
    request, codes = parse(request_snap.body)
    if request is None:
        return _result(codes)
    now = parse_ts(ctx.now)
    exp = parse_ts(str(request["expires_at_utc"]))
    if exp is None or now is None:
        return _result(["BAD_TIMESTAMP:expires_at_utc"])
    return _result(["CONSULT_TIMEOUT"] if now >= exp else ["AWAITING_REPLY"])


def check_qa_independence(qa_agent: str, qa_session: str, task_id: str, head_sha: str,
                          ledger: Ledger) -> Result:
    """FAIL if the would-be independent QA consulted (or was consulted) on
    the same task and HEAD. Matching is by agent role as well as session,
    because sessions can be renewed under a shared identity."""
    for (task, head, agent, session, _role) in ledger.participation:
        if task == task_id and head == head_sha and (agent == qa_agent or session == qa_session):
            return _result(["QA_INDEPENDENCE_CONFLICT"])
    return _result([])


# ---------------------------------------------------------------------------
# Offline drafting helpers (no sending)
# ---------------------------------------------------------------------------


def draft_request(*, task_id: str, consult_id: str, source_agent: str, source_session: str,
                  target_agent: str, target_session: str, source_ref: str, source_head_sha: str,
                  spec_sha256: str, ts_utc: str, question: str, source_paths: Sequence[str],
                  allowed_evidence: Sequence[str] = (), risk: str = "LOW",
                  expires_at_utc: Optional[str] = None) -> bytes:
    """Return canonical CONSULT-REQUEST/1 bytes for local review only."""
    if expires_at_utc is None:
        start = parse_ts(ts_utc)
        if start is None:
            raise ValueError("bad ts_utc")
        expires_at_utc = format_ts(start + DEFAULT_EXPIRY)
    return serialize(
        {
            "type": TYPE_REQUEST, "v": "1", "mode": MODE_COLLAB, "task_id": task_id,
            "consult_id": consult_id, "source_agent": source_agent, "source_session": source_session,
            "target_agent": target_agent, "target_session": target_session, "source_ref": source_ref,
            "source_head_sha": source_head_sha, "spec_sha256": spec_sha256, "ts_utc": ts_utc,
            "expires_at_utc": expires_at_utc, "risk": risk, "scope": SCOPE_ADVISORY,
            "question": normalize_text(question), "source_paths": list(source_paths),
            "allowed_evidence": list(allowed_evidence),
        }
    )
