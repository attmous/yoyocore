"""Helpers for listing ALSA capture/playback devices for UI selection.

These functions intentionally have safe fallbacks when running in environments
without ALSA utilities (for example the Windows simulator).
"""

from __future__ import annotations

import shutil
import subprocess

from loguru import logger


def _normalize_alsa_selector(value: str) -> str:
    raw = value.strip()
    if raw.upper().startswith("ALSA:"):
        raw = raw.split(":", 1)[1].strip()
    return raw


def _run_list(binary: str) -> list[str]:
    if not shutil.which(binary):
        return []
    try:
        result = subprocess.run(
            [binary, "-L"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception as exc:
        logger.debug("ALSA list via {} failed: {}", binary, exc)
        return []
    if result.returncode != 0:
        return []
    devices: list[str] = []
    for line in result.stdout.splitlines():
        # Device identifiers are on non-indented lines; descriptions are indented.
        if not line or line.startswith(" "):
            continue
        device = line.strip()
        if not device:
            continue
        if device in {"null"}:
            continue
        devices.append(device)
    return devices


def list_playback_devices(*, aplay_binary: str = "aplay") -> list[str]:
    """Return ALSA playback devices in a stable, UI-friendly order."""

    parsed = _run_list(aplay_binary)
    filtered: list[str] = []
    for device in parsed:
        # Skip common aliases that don't help selection.
        if device in {"default", "sysdefault"}:
            continue
        if "vc4hdmi" in device.lower():
            continue
        filtered.append(device)

    def sort_key(value: str) -> tuple[int, str]:
        lowered = value.lower()
        if "card=se" in lowered or "usb" in lowered:
            return (0, value)
        if value.startswith("plughw:"):
            return (1, value)
        if value.startswith("default:card="):
            return (2, value)
        if value.startswith("sysdefault:card="):
            return (3, value)
        return (4, value)

    return sorted(dict.fromkeys(filtered), key=sort_key)


def list_capture_devices(*, arecord_binary: str = "arecord") -> list[str]:
    """Return ALSA capture devices in a stable, UI-friendly order."""

    parsed = _run_list(arecord_binary)
    filtered: list[str] = []
    for device in parsed:
        if device in {"default", "sysdefault"}:
            continue
        filtered.append(device)

    def sort_key(value: str) -> tuple[int, str]:
        lowered = value.lower()
        if "card=se" in lowered or "usb" in lowered:
            return (0, value)
        if value.startswith("plughw:"):
            return (1, value)
        if value.startswith("front:card="):
            return (2, value)
        if value.startswith("dsnoop:card="):
            return (3, value)
        if value.startswith("hw:"):
            return (4, value)
        return (5, value)

    return sorted(dict.fromkeys(filtered), key=sort_key)


def format_device_label(device_id: str | None) -> str:
    """Turn an ALSA selector into a compact label suitable for the 240px UI."""

    if not device_id:
        return "Auto"

    normalized = _normalize_alsa_selector(device_id)

    # If the selector is of the form "<route>:CARD=XYZ,DEV=0", prefer showing the
    # card (and dev) with a route suffix. This reads much better than raw ALSA
    # strings like "iec958:CARD=SE,DEV=0".
    route = ""
    spec = normalized
    if ":" in normalized:
        route, spec = normalized.split(":", 1)
        route = route.strip()
        spec = spec.strip()

    card = ""
    dev = ""
    upper_spec = spec.upper()
    if "CARD=" in upper_spec:
        start = upper_spec.index("CARD=") + len("CARD=")
        end = spec.find(",", start)
        card = spec[start:] if end == -1 else spec[start:end]
        card = card.strip()
    if "DEV=" in upper_spec:
        start = upper_spec.index("DEV=") + len("DEV=")
        end = spec.find(",", start)
        dev = spec[start:] if end == -1 else spec[start:end]
        dev = dev.strip()

    if card:
        label = card
        if route:
            label = f"{label} {route}"
        if dev:
            label = f"{label} {dev}"
        label = label.strip()
        if len(label) > 18:
            return label[:17] + "..."
        return label

    # Keep the full selector for power users, but avoid noisy prefixes.
    for prefix in (
        "default:",
        "sysdefault:",
        "plughw:",
        "front:",
        "dsnoop:",
        "dmix:",
        "hw:",
        "iec958:",
        "hdmi:",
    ):
        if normalized.lower().startswith(prefix):
            normalized = normalized[len(prefix) :]
            break

    normalized = normalized.strip()
    if not normalized:
        return "Auto"

    if len(normalized) > 18:
        return normalized[:17] + "..."
    return normalized
