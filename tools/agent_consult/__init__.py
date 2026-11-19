"""Offline, disabled-by-default AGENT-CONSULT Stage A prototype.

TAXI-AGENT-CONSULT-STAGE-A-01. NON-NORMATIVE.

This package only parses, serializes and verifies *synthetic* proposal
records CONSULT-REQUEST/1, CONSULT-REPLY/1 and CONSULT-CLOSE/1 described in
``docs/agents/consult/STAGE-A-PROPOSAL.md``. These records are not messages
of the active PROTOCOL v1 (``docs/agents/PROTOCOL.md``) and must not be
published in live tasks.

The package has no transport: it never sends, posts or reads anything over
the network, never writes to GitHub, never touches the filesystem, reads no
environment variables or tokens, and never executes record content. Every
verification result carries ``effect == "NONE"``: a record grants no
permission, lease, gate decision, assignment or QA verdict.

The flags below are informational constants. Nothing in this package reads
them to switch on any live behaviour; enabling CONSULT in live tasks requires
a separate owner-approved task.
"""

from __future__ import annotations

ENABLED = False
"""CONSULT is disabled by default. There is no code path that enables it."""

LIVE_TRANSPORT = False
"""No relay, MCP tool, GitHub write or agent-to-agent channel exists here."""

NORMATIVE = False
"""Records are proposals only; active PROTOCOL v1 is unchanged."""

from . import verify  # noqa: E402

__all__ = ["ENABLED", "LIVE_TRANSPORT", "NORMATIVE", "verify"]
