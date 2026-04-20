"""Runtime diagnostics helpers for signal handling and watchdog evidence."""

from __future__ import annotations

import faulthandler
import json
import signal
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, TextIO

from yoyopod.core import RUNTIME_REQUIRED_CONFIG_FILES
from yoyopod.runtime.responsiveness import ResponsivenessWatchdogDecision


def _signal_name(signum: int) -> str:
    """Return a stable signal name for diagnostics logs."""

    try:
        return signal.Signals(signum).name
    except ValueError:
        return str(signum)


def _json_safe(value: object) -> object:
    """Normalize runtime state into JSON-safe values for snapshots."""

    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except TypeError:
            pass
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


def _build_runtime_snapshot_payload(
    *,
    app: object,
    source: str,
    trigger: str,
    capture_mode: str | None = None,
    reason: str | None = None,
    suspected_scope: str | None = None,
    summary: str | None = None,
    status: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Build one JSON-safe runtime snapshot payload for logs or evidence files."""

    payload: dict[str, object] = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "trigger": trigger,
    }
    if capture_mode is not None:
        payload["capture_mode"] = capture_mode
    if reason is not None:
        payload["reason"] = reason
    if suspected_scope is not None:
        payload["suspected_scope"] = suspected_scope
    if summary is not None:
        payload["summary"] = summary

    snapshot_status = status
    if snapshot_status is None:
        get_status = getattr(app, "get_status", None)
        if callable(get_status):
            try:
                snapshot_status = get_status()
            except Exception as exc:
                payload["status_error"] = str(exc)
        else:
            payload["status_error"] = "app does not expose get_status()"

    if snapshot_status is not None:
        payload["status"] = _json_safe(snapshot_status)

    return payload


def _log_signal_snapshot(
    *,
    app: object,
    app_log: Any,
    signal_name: str,
    prefer_readback: bool,
) -> None:
    """Emit one structured runtime snapshot to the error log on demand."""

    payload = _build_runtime_snapshot_payload(
        app=app,
        source="signal_snapshot",
        trigger=signal_name,
        capture_mode="readback-first" if prefer_readback else "shadow-first",
        status=None,
    )
    payload["signal"] = signal_name
    app_log.error("Freeze diagnostics snapshot: {}", json.dumps(payload, sort_keys=True))


def _log_setup_failure_guidance(app_log: Any) -> None:
    """Log shared bootstrap guidance when app setup fails."""

    app_log.error("Check that:")
    for relative_path in RUNTIME_REQUIRED_CONFIG_FILES:
        app_log.error(f"  - {relative_path.as_posix()} exists")
    app_log.error(
        "  - data/people/contacts.yaml can be created from config/people/contacts.seed.yaml"
    )
    app_log.error("  - liblinphone is installed and the native shim is built")
    app_log.error("  - mpv is installed and the configured music backend can start")
    app_log.error(
        "  - Whisplay production runs have a working LVGL shim and do not rely on PIL or simulation fallback"
    )


def _resolve_responsiveness_capture_dir(app: object) -> Path:
    """Resolve the configured directory for automatic watchdog captures."""

    app_settings = getattr(app, "app_settings", None)
    diagnostics = getattr(app_settings, "diagnostics", None)
    raw_capture_dir = getattr(diagnostics, "responsiveness_capture_dir", "logs/responsiveness")
    capture_dir = Path(str(raw_capture_dir))
    if not capture_dir.is_absolute():
        capture_dir = Path.cwd() / capture_dir
    return capture_dir


def _append_traceback_dump(
    *,
    dump_path: Path,
    app_log: Any,
    header: str,
) -> bool:
    """Write one all-thread traceback dump to the provided file path."""

    dump_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with dump_path.open("a", encoding="utf-8", buffering=1) as dump_stream:
            dump_stream.write(f"{header}\n")
            faulthandler.dump_traceback(file=dump_stream, all_threads=True)
            dump_stream.write("\n")
    except OSError as exc:
        app_log.warning("Failed to write traceback dump {}: {}", dump_path, exc)
        return False
    return True


def _capture_responsiveness_watchdog_evidence(
    *,
    app: object,
    app_log: Any,
    error_log_path: Path,
    decision: ResponsivenessWatchdogDecision,
    status: Mapping[str, object],
) -> None:
    """Persist one automatic responsiveness capture and announce where it landed."""

    payload = _build_runtime_snapshot_payload(
        app=app,
        source="responsiveness_watchdog",
        trigger=decision.reason,
        reason=decision.reason,
        suspected_scope=decision.suspected_scope,
        summary=decision.summary,
        status=status,
    )
    capture_dir = _resolve_responsiveness_capture_dir(app)
    capture_dir.mkdir(parents=True, exist_ok=True)

    captured_at = payload["captured_at"]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = f"{timestamp}-{decision.reason}"
    snapshot_path = capture_dir / f"{stem}.json"
    snapshot_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    traceback_path = capture_dir / f"{stem}.traceback.txt"
    _append_traceback_dump(
        dump_path=traceback_path,
        app_log=app_log,
        header=(
            f"=== Responsiveness watchdog capture at {captured_at} "
            f"reason={decision.reason} scope={decision.suspected_scope} ==="
        ),
    )

    record_capture = getattr(app, "record_responsiveness_capture", None)
    artifacts = {
        "snapshot": str(snapshot_path),
        "traceback": str(traceback_path),
        "error_log": str(error_log_path),
    }
    if callable(record_capture):
        record_capture(
            captured_at=time.monotonic(),
            reason=decision.reason,
            suspected_scope=decision.suspected_scope,
            summary=decision.summary,
            artifacts=artifacts,
        )

    app_log.error(
        "Responsiveness watchdog captured evidence: {}",
        json.dumps(
            {
                "captured_at": captured_at,
                "reason": decision.reason,
                "suspected_scope": decision.suspected_scope,
                "summary": decision.summary,
                "snapshot_path": str(snapshot_path),
                "traceback_path": str(traceback_path),
                "loop_heartbeat_age_seconds": status.get("loop_heartbeat_age_seconds"),
                "input_activity_age_seconds": status.get("input_activity_age_seconds"),
                "handled_input_activity_age_seconds": status.get(
                    "handled_input_activity_age_seconds"
                ),
                "current_screen": status.get("current_screen"),
                "state": status.get("state"),
            },
            sort_keys=True,
        ),
    )


def _install_traceback_dump_handlers(
    *,
    signals: tuple[int, ...],
    dump_path: Path,
    app_log: Any,
) -> tuple[TextIO | None, tuple[int, ...]]:
    """Chain all-thread traceback dumps onto the screenshot signals."""

    if not signals:
        return None, ()

    dump_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        dump_stream = dump_path.open("a", encoding="utf-8", buffering=1)
    except OSError as exc:
        app_log.warning("Failed to open traceback dump log {}: {}", dump_path, exc)
        return None, ()

    installed: list[int] = []
    for signum in signals:
        try:
            faulthandler.register(signum, file=dump_stream, all_threads=True, chain=True)
        except (OSError, RuntimeError, ValueError) as exc:
            app_log.warning(
                "Failed to arm traceback dump for {}: {}",
                _signal_name(signum),
                exc,
            )
            continue
        installed.append(signum)

    if not installed:
        dump_stream.close()
        return None, ()

    app_log.info(
        "Freeze traceback dumps armed for {} -> {}",
        ", ".join(_signal_name(signum) for signum in installed),
        dump_path,
    )
    return dump_stream, tuple(installed)


def _uninstall_traceback_dump_handlers(
    *,
    signals: tuple[int, ...],
    dump_stream: TextIO | None,
) -> None:
    """Best-effort faulthandler cleanup on process exit."""

    for signum in signals:
        try:
            faulthandler.unregister(signum)
        except (OSError, RuntimeError, ValueError):
            continue

    if dump_stream is not None:
        dump_stream.close()
