# Project Overview

YoyoPod is an iPod-inspired Raspberry Pi application combining SIP calling and mpv-based local music playback behind a small-screen, button-driven UI. Target hardware is Raspberry Pi Zero 2W (416 MB RAM).

Three display/input modes are supported today: Pimoroni Display HAT Mini, PiSugar Whisplay, and browser-based simulation.

## Common Commands

```bash
# Install dev dependencies
uv run yoyoctl setup host
uv run yoyoctl setup verify-host

# Run the app
python yoyopod.py
python yoyopod.py --simulate

# Tests
uv run pytest -q
uv run pytest -q tests/test_fsm_runtime.py

# Code quality
uv run black .
uv run ruff check .

# Pi setup and verification
uv run yoyoctl setup pi
uv run yoyoctl setup verify-pi
```

## Configuration

All tracked config lives under `config/`:
- `yoyopod_config.yaml` -- display hardware, local music directory, mpv settings, default volume, auto-resume
- `voip_config.yaml` -- SIP account, transport, STUN, Liblinphone messaging, audio devices
- `contacts.yaml` -- contact list and speed dial

## Current Gaps

- Settings UI is still not implemented
- Hardware-required validation still needs real Pi coverage beyond CI and simulation
