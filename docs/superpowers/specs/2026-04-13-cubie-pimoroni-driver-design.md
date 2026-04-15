# Cubie-Native Pimoroni Display + Input Driver

**Date:** 2026-04-13
**Status:** Approved
**Board:** Radxa Cubie A7Z at 192.168.178.110
**Goal:** Get the Pimoroni Display HAT Mini (320x240 landscape, 4-button) working on the Cubie A7Z board using spidev + gpiod, without the Pi-specific `displayhatmini` library.

## Context

The Pimoroni Display HAT Mini works on Raspberry Pi through the `displayhatmini` Python library, which depends on `RPi.GPIO`. On the Radxa Cubie A7Z:

- `RPi.GPIO` cannot be installed (Allwinner SoC, not Broadcom)
- GPIO chip/line numbering differs from Pi BCM numbering
- SPI bus is `spidev1.0` (Pi uses `spidev0.1`)
- The Whisplay driver on this same board already proves that `spidev` + `gpiod` works

The Cubie was previously brought up with the Whisplay HAT, but the Whisplay physical button is unsafe on this board (causes immediate shutdown). Switching to the Pimoroni HAT gives 4 safe buttons and a wider 320x240 landscape display.

## Approach

Write a Cubie-native ST7789 display driver and gpiod-based button adapter (Approach A). The existing Pi Pimoroni path (`pimoroni.py` + `four_button.py` using `displayhatmini`) remains untouched.

## GPIO Pin Mapping

Pimoroni Display HAT Mini pins cross-referenced with the Cubie A7Z 40-pin header:

### Display SPI + Control

| Signal | Physical Pin | Cubie GPIO | Notes |
|---|---|---|---|
| SPI MOSI | 19 | gpiochip0:108 | SPI1 MOSI (kernel) |
| SPI SCLK | 23 | gpiochip0:107 | SPI1 SCLK (kernel) |
| SPI CS (CE1) | 26 | gpiochip0:110 | Software CS (unused, available) |
| DC (data/cmd) | 21 | gpiochip0:109 | SPI1 MISO repurposed as DC |
| Backlight | 33 | gpiochip1:35 | Unused, available |

### Buttons (active-low with pull-up)

| Button | Physical Pin | Cubie GPIO | Status |
|---|---|---|---|
| A (SELECT) | 29 | gpiochip0:34 | Unused, available |
| B (BACK) | 31 | gpiochip0:35 | Unused, available |
| X (UP) | 36 | gpiochip0:36 | Kernel-associated, no active consumer |
| Y (DOWN) | 18 | gpiochip0:313 | Freed when Whisplay stopped |

### RGB LED

| Channel | Physical Pin | Cubie GPIO | Status |
|---|---|---|---|
| Red | 11 | gpiochip0:33 | Freed when Whisplay stopped |
| Green | 13 | gpiochip1:6 | Freed when Whisplay stopped |
| Blue | 15 | gpiochip1:7 | Freed when Whisplay stopped |

### Prerequisites

- YoyoPod service must be stopped before switching display mode (frees Whisplay GPIO claims)
- Set `YOYOPOD_DISPLAY=pimoroni` or configure in board config

## Components

### 1. ST7789 SPI Driver

**File:** `src/yoyopod/ui/display/adapters/st7789_spi.py`

Low-level driver that communicates with the ST7789 display controller over SPI, using gpiod for control signals.

**Responsibilities:**
- Open `spidev1.0` (mode 0, 8-bit, 60 MHz max, `no_cs=True`)
- Control DC pin via gpiod (low=command, high=data)
- Control CS pin via gpiod (software chip select)
- Control backlight via gpiod (on/off toggle, no PWM initially)
- Send ST7789 initialization commands (SWRESET, SLPOUT, COLMOD RGB565, MADCTL for landscape rotation, INVON, NORON, DISPON)
- Provide `draw_image(x, y, w, h, rgb565_data)` for pixel output via CASET + RASET + RAMWR

**Interface:**

```python
class ST7789SpiDriver:
    def __init__(self, spi_bus: int, spi_device: int, spi_speed_hz: int,
                 dc_chip: str, dc_line: int,
                 cs_chip: str, cs_line: int,
                 backlight_chip: str, backlight_line: int) -> None: ...

    def init(self) -> None: ...
    def command(self, cmd: int, data: bytes = b"") -> None: ...
    def draw_image(self, x: int, y: int, width: int, height: int, pixel_data: bytes) -> None: ...
    def set_backlight(self, on: bool) -> None: ...
    def cleanup(self) -> None: ...
```

**Pin configuration** is passed at construction time, sourced from the board config overlay.

### 2. Cubie Pimoroni Display Adapter

**File:** `src/yoyopod/ui/display/adapters/cubie_pimoroni.py`

Implements `DisplayHAL` for the Pimoroni Display HAT Mini on non-Pi boards.

**Responsibilities:**
- Maintain a PIL `Image` buffer (320x240, RGB)
- Delegate all drawing primitives (text, rectangle, circle, line, image) to PIL
- On `update()`: convert PIL buffer to RGB565 and call `driver.draw_image()`
- Drive the RGB LED via gpiod (on/off per channel, no PWM initially)
- Implement `status_bar()` (reuse logic from existing `pimoroni.py`)

**Class constants:**

```python
DISPLAY_TYPE = "pimoroni"
WIDTH = 320
HEIGHT = 240
ORIENTATION = "landscape"
STATUS_BAR_HEIGHT = 20
```

The `DISPLAY_TYPE` remains `"pimoroni"` so all existing screen routing, interaction profile detection, and theme logic works unchanged.

**RGB565 conversion:**

```python
def _pil_to_rgb565(self, image: Image.Image) -> bytes:
    """Convert PIL RGB image to RGB565 bytes for SPI."""
    pixels = image.tobytes()
    rgb565 = bytearray(self.WIDTH * self.HEIGHT * 2)
    for i in range(0, len(pixels), 3):
        r, g, b = pixels[i], pixels[i + 1], pixels[i + 2]
        val = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        j = (i // 3) * 2
        rgb565[j] = (val >> 8) & 0xFF
        rgb565[j + 1] = val & 0xFF
    return bytes(rgb565)
```

### 3. gpiod Button Adapter

**File:** `src/yoyopod/ui/input/adapters/gpiod_buttons.py`

Implements `InputHAL` for 4-button input via gpiod, replacing the `displayhatmini`-dependent `FourButtonInputAdapter` on non-Pi boards.

**Responsibilities:**
- Request 4 GPIO lines via gpiod with pull-up bias and active-low polarity
- Poll at 10ms intervals in a daemon thread
- Debounce at 50ms
- Long press detection at 1.0s (B long press -> HOME)
- Fire `InputAction` callbacks through the standard HAL interface

**Interface:**

```python
class GpiodButtonAdapter(InputHAL):
    def __init__(self, pin_config: dict, simulate: bool = False) -> None: ...
    # pin_config: {"a": {"chip": "gpiochip0", "line": 34}, "b": {...}, ...}

    def start(self) -> None: ...
    def stop(self) -> None: ...
    def on_action(self, action: InputAction, callback) -> None: ...
    def clear_callbacks(self) -> None: ...
    def get_capabilities(self) -> list[InputAction]: ...
```

**Button mapping** (same as existing `FourButtonInputAdapter`):

| Button | Short Press | Long Press (1.0s) |
|---|---|---|
| A | SELECT | - |
| B | BACK | HOME |
| X | UP | - |
| Y | DOWN | - |

The polling loop logic (state tracking, debounce, long press detection) is ported from `four_button.py` with the only change being GPIO reads via gpiod instead of `displayhatmini`.

### 4. Board GPIO Configuration

**File:** `config/boards/radxa-cubie-a7z/yoyopod_config.yaml` (additions)

```yaml
display:
  pimoroni_gpio:
    spi_bus: 1
    spi_device: 0
    spi_speed_hz: 60000000
    dc: { chip: "gpiochip0", line: 109 }
    cs: { chip: "gpiochip0", line: 110 }
    backlight: { chip: "gpiochip1", line: 35 }
    led_r: { chip: "gpiochip0", line: 33 }
    led_g: { chip: "gpiochip1", line: 6 }
    led_b: { chip: "gpiochip1", line: 7 }

input:
  pimoroni_gpio:
    button_a: { chip: "gpiochip0", line: 34 }
    button_b: { chip: "gpiochip0", line: 35 }
    button_x: { chip: "gpiochip0", line: 36 }
    button_y: { chip: "gpiochip0", line: 313 }
```

### 5. Factory Integration

**Display factory** (`src/yoyopod/ui/display/factory.py`):

When `hardware == "pimoroni"`:
1. Try importing `displayhatmini` -> use existing `PimoroniDisplayAdapter` (Pi path)
2. If import fails, check for `pimoroni_gpio` in board config -> use `CubiePimoroniAdapter`
3. If neither, fall back to simulation

**Input factory** (`src/yoyopod/ui/input/factory.py`):

When display type is `"pimoroni"`:
1. If `displayhatmini` available -> use existing `FourButtonInputAdapter` (Pi path)
2. If unavailable but `pimoroni_gpio` input config exists -> use `GpiodButtonAdapter`
3. Fallback: keyboard adapter

### 6. Config Models

**File:** `src/yoyopod/config/models.py` (additions)

Add typed config models for the GPIO pin mapping:

```python
@dataclass
class GpioPin:
    chip: str
    line: int

@dataclass
class PimoroniGpioConfig:
    spi_bus: int = 1
    spi_device: int = 0
    spi_speed_hz: int = 60_000_000
    dc: GpioPin | None = None
    cs: GpioPin | None = None
    backlight: GpioPin | None = None
    led_r: GpioPin | None = None
    led_g: GpioPin | None = None
    led_b: GpioPin | None = None

@dataclass
class PimoroniGpioInputConfig:
    button_a: GpioPin | None = None
    button_b: GpioPin | None = None
    button_x: GpioPin | None = None
    button_y: GpioPin | None = None
```

## Known Risks

### DC Pin (PIN_21 / SPI MISO)

The Pimoroni HAT physically routes the ST7789 DC signal to PIN_21, which is SPI1 MISO on the Cubie. The kernel SPI driver may hold this pin via pinmux.

**Mitigation (try in order):**
1. Claim via gpiod while spidev is loaded (often works if MISO is unused)
2. Set `SPI_3WIRE` mode on spidev to release MISO
3. Create a custom DT overlay that maps SPI1 without MISO

### Button X (PIN_36)

Kernel debug GPIO shows no active consumer, but `gpioinfo` marks it as kernel-used. Likely associated with the I2S pin group in the device tree.

**Mitigation:**
1. Try to claim via gpiod - may work since no active consumer
2. If blocked, skip Button X initially (3-button operation: A/B/Y)
3. If needed, create a DT overlay to release PIN_36 from the I2S group

## What Does NOT Change

- Existing Pi Pimoroni path (`pimoroni.py`, `four_button.py`) - untouched
- Whisplay path - untouched
- All screen implementations - hardware-agnostic via DisplayHAL + InputHAL
- Screen routing, theme, navigation model
- `DISPLAY_TYPE = "pimoroni"` -> InteractionProfile.STANDARD (4-button)
- Status bar rendering logic

## Validation Plan

1. Stop YoyoPod service on Cubie (`sudo systemctl stop yoyopod@radxa`)
2. Set `YOYOPOD_DISPLAY=pimoroni` and `YOYOPOD_CONFIG_BOARD=radxa-cubie-a7z`
3. Run `python yoyopod.py` with the new driver
4. Verify display initialization (ST7789 commands, backlight on)
5. Verify pixel output (home screen renders correctly)
6. Verify button input (all 4 buttons, debounce, long press)
7. Verify RGB LED (on/off per channel)
8. Walk through all screens and transitions
9. Test screen timeout and wake behavior
