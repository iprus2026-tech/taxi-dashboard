"""Minimal fail-closed JSON storage for Taxi Dashboard (B2-R2).

Scope:
- strict reads, schema checks, missing/corrupt/unavailable states;
- initialization marker (`storage_meta.json`) with flags only;
- no per-write hash synchronization;
- no transaction/journal layer (B3).
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

STATE_NAME = "driver_state.json"
HISTORY_NAME = "shift_history.json"
META_NAME = "storage_meta.json"
LOCK_NAME = ".storage.lock"
BLOCK_NAME = ".storage_blocked.json"
SCHEMA_VERSION = 1


class StorageFailure(Exception):
    http_status = 503

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class StorageManager:
    def __init__(self, base_dir: str | os.PathLike[str]):
        self.base_dir = Path(base_dir)
        self.state_path = self.base_dir / STATE_NAME
        self.history_path = self.base_dir / HISTORY_NAME
        self.meta_path = self.base_dir / META_NAME
        self.lock_path = self.base_dir / LOCK_NAME
        self.block_path = self.base_dir / BLOCK_NAME
        self._local_block: str | None = None

    # ------------------------------------------------------------------
    # Locking
    # ------------------------------------------------------------------

    @contextlib.contextmanager
    def _locked(self) -> Iterator[None]:
        try:
            fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        except OSError as exc:
            self._local_block = "data_unavailable"
            raise StorageFailure(
                "data_unavailable",
                "Хранилище данных недоступно; изменения остановлены.",
            ) from exc
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX)
            except OSError as exc:
                self._local_block = "data_unavailable"
                raise StorageFailure(
                    "data_unavailable",
                    "Не удалось заблокировать хранилище; изменения остановлены.",
                ) from exc
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
            os.close(fd)

    # ------------------------------------------------------------------
    # Block marker
    # ------------------------------------------------------------------

    def _blocked_error(self) -> StorageFailure:
        return StorageFailure(
            self._local_block or "data_recovery_required",
            "Хранилище заблокировано после ошибки данных; запись остановлена.",
        )

    def _check_blocked_locked(self) -> None:
        if self._local_block is not None:
            raise self._blocked_error()
        if self.block_path.exists():
            try:
                payload = json.loads(self.block_path.read_text(encoding="utf-8"))
            except (OSError, ValueError, UnicodeError):
                self._local_block = "data_recovery_required"
                raise self._blocked_error()
            code = payload.get("code") if isinstance(payload, dict) else None
            self._local_block = str(code or "data_recovery_required")
            raise self._blocked_error()

    def _set_block_locked(self, code: str) -> None:
        self._local_block = code
        if self.block_path.exists():
            return
        payload = {
            "code": code,
            "created_at": _now_iso(),
            "message": "Storage blocked after a data-integrity failure.",
        }
        try:
            self._atomic_write(
                self.block_path,
                json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
            )
        except OSError:
            pass

    def _fail_locked(self, code: str, message: str, *, block: bool = True) -> None:
        if block:
            self._set_block_locked(code)
        raise StorageFailure(code, message)

    # ------------------------------------------------------------------
    # Atomic write (data and marker only; no meta hash coupling)
    # ------------------------------------------------------------------

    def _atomic_write(self, path: Path, data: bytes) -> None:
        tmp = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
            dir_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except BaseException:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    # ------------------------------------------------------------------
    # Read primitives
    # ------------------------------------------------------------------

    def _read_meta_locked(self) -> dict | None:
        try:
            raw = self.meta_path.read_bytes()
        except FileNotFoundError:
            return None
        except OSError:
            self._fail_locked(
                "data_unavailable",
                "Метаданные хранилища недоступны; изменения остановлены.",
            )
            raise AssertionError("unreachable")

        try:
            meta = json.loads(raw.decode("utf-8"))
        except (UnicodeError, ValueError):
            self._fail_locked("data_corrupt", "Метаданные хранилища повреждены.")
            raise AssertionError("unreachable")

        if not isinstance(meta, dict):
            self._fail_locked("data_corrupt", "Метаданные хранилища имеют неверный тип.")
            raise AssertionError("unreachable")
        if meta.get("schema_version") != SCHEMA_VERSION:
            self._fail_locked(
                "data_recovery_required",
                "Версия метаданных хранилища несовместима.",
            )
            raise AssertionError("unreachable")
        if not isinstance(meta.get("state_initialized"), bool) or not isinstance(
            meta.get("history_initialized"), bool
        ):
            self._fail_locked("data_recovery_required", "Метаданные хранилища неполны.")
            raise AssertionError("unreachable")
        return meta

    def _read_bytes_locked(self, path: Path) -> bytes:
        try:
            return path.read_bytes()
        except FileNotFoundError:
            self._fail_locked("data_missing_unexpectedly", "Файл данных исчез при чтении.")
            raise AssertionError("unreachable")
        except OSError:
            self._fail_locked("data_unavailable", "Не удалось прочитать файл данных.")
            raise AssertionError("unreachable")

    def _read_state_file_locked(self) -> tuple[dict, bytes]:
        data = self._read_bytes_locked(self.state_path)
        try:
            state = json.loads(data.decode("utf-8"))
        except (UnicodeError, ValueError):
            self._fail_locked(
                "data_corrupt",
                "Файл состояния повреждён; запись остановлена без изменения файла.",
            )
            raise AssertionError("unreachable")
        if not isinstance(state, dict):
            self._fail_locked("data_corrupt", "Файл состояния имеет неверный тип.")
            raise AssertionError("unreachable")
        self._assert_state_structure_locked(state)
        return state, data

    def _read_history_file_locked(self) -> tuple[list, bytes]:
        data = self._read_bytes_locked(self.history_path)
        try:
            history = json.loads(data.decode("utf-8"))
        except (UnicodeError, ValueError):
            self._fail_locked(
                "data_corrupt",
                "Файл истории повреждён; запись остановлена без изменения файла.",
            )
            raise AssertionError("unreachable")
        if not isinstance(history, list):
            self._fail_locked("data_corrupt", "Файл истории имеет неверный тип.")
            raise AssertionError("unreachable")
        for record in history:
            if not isinstance(record, dict):
                self._fail_locked("data_corrupt", "Запись истории имеет неверный тип.")
                raise AssertionError("unreachable")
        return history, data

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _assert_state_structure_locked(self, state: dict) -> None:
        shift = state.get("shift")
        if not isinstance(shift, dict):
            self._fail_locked(
                "data_corrupt",
                "В состоянии отсутствует корректная смена; запись остановлена.",
            )
        if not isinstance(shift.get("started_at"), str) or not shift["started_at"]:
            self._fail_locked(
                "data_corrupt",
                "В состоянии отсутствует время начала смены.",
            )
        for key in ("markers", "orders", "expenses"):
            if not isinstance(shift.get(key), list):
                self._fail_locked("data_corrupt", "Структура смены неполна.")
        for marker in shift["markers"]:
            if not isinstance(marker, dict):
                self._fail_locked("data_corrupt", "Метка GPS имеет неверный тип.")
            lat, lng = marker.get("lat"), marker.get("lng")
            if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
                self._fail_locked("data_corrupt", "Метка GPS не содержит координаты.")
        for operation in shift["orders"] + shift["expenses"]:
            if not isinstance(operation, dict) or not isinstance(
                operation.get("amount"), (int, float)
            ):
                self._fail_locked("data_corrupt", "Финансовая операция имеет неверный тип.")

    def _assert_state_for_write_locked(self, state: dict) -> None:
        if not isinstance(state, dict):
            raise StorageFailure("data_invalid_candidate", "Состояние не записано: неверный тип.")
        shift = state.get("shift")
        if not isinstance(shift, dict):
            raise StorageFailure("data_invalid_candidate", "Состояние не записано: нет смены.")
        if not isinstance(shift.get("started_at"), str) or not shift["started_at"]:
            raise StorageFailure("data_invalid_candidate", "Состояние не записано: нет времени смены.")
        for key in ("markers", "orders", "expenses"):
            if not isinstance(shift.get(key), list):
                raise StorageFailure("data_invalid_candidate", "Состояние не записано: неполная смена.")

    # ------------------------------------------------------------------
    # Validation / normal reads
    # ------------------------------------------------------------------

    def _validate_locked(self, *, check_block: bool = True) -> tuple[dict, list, dict]:
        if check_block:
            self._check_blocked_locked()
        meta = self._read_meta_locked()

        state_exists = self.state_path.exists()
        history_exists = self.history_path.exists()

        if meta is None:
            if state_exists or history_exists:
                self._fail_locked(
                    "data_missing_unexpectedly",
                    "Данные существуют, но метаданные инициализации отсутствуют; "
                    "запись остановлена без создания пустой смены.",
                )
            self._fail_locked(
                "data_missing_first_boot",
                "Хранилище не инициализировано; требуется контролируемый bootstrap.",
                block=False,
            )

        if meta.get("state_initialized") is not True:
            self._fail_locked("data_recovery_required", "Флаг state не подтверждён.")
        if not state_exists:
            self._fail_locked(
                "data_missing_unexpectedly",
                "Ранее инициализированный state отсутствует; пустая смена не создаётся.",
            )

        state, _state_bytes = self._read_state_file_locked()

        history: list = []
        if meta.get("history_initialized") is True and not history_exists:
            self._fail_locked(
                "data_missing_unexpectedly",
                "Ранее инициализированная history отсутствует.",
            )
        if history_exists:
            # A history created after bootstrap is valid even while the
            # bootstrap-time history_initialized flag is false.
            history, _history_bytes = self._read_history_file_locked()

        return state, history, meta

    # ------------------------------------------------------------------
    # Bootstrap
    # ------------------------------------------------------------------

    def _write_meta_locked(self, meta: dict) -> None:
        try:
            self._atomic_write(
                self.meta_path,
                json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8"),
            )
        except OSError:
            self._fail_locked(
                "data_recovery_required",
                "Не удалось зафиксировать метаданные; запись остановлена.",
            )

    def _archive_block_locked(self) -> None:
        if not self.block_path.exists():
            return
        target = self.block_path.with_name(
            f".storage_blocked.{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        )
        try:
            os.replace(self.block_path, target)
        except OSError:
            self._fail_locked(
                "data_recovery_required",
                "Не удалось снять block-marker; запись остановлена.",
            )
        self._local_block = None

    def _peek_json(self, path: Path):
        try:
            return json.loads(path.read_bytes().decode("utf-8")), None
        except FileNotFoundError:
            return None, "missing"
        except (OSError, UnicodeError, ValueError):
            return None, "invalid"

    @staticmethod
    def _state_structure_ok(state) -> bool:
        if not isinstance(state, dict):
            return False
        shift = state.get("shift")
        if not isinstance(shift, dict):
            return False
        if not isinstance(shift.get("started_at"), str) or not shift["started_at"]:
            return False
        if any(not isinstance(shift.get(key), list) for key in ("markers", "orders", "expenses")):
            return False
        return True

    @staticmethod
    def _history_structure_ok(history) -> bool:
        return isinstance(history, list) and all(isinstance(item, dict) for item in history)

    def bootstrap_plan(self) -> dict:
        """Read-only description; never writes and never creates a block marker."""
        with self._locked():
            block_present = self.block_path.exists()
            meta_present = self.meta_path.exists()
            state_present = self.state_path.exists()
            history_present = self.history_path.exists()
            valid = False

            meta = None
            if meta_present:
                meta, meta_error = self._peek_json(self.meta_path)
                if meta_error is not None or not isinstance(meta, dict):
                    valid = False
                elif meta.get("schema_version") != SCHEMA_VERSION:
                    valid = False
                elif not isinstance(meta.get("state_initialized"), bool) or not isinstance(
                    meta.get("history_initialized"), bool
                ):
                    valid = False
                else:
                    valid = True

            if valid or not meta_present:
                state = None
                if state_present:
                    state, state_error = self._peek_json(self.state_path)
                    state_ok = state_error is None and self._state_structure_ok(state)
                else:
                    state_ok = False

                history_ok = True
                if history_present:
                    history, history_error = self._peek_json(self.history_path)
                    history_ok = history_error is None and self._history_structure_ok(history)
                if meta_present:
                    if meta.get("state_initialized") is not True:
                        state_ok = False
                    if meta.get("history_initialized") is True:
                        history_ok = history_ok and history_present
                    # false + history_present is valid: first history created
                    # after bootstrap while the meta flag remains false.
                valid = state_ok and history_ok

            return {
                "block_present": block_present,
                "meta_present": meta_present,
                "state_present": state_present,
                "history_present": history_present,
                "valid": bool(valid),
                "recoverable": bool(valid and block_present),
            }

    def bootstrap_existing(self, *, recover_block: bool = False) -> dict:
        """Create meta for existing valid files; never creates state/history."""
        with self._locked():
            block_present = self.block_path.exists()
            if block_present and not recover_block:
                raise StorageFailure(
                    "data_recovery_required",
                    "Block-marker присутствует; требуется контролируемое восстановление.",
                )

            if self.meta_path.exists():
                self._validate_locked(check_block=not recover_block)
                if block_present:
                    self._archive_block_locked()
                return self._read_meta_locked() or {}

            if not self.state_path.exists():
                self._fail_locked(
                    "data_missing_unexpectedly",
                    "Нет state для bootstrap; пустая смена не создаётся.",
                )

            state, state_bytes = self._read_state_file_locked()
            history_present = self.history_path.exists()
            history_bytes = None
            if history_present:
                _history, history_bytes = self._read_history_file_locked()

            meta = {
                "schema_version": SCHEMA_VERSION,
                "instance_id": uuid.uuid4().hex,
                "initialized_at": _now_iso(),
                "state_initialized": True,
                "history_initialized": bool(history_present),
                "bootstrap_state_sha256": _sha256(state_bytes),
                "bootstrap_history_sha256": _sha256(history_bytes) if history_bytes is not None else None,
                "updated_at": _now_iso(),
            }
            self._write_meta_locked(meta)
            if block_present:
                self._archive_block_locked()
            return meta

    def initialize_first_boot(self, state: dict) -> dict:
        with self._locked():
            self._check_blocked_locked()
            if self.meta_path.exists() or self.state_path.exists() or self.history_path.exists():
                self._fail_locked("data_missing_unexpectedly", "Инициализация запрещена: данные уже есть.")
            self._assert_state_for_write_locked(state)
            state_bytes = json.dumps(state, ensure_ascii=False, indent=2).encode("utf-8")
            self._atomic_write(self.state_path, state_bytes)
            meta = {
                "schema_version": SCHEMA_VERSION,
                "instance_id": uuid.uuid4().hex,
                "initialized_at": _now_iso(),
                "state_initialized": True,
                "history_initialized": False,
                "bootstrap_state_sha256": _sha256(state_bytes),
                "bootstrap_history_sha256": None,
                "updated_at": _now_iso(),
            }
            self._write_meta_locked(meta)
            return meta

    # ------------------------------------------------------------------
    # Public reads/writes
    # ------------------------------------------------------------------

    def read_state(self) -> dict:
        with self._locked():
            state, _history, _meta = self._validate_locked()
            return state

    def read_history(self) -> list:
        with self._locked():
            _state, history, _meta = self._validate_locked()
            return history

    def write_state(self, state: dict) -> None:
        with self._locked():
            self._validate_locked()
            self._assert_state_for_write_locked(state)
            data = json.dumps(state, ensure_ascii=False, indent=2).encode("utf-8")
            try:
                self._atomic_write(self.state_path, data)
            except OSError:
                self._fail_locked("data_unavailable", "Не удалось записать состояние.")

    def append_history(self, record: dict) -> None:
        with self._locked():
            _state, history, meta = self._validate_locked()
            if not isinstance(record, dict):
                raise StorageFailure("data_invalid_candidate", "Запись истории не добавлена.")
            # storage_meta is immutable after bootstrap: no meta write here.
            history = list(history)
            history.append(record)
            data = json.dumps(history, ensure_ascii=False, indent=2).encode("utf-8")
            try:
                self._atomic_write(self.history_path, data)
            except OSError:
                self._fail_locked("data_unavailable", "Не удалось записать историю.")

    def storage_status(self) -> dict:
        with self._locked():
            try:
                self._validate_locked()
            except StorageFailure as exc:
                return {"ok": False, "code": exc.code}
            return {"ok": True, "code": "confirmed"}
