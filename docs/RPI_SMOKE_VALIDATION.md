# Raspberry Pi Smoke Validation

This guide separates the validation work that is safe in CI from the checks that still require Raspberry Pi hardware, the mpv music backend, and a reachable SIP account.

## Validation Layers

### 1. CI-safe Python checks

Run these anywhere:

```bash
uv sync --extra dev
uv run pytest -q
```

This covers the pure-Python and simulation-mode regression suite.

### 2. Raspberry Pi core hardware smoke

Run this on the target Raspberry Pi after pulling the latest branch:

```bash
yoyoctl pi smoke
yoyoctl pi smoke --with-power --with-rtc
yoyoctl pi lvgl soak
```

What it checks:

- target environment information
- display initialization on real hardware
- matching input adapter construction and start/stop
- optional LVGL transition and sleep/wake soak when requested

Expected result:

- `display` should report a real hardware adapter, not simulation
- `input` should report the active interaction profile plus semantic capabilities for the attached hardware

### 3. Raspberry Pi service smoke

Add music-backend and SIP checks when the services are expected to be available:

```bash
yoyoctl pi smoke --with-music --with-voip
yoyoctl pi smoke --with-power --with-rtc --with-music --with-voip
```

What it checks:

- PiSugar battery telemetry and RTC state when requested
- mpv music-backend startup using `config/yoyopod_config.yaml`
- Liblinphone startup and SIP registration using `config/voip_config.yaml`
- Liblinphone media/codec defaults from `config/liblinphone_factory.conf`

Useful flags:

- `--music-timeout 10`
- `--voip-timeout 15`
- `--verbose`

## Manual Follow-up Checks

### Full application startup

```bash
uv run python yoyopod.py
```

Verify:

- the home/menu UI renders on the target display
- button input navigates screens correctly
- the app returns cleanly on `Ctrl+C`

### VoIP registration drill

```bash
yoyoctl pi voip check
```

Use this when you want a registration-only pass with detailed logs.

### Incoming call debug drill

```bash
yoyoctl pi voip debug
```

Use this when SIP registration works but incoming-call parsing or callback delivery looks wrong.

### Whisplay display-only debug

```bash
yoyoctl build lvgl
yoyoctl pi lvgl probe --scene carousel --duration-seconds 10
```

Use this only on a Pi with the Whisplay hardware attached. It validates the display/LVGL path without starting the full app and is not part of CI.

### Whisplay gesture tuning

```bash
yoyoctl pi tune
yoyoctl pi tune --double-tap-ms 240 --long-hold-ms 900
```

Use this when button feel needs tuning on the real device. It listens for the semantic Whisplay gestures, prints every detected `advance` / `select` / `back` event with timing detail, and can apply temporary timing overrides without editing `config/yoyopod_config.yaml`.

Useful flags:

- `--duration-seconds 45`
- `--debounce-ms 75`
- `--double-tap-ms 240`
- `--long-hold-ms 900`
- `--verbose`

### LVGL Whisplay soak

```bash
yoyoctl pi lvgl soak
yoyoctl pi lvgl soak --cycles 3 --hold-seconds 0.3
```

Use this when Whisplay rendering feels fast but you still want a hardware pass for:

- repeated routed screen transitions
- sleep/wake recovery
- LVGL-only corruption or stuck redraw issues

### PiSugar RTC drill

```bash
yoyoctl pi power rtc status
yoyoctl pi power rtc sync-to
```

Use this when you want a focused RTC read/sync pass without running the full app.

### PiSugar power drill

```bash
yoyoctl pi power battery
```

Use this when you want a focused battery, charging, RTC, shutdown-threshold, and watchdog readout without the full smoke flow.

## Suggested Order On Hardware

1. `uv sync --extra dev`
2. `uv run pytest -q`
3. `yoyoctl pi smoke`
4. `yoyoctl pi smoke --with-music --with-voip`
5. `yoyoctl pi lvgl soak`
6. `uv run python yoyopod.py`

## Failure Triage

- `display` fails: check attached HAT, driver/library install, and `display.hardware` config
- `input` fails: check the matching display adapter initialized correctly first
- `music` fails: verify `mpv` is installed, the configured socket path is writable, and the configured `audio.music_dir` exists
- `voip` fails: verify the Liblinphone shim build, `config/liblinphone_factory.conf`, SIP credentials, network reachability, and audio device configuration

## Notes

- The smoke script exits non-zero if any requested check fails.
- CI intentionally does not run hardware-in-the-loop checks.
- The hardware smoke script is meant to be quick. Use the manual drills above when you need deeper debugging.
