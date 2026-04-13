# Unified LVGL Rendering Pipeline

**Date:** 2026-04-13
**Status:** Approved
**Goal:** Make LVGL the single rendering path for all three display adapters (Whisplay, Pimoroni, Simulation), eliminating the PIL fallback in screens and enabling consistent visual output across all hardware.

## Context

Screens currently maintain two rendering codepaths: LVGL widgets (Whisplay only) and PIL primitives (Pimoroni, Simulation). The PIL path is a maintenance burden — every screen duplicates layout code, and simulation doesn't show what production actually renders.

The LVGL binding layer is already resolution-agnostic in Python. The coupling is localized to ~30 lines of hardcoded pixel values in the C shim (`lvgl_shim.c`). The 14 Python screen views pass pure data (strings, numbers, state) and contain zero layout logic.

## Architecture

### Current State

```
Whisplay:    Screen → LVGL views → C shim → flush → Whisplay SPI (240x280)
Pimoroni:    Screen → PIL fallback → adapter → SPI (320x240)
Simulation:  Screen → PIL fallback → adapter → PNG → WebSocket (240x280)
```

### Target State

```
All displays:  Screen → LVGL views → C shim (flex layout) → flush → adapter.draw_rgb565_region()
                                                                       ├─ Whisplay:   SPI 240x280
                                                                       ├─ Pimoroni:   SPI 320x240
                                                                       └─ Simulation: framebuffer → PNG → WebSocket
```

LVGL is the only rendering path. The C shim accepts any display dimensions at registration time. Scenes use LVGL's flex layout engine to adapt naturally to portrait or landscape. Each adapter implements a `draw_rgb565_region()` method that receives partial RGB565 region updates from LVGL's flush callback.

## Components

### 1. C Shim: Flex Layout Migration (lvgl_shim.c)

Store display dimensions at registration time:

```c
static int g_display_width = 240;
static int g_display_height = 280;
```

Set during `register_display()` which already receives width and height from Python.

Rewrite all 11 scenes from absolute pixel positioning to LVGL's flex container system:

**Before** (hardcoded):
```c
lv_obj_set_pos(label, 120 - (text_width / 2), 140);
lv_obj_set_size(panel, 208, 188);
lv_obj_set_pos(footer, 0, 248);
```

**After** (flex):
```c
lv_obj_set_size(root, lv_pct(100), lv_pct(100));
lv_obj_set_flex_flow(root, LV_FLEX_FLOW_COLUMN);
lv_obj_set_flex_grow(content, 1);
lv_obj_set_flex_align(content, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
lv_obj_set_size(footer, lv_pct(100), YOYOPY_FOOTER_BAR_HEIGHT);
```

**Design constants that stay hardcoded** (these are design decisions, not layout):
- Icon sizes (56x56, 120x120)
- Font sizes
- Padding and margin values
- `YOYOPY_FOOTER_BAR_HEIGHT` (32px)
- `YOYOPY_STATUS_BAR_HEIGHT`

**Status bar macros** — battery position, time position, signal indicator position — recomputed from `g_display_width` instead of hardcoded to 240px offsets.

**All magic numbers** get named macros. No raw numeric constants for layout.

**Scene migration complexity:**

| Scene | Pattern | Effort |
|---|---|---|
| Status bar | Horizontal flex, battery right-aligned | Low |
| Hub | Vertical flex, centered card + dots | Low |
| Listen | Vertical flex, scrollable list | Low |
| Playlist | Vertical flex, scrollable list | Low |
| Ask | Vertical flex, centered icon + label | Low |
| Power | Vertical flex, icon + list items | Low |
| Incoming Call | Vertical flex, centered icon + text | Low |
| Outgoing Call | Vertical flex, centered icon + text | Low |
| In Call | Vertical flex, centered icon + mute chip | Low |
| Now Playing | Vertical + horizontal mix, progress bar | Medium |
| Talk | Horizontal card carousel + dots | Medium |
| Talk Actions | Dynamic button row + dots | Medium |

### 2. Generic LVGL Flush Target

Define a flush target protocol that any display adapter can implement:

```python
class LvglFlushTarget(Protocol):
    WIDTH: int
    HEIGHT: int

    def draw_rgb565_region(self, x: int, y: int, width: int, height: int, pixel_data: bytes) -> None: ...
```

`LvglDisplayBackend.__init__` accepts any object matching this protocol, not a Whisplay adapter specifically. The flush callback calls `target.draw_rgb565_region()` with partial region updates from LVGL.

### 3. Adapter Changes

**Whisplay**: No changes. Already implements `draw_rgb565_region()` and works as a flush target.

**CubiePimoroni**: Add `draw_rgb565_region()` as a thin wrapper around `ST7789SpiDriver.draw_image()` (same signature, same RGB565 format). Add `get_flush_target()` returning `self`.

**Simulation**: New capabilities:
- In-memory RGB565 framebuffer (`WIDTH * HEIGHT * 2` bytes) for compositing partial updates
- `draw_rgb565_region()` writes into the framebuffer at the correct offset
- On frame completion: convert framebuffer to PNG base64, push via WebSocket
- Resolution flag: `--simulate-display pimoroni|whisplay` to choose between 320x240 landscape and 240x280 portrait (default: whisplay for backward compat)

### 4. Factory and Backend Wiring

Display factory (`get_display()`) wires the LVGL backend after creating the adapter:

```python
adapter = create_adapter(...)
flush_target = adapter.get_flush_target()  # returns self or None

if flush_target is not None:
    try:
        backend = LvglDisplayBackend(flush_target)
        adapter.ui_backend = backend
    except Exception:
        pass  # LVGL not compiled — PIL fallback
```

This replaces the current Whisplay-specific LVGL initialization. The pattern works for all adapters.

### 5. PIL Fallback Strategy

PIL rendering code stays but becomes secondary:

**Keep PIL for:**
- Screenshot capture via shadow buffer
- Graceful degradation when LVGL C shim isn't compiled
- CI test environments without LVGL

**In screens:**
- PIL fallback branches (`else` in the dual-rendering pattern) become unreachable on LVGL-capable adapters
- No screen changes needed for this consolidation — screens already have LVGL views
- PIL branches can be deprecated and removed in a future cleanup pass

**In adapters:**
- PIL drawing methods (`clear()`, `text()`, `rectangle()`) stay on `DisplayHAL` for shadow buffer and backward compat
- They are no longer the primary rendering path

### 6. Screen Views

Zero changes. The 14 existing LVGL screen views pass pure data to the C shim. They work unchanged because:
- Resolution is handled by the C shim's flex layout
- Flush routing is handled by the backend's flush target
- Python views never reference pixel dimensions

## What Does NOT Change

- Whisplay display path — untouched, already on LVGL
- Screen view Python code (14 files) — zero changes
- LVGL binding.py — zero changes
- Input system — unrelated
- Screen navigation and routing — unrelated
- DisplayHAL interface — stays, gains optional `get_flush_target()`

## Known Risks

### LVGL Build on Dev Machines

The C shim must compile on the dev machine for simulation to use LVGL. If the build fails (missing C toolchain, LVGL headers), simulation falls back to PIL. This is acceptable — simulation without LVGL is worse but not broken.

Mitigation: `yoyoctl build lvgl` already handles cross-platform builds.

### Flex Layout Visual Regression on Whisplay

Rewriting scenes from absolute to flex positioning could introduce visual differences on the 240x280 Whisplay display.

Mitigation: validate each scene on Whisplay after migration. The screenshot comparison tool (`yoyoctl pi screenshot`) can catch regressions.

### Simulation Frame Rate

LVGL's partial updates mean the simulation adapter must composite regions into a full framebuffer before PNG conversion. This adds CPU overhead compared to direct PIL-to-PNG.

Mitigation: throttle WebSocket frame pushes (e.g., max 15fps). LVGL's `lv_refr_now()` timing already controls flush frequency.

## Validation Plan

1. Parameterize C shim — verify Whisplay still renders identically
2. Migrate one scene to flex (Hub, simplest) — verify on both 240x280 and 320x240
3. Complete all scene migrations — screenshot comparison on Whisplay
4. Wire CubiePimoroni as flush target — verify LVGL rendering on Pimoroni display
5. Wire Simulation as flush target — verify in browser
6. Walk all screens on both display sizes
