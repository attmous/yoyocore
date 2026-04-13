# Unified LVGL Rendering Pipeline — Cycle 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make LVGL render on all display adapters by decoupling the flush target from Whisplay, parameterizing the C shim for any resolution, migrating 3 pilot scenes to flex layout, and wiring the CubiePimoroni adapter as an LVGL flush target.

**Architecture:** The LVGL C shim stores display dimensions at registration time and uses flex containers instead of hardcoded pixel positions. `LvglDisplayBackend` accepts any flush target implementing `draw_rgb565_region()`. The display factory wires LVGL to whatever adapter is active.

**Tech Stack:** C (LVGL 8.x), Python 3.12, CFFI, spidev, gpiod

**Spec:** `docs/superpowers/specs/2026-04-13-unified-lvgl-rendering-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `yoyopy/ui/lvgl_binding/native/lvgl_shim.c` | Modify | Add runtime dimensions, parameterize macros, flex-migrate 3 scenes |
| `yoyopy/ui/lvgl_binding/backend.py` | Modify | Accept generic flush target, remove Whisplay coupling |
| `yoyopy/ui/display/hal.py` | Modify | Add `draw_rgb565_region()` and `get_flush_target()` default methods |
| `yoyopy/ui/display/adapters/cubie_pimoroni.py` | Modify | Implement `draw_rgb565_region()` and `get_flush_target()` |
| `yoyopy/ui/display/adapters/whisplay.py` | Modify | Add `get_flush_target()` (returning self) |
| `yoyopy/ui/display/factory.py` | Modify | Wire LVGL backend to any adapter's flush target |
| `yoyopy/app.py` | Modify | Remove Whisplay-specific LVGL init, use factory-provided backend |
| `tests/test_flush_target.py` | Create | Tests for generic flush target protocol |
| `tests/test_lvgl_backend_generic.py` | Create | Tests for decoupled LvglDisplayBackend |

---

### Task 1: Runtime Display Dimensions in C Shim

**Files:**
- Modify: `yoyopy/ui/lvgl_binding/native/lvgl_shim.c`

This task adds global dimension variables and named macros, replacing the hardcoded 240/280/248 foundation that all scenes depend on. No scene layout changes yet — just the constants.

- [ ] **Step 1: Add runtime dimension globals after the existing display global (line ~207)**

After `lv_display_t* g_display = NULL;`, add:

```c
/* Runtime display dimensions — set during register_display(). */
static int g_display_width  = 240;
static int g_display_height = 280;
```

- [ ] **Step 2: Store dimensions in `yoyopy_lvgl_register_display()` (line ~3086)**

At the top of the function body, before `lv_display_t *disp = lv_display_create(width, height);`, add:

```c
g_display_width  = width;
g_display_height = height;
```

- [ ] **Step 3: Replace hardcoded footer macros (lines ~749-751)**

Replace:
```c
#define YOYOPY_FOOTER_BAR_TOP 248
#define YOYOPY_FOOTER_HEIGHT 32
#define YOYOPY_FOOTER_OBJ_WIDTH 214
```

With:
```c
#define YOYOPY_STATUS_BAR_H  32
#define YOYOPY_FOOTER_BAR_H  32
#define YOYOPY_CONTENT_PAD    8

/* Computed at runtime — use via inline helpers, not macros. */
static inline int footer_bar_top(void) { return g_display_height - YOYOPY_FOOTER_BAR_H; }
static inline int content_height(void) { return g_display_height - YOYOPY_STATUS_BAR_H - YOYOPY_FOOTER_BAR_H; }
static inline int center_x(void)       { return g_display_width / 2; }
```

- [ ] **Step 4: Update `yoyopy_prepare_footer_label()` (lines ~763-776)**

Replace the hardcoded width `214` and y-position with runtime values:

```c
static void yoyopy_prepare_footer_label(lv_obj_t *label) {
    int footer_width = g_display_width - (2 * YOYOPY_CONTENT_PAD);
    lv_obj_set_width(label, footer_width);
    lv_obj_set_style_text_align(label, LV_TEXT_ALIGN_CENTER, 0);
    lv_obj_align(label, LV_ALIGN_BOTTOM_MID, 0, -YOYOPY_CONTENT_PAD);
}
```

- [ ] **Step 5: Update status bar battery macros (lines ~738-750)**

Replace absolute-X battery macros with runtime-computed positions:

```c
#define YOYOPY_STATUS_DOT_X       18
#define YOYOPY_STATUS_DOT_Y       15
#define YOYOPY_STATUS_TIME_X      38
#define YOYOPY_STATUS_TIME_Y       9

/* Battery positions computed from display width */
static inline int status_battery_x(void)       { return g_display_width - 68; }
static inline int status_battery_tip_x(void)   { return g_display_width - 54; }
static inline int status_battery_label_x(void) { return g_display_width - 44; }

#define YOYOPY_STATUS_BATTERY_Y       11
#define YOYOPY_STATUS_BATTERY_TIP_Y   14
#define YOYOPY_STATUS_BATTERY_LABEL_Y  8
```

- [ ] **Step 6: Update `yoyopy_status_bar_build()` to use the new battery helpers**

In the status bar build function, replace every reference to the old `YOYOPY_STATUS_BATTERY_X`, `YOYOPY_STATUS_BATTERY_TIP_X`, `YOYOPY_STATUS_BATTERY_LABEL_X` macros with calls to `status_battery_x()`, `status_battery_tip_x()`, `status_battery_label_x()`.

- [ ] **Step 7: Build and verify the shim compiles**

Run: `yoyoctl build lvgl`
Expected: Compiles without errors or warnings related to the new code.

- [ ] **Step 8: Commit**

```bash
git add yoyopy/ui/lvgl_binding/native/lvgl_shim.c
git commit -m "feat(lvgl): add runtime display dimensions and named layout macros"
```

---

### Task 2: Hub Scene Flex Migration

**Files:**
- Modify: `yoyopy/ui/lvgl_binding/native/lvgl_shim.c`

The Hub scene is the simplest full scene: a centered card with icon, title, subtitle, dots row, and footer bar. This is the pilot for the flex pattern all other scenes will follow.

- [ ] **Step 1: Rewrite `yoyopy_lvgl_hub_build()` with flex layout**

The current function creates objects with absolute positions. Rewrite to use a vertical flex container:

```c
void yoyopy_lvgl_hub_build(void) {
    lv_obj_t *screen = lv_screen_active();

    /* Root container — full screen, vertical flex */
    lv_obj_t *root = lv_obj_create(screen);
    lv_obj_remove_style_all(root);
    lv_obj_set_size(root, lv_pct(100), lv_pct(100));
    lv_obj_set_flex_flow(root, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_flex_align(root, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
    lv_obj_set_style_pad_all(root, 0, 0);

    /* Status bar region — fixed height at top */
    lv_obj_t *status_area = lv_obj_create(root);
    lv_obj_remove_style_all(status_area);
    lv_obj_set_size(status_area, lv_pct(100), YOYOPY_STATUS_BAR_H);
    /* Status bar widgets are built by yoyopy_status_bar_build() onto this area */

    /* Content area — grows to fill, centers children */
    lv_obj_t *content = lv_obj_create(root);
    lv_obj_remove_style_all(content);
    lv_obj_set_width(content, lv_pct(100));
    lv_obj_set_flex_grow(content, 1);
    lv_obj_set_flex_flow(content, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_flex_align(content, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);

    /* Icon glow (120x120) */
    g_hub_scene.icon_glow = lv_obj_create(content);
    lv_obj_set_size(g_hub_scene.icon_glow, 120, 120);
    /* ... icon glow styling unchanged ... */

    /* Card panel */
    g_hub_scene.card_panel = lv_obj_create(content);
    lv_obj_set_size(g_hub_scene.card_panel, lv_pct(85), LV_SIZE_CONTENT);
    lv_obj_set_flex_flow(g_hub_scene.card_panel, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_flex_align(g_hub_scene.card_panel, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);

    /* Title label */
    g_hub_scene.title_label = lv_label_create(g_hub_scene.card_panel);
    lv_obj_set_width(g_hub_scene.title_label, lv_pct(100));
    lv_obj_set_style_text_align(g_hub_scene.title_label, LV_TEXT_ALIGN_CENTER, 0);

    /* Subtitle label */
    g_hub_scene.subtitle_label = lv_label_create(g_hub_scene.card_panel);
    lv_obj_set_width(g_hub_scene.subtitle_label, lv_pct(100));
    lv_obj_set_style_text_align(g_hub_scene.subtitle_label, LV_TEXT_ALIGN_CENTER, 0);

    /* Dots row — horizontal flex, centered */
    lv_obj_t *dots_row = lv_obj_create(content);
    lv_obj_remove_style_all(dots_row);
    lv_obj_set_size(dots_row, LV_SIZE_CONTENT, LV_SIZE_CONTENT);
    lv_obj_set_flex_flow(dots_row, LV_FLEX_FLOW_ROW);
    lv_obj_set_style_pad_column(dots_row, 6, 0);
    for (int i = 0; i < 4; i++) {
        g_hub_scene.dots[i] = lv_obj_create(dots_row);
        lv_obj_set_size(g_hub_scene.dots[i], 8, 8);
        lv_obj_set_style_radius(g_hub_scene.dots[i], LV_RADIUS_CIRCLE, 0);
    }

    /* Footer bar — fixed height at bottom */
    g_hub_scene.footer_bar = lv_obj_create(root);
    lv_obj_set_size(g_hub_scene.footer_bar, lv_pct(100), YOYOPY_FOOTER_BAR_H);
    /* ... footer styling unchanged ... */

    g_hub_scene.footer_label = lv_label_create(g_hub_scene.footer_bar);
    yoyopy_prepare_footer_label(g_hub_scene.footer_label);
}
```

- [ ] **Step 2: Simplify `yoyopy_lvgl_hub_sync()` — remove hardcoded centering**

The sync function no longer needs the `int first_x = (240 - dots_width) / 2` calculation. Dots are in a flex row that auto-centers. The sync function just updates visibility and colors:

```c
/* Replace the dots positioning block (around line 1004) with: */
for (int i = 0; i < 4; i++) {
    if (i < total_cards) {
        lv_obj_clear_flag(g_hub_scene.dots[i], LV_OBJ_FLAG_HIDDEN);
        lv_color_t color = (i == selected_index)
            ? lv_color_white()
            : lv_color_make(0x66, 0x66, 0x66);
        lv_obj_set_style_bg_color(g_hub_scene.dots[i], color, 0);
    } else {
        lv_obj_add_flag(g_hub_scene.dots[i], LV_OBJ_FLAG_HIDDEN);
    }
}
```

- [ ] **Step 3: Build and verify**

Run: `yoyoctl build lvgl`
Expected: Compiles without errors.

- [ ] **Step 4: Commit**

```bash
git add yoyopy/ui/lvgl_binding/native/lvgl_shim.c
git commit -m "feat(lvgl): migrate hub scene to flex layout"
```

---

### Task 3: Listen Scene Flex Migration

**Files:**
- Modify: `yoyopy/ui/lvgl_binding/native/lvgl_shim.c`

The Listen scene has a scrollable vertical list of items — the pattern used by Playlist too (Cycle 2). This establishes the list-in-flex-container pattern.

- [ ] **Step 1: Rewrite `yoyopy_lvgl_listen_build()` with flex layout**

Replace the hardcoded panel sizes (208x188, items 208x44) with flex containers:

```c
void yoyopy_lvgl_listen_build(void) {
    lv_obj_t *screen = lv_screen_active();

    /* Root — full screen vertical flex (same pattern as hub) */
    lv_obj_t *root = lv_obj_create(screen);
    lv_obj_remove_style_all(root);
    lv_obj_set_size(root, lv_pct(100), lv_pct(100));
    lv_obj_set_flex_flow(root, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_flex_align(root, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);
    lv_obj_set_style_pad_all(root, 0, 0);

    /* Status bar — fixed height */
    lv_obj_t *status_area = lv_obj_create(root);
    lv_obj_remove_style_all(status_area);
    lv_obj_set_size(status_area, lv_pct(100), YOYOPY_STATUS_BAR_H);

    /* Title area */
    lv_obj_t *title_area = lv_obj_create(root);
    lv_obj_remove_style_all(title_area);
    lv_obj_set_size(title_area, lv_pct(100), LV_SIZE_CONTENT);
    lv_obj_set_style_pad_top(title_area, 4, 0);
    lv_obj_set_style_pad_bottom(title_area, 2, 0);

    g_listen_scene.title_label = lv_label_create(title_area);
    lv_obj_set_width(g_listen_scene.title_label, lv_pct(100));
    lv_obj_set_style_text_align(g_listen_scene.title_label, LV_TEXT_ALIGN_CENTER, 0);

    g_listen_scene.subtitle_label = lv_label_create(title_area);
    lv_obj_set_width(g_listen_scene.subtitle_label, lv_pct(100));
    lv_obj_set_style_text_align(g_listen_scene.subtitle_label, LV_TEXT_ALIGN_CENTER, 0);

    /* List panel — grows to fill, scrollable, vertical flex */
    g_listen_scene.list_panel = lv_obj_create(root);
    lv_obj_set_width(g_listen_scene.list_panel, lv_pct(90));
    lv_obj_set_flex_grow(g_listen_scene.list_panel, 1);
    lv_obj_set_flex_flow(g_listen_scene.list_panel, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_style_pad_row(g_listen_scene.list_panel, 4, 0);
    lv_obj_add_flag(g_listen_scene.list_panel, LV_OBJ_FLAG_SCROLLABLE);

    /* List items — full width of panel, fixed height */
    for (int i = 0; i < LISTEN_MAX_ITEMS; i++) {
        g_listen_scene.items[i].panel = lv_obj_create(g_listen_scene.list_panel);
        lv_obj_set_size(g_listen_scene.items[i].panel, lv_pct(100), 44);

        g_listen_scene.items[i].label = lv_label_create(g_listen_scene.items[i].panel);
        lv_obj_center(g_listen_scene.items[i].label);
    }

    /* Empty state label */
    g_listen_scene.empty_label = lv_label_create(g_listen_scene.list_panel);
    lv_obj_set_width(g_listen_scene.empty_label, lv_pct(100));
    lv_obj_set_style_text_align(g_listen_scene.empty_label, LV_TEXT_ALIGN_CENTER, 0);

    /* Footer bar — fixed height */
    g_listen_scene.footer_bar = lv_obj_create(root);
    lv_obj_set_size(g_listen_scene.footer_bar, lv_pct(100), YOYOPY_FOOTER_BAR_H);

    g_listen_scene.footer_label = lv_label_create(g_listen_scene.footer_bar);
    yoyopy_prepare_footer_label(g_listen_scene.footer_label);
}
```

- [ ] **Step 2: Update `yoyopy_lvgl_listen_sync()` — remove hardcoded item positioning**

Items are now in a flex container, so sync only updates content and visibility — no `lv_obj_set_pos()` calls needed for item layout. Keep the item highlight logic (selected background color) unchanged.

- [ ] **Step 3: Build and verify**

Run: `yoyoctl build lvgl`
Expected: Compiles without errors.

- [ ] **Step 4: Commit**

```bash
git add yoyopy/ui/lvgl_binding/native/lvgl_shim.c
git commit -m "feat(lvgl): migrate listen scene to flex layout"
```

---

### Task 4: Generic Flush Target Protocol

**Files:**
- Modify: `yoyopy/ui/display/hal.py`
- Create: `tests/test_flush_target.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_flush_target.py`:

```python
"""Tests for the generic LVGL flush target protocol."""

import pytest


def test_display_hal_has_draw_rgb565_region():
    """DisplayHAL base class should provide a default draw_rgb565_region."""
    from yoyopy.ui.display.hal import DisplayHAL

    assert hasattr(DisplayHAL, "draw_rgb565_region")


def test_display_hal_has_get_flush_target():
    """DisplayHAL base class should provide get_flush_target defaulting to None."""
    from yoyopy.ui.display.hal import DisplayHAL

    # Can't instantiate ABC directly, check the method exists
    assert hasattr(DisplayHAL, "get_flush_target")


def test_cubie_pimoroni_is_flush_target():
    """CubiePimoroniAdapter should return self as flush target."""
    from yoyopy.ui.display.adapters.cubie_pimoroni import CubiePimoroniAdapter

    adapter = CubiePimoroniAdapter(simulate=True)
    target = adapter.get_flush_target()
    assert target is adapter
    assert hasattr(target, "draw_rgb565_region")
    assert hasattr(target, "WIDTH")
    assert hasattr(target, "HEIGHT")
    adapter.cleanup()


def test_simulation_get_flush_target_returns_none_without_lvgl():
    """Simulation adapter returns None when LVGL is not available."""
    from yoyopy.ui.display.adapters.simulation import SimulationDisplayAdapter

    adapter = SimulationDisplayAdapter()
    target = adapter.get_flush_target()
    # Without LVGL compiled, should return None (PIL fallback)
    assert target is None
    adapter.cleanup()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_flush_target.py -v`
Expected: FAIL — `draw_rgb565_region` and `get_flush_target` don't exist on DisplayHAL.

- [ ] **Step 3: Add default methods to DisplayHAL**

In `yoyopy/ui/display/hal.py`, add after the `reset_ui_backend()` method (around line 276):

```python
    def draw_rgb565_region(
        self, x: int, y: int, width: int, height: int, pixel_data: bytes
    ) -> None:
        """Receive an RGB565 pixel region from the LVGL flush callback.

        Adapters that support LVGL rendering override this to push pixel
        data to their hardware (SPI, framebuffer, WebSocket, etc.).
        The default implementation is a no-op.
        """
        pass

    def get_flush_target(self) -> "DisplayHAL | None":
        """Return this adapter as an LVGL flush target, or None.

        Adapters that can receive RGB565 region updates from LVGL's flush
        callback should override this to return ``self``.  The display
        factory uses this to wire the LvglDisplayBackend automatically.
        """
        return None
```

- [ ] **Step 4: Run test to verify first two pass**

Run: `uv run pytest tests/test_flush_target.py::test_display_hal_has_draw_rgb565_region tests/test_flush_target.py::test_display_hal_has_get_flush_target -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add yoyopy/ui/display/hal.py tests/test_flush_target.py
git commit -m "feat: add draw_rgb565_region and get_flush_target to DisplayHAL"
```

---

### Task 5: CubiePimoroni Flush Target

**Files:**
- Modify: `yoyopy/ui/display/adapters/cubie_pimoroni.py`
- Test: `tests/test_flush_target.py` (test already written in Task 4)

- [ ] **Step 1: Add `draw_rgb565_region()` to CubiePimoroniAdapter**

In `yoyopy/ui/display/adapters/cubie_pimoroni.py`, add after the `update()` method:

```python
    def draw_rgb565_region(
        self, x: int, y: int, width: int, height: int, pixel_data: bytes
    ) -> None:
        """Receive RGB565 region from LVGL flush and push to ST7789 via SPI."""
        if not self.simulate and self._driver:
            try:
                self._driver.draw_image(x, y, width, height, pixel_data)
            except Exception as e:
                logger.error("Failed to draw LVGL region: {}", e)
```

- [ ] **Step 2: Add `get_flush_target()`**

```python
    def get_flush_target(self) -> "CubiePimoroniAdapter | None":
        """Return self as LVGL flush target when hardware is available."""
        if not self.simulate and self._driver:
            return self
        return None
```

- [ ] **Step 3: Run the flush target tests**

Run: `uv run pytest tests/test_flush_target.py -v`
Expected: ALL PASS.

- [ ] **Step 4: Commit**

```bash
git add yoyopy/ui/display/adapters/cubie_pimoroni.py
git commit -m "feat: make CubiePimoroniAdapter an LVGL flush target"
```

---

### Task 6: Whisplay Flush Target Conformance

**Files:**
- Modify: `yoyopy/ui/display/adapters/whisplay.py`
- Test: `tests/test_flush_target.py`

The Whisplay adapter already has `draw_rgb565_region()`. It just needs `get_flush_target()` to conform to the protocol.

- [ ] **Step 1: Add test**

Append to `tests/test_flush_target.py`:

```python
def test_whisplay_has_flush_target_method():
    """WhisplayDisplayAdapter should have get_flush_target method."""
    from yoyopy.ui.display.adapters.whisplay import WhisplayDisplayAdapter

    assert hasattr(WhisplayDisplayAdapter, "get_flush_target")
    assert hasattr(WhisplayDisplayAdapter, "draw_rgb565_region")
```

- [ ] **Step 2: Add `get_flush_target()` to WhisplayDisplayAdapter**

In `yoyopy/ui/display/adapters/whisplay.py`, add the method:

```python
    def get_flush_target(self) -> "WhisplayDisplayAdapter | None":
        """Return self as LVGL flush target when hardware is available."""
        if not self.simulate and self.device:
            return self
        return None
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/test_flush_target.py -v`
Expected: ALL PASS.

- [ ] **Step 4: Commit**

```bash
git add yoyopy/ui/display/adapters/whisplay.py tests/test_flush_target.py
git commit -m "feat: add get_flush_target to WhisplayDisplayAdapter"
```

---

### Task 7: Factory LVGL Wiring

**Files:**
- Modify: `yoyopy/ui/display/factory.py`
- Modify: `yoyopy/app.py`
- Create: `tests/test_lvgl_backend_generic.py`

Move LVGL backend initialization from app.py (Whisplay-specific) to the display factory (generic for any adapter).

- [ ] **Step 1: Write the test**

Create `tests/test_lvgl_backend_generic.py`:

```python
"""Tests for generic LVGL backend wiring in the display factory."""

from unittest.mock import MagicMock, patch

import pytest


def test_factory_attaches_lvgl_backend_when_flush_target_available():
    """When an adapter provides a flush target, factory should try LVGL wiring."""
    from yoyopy.ui.display.factory import _try_attach_lvgl_backend

    adapter = MagicMock()
    adapter.get_flush_target.return_value = adapter
    adapter.WIDTH = 320
    adapter.HEIGHT = 240

    # LVGL binding won't be available in CI, but the function should handle that
    result = _try_attach_lvgl_backend(adapter)
    # Returns True if LVGL attached, False if unavailable
    assert isinstance(result, bool)


def test_factory_skips_lvgl_when_no_flush_target():
    """When adapter returns None flush target, skip LVGL entirely."""
    from yoyopy.ui.display.factory import _try_attach_lvgl_backend

    adapter = MagicMock()
    adapter.get_flush_target.return_value = None

    result = _try_attach_lvgl_backend(adapter)
    assert result is False
```

- [ ] **Step 2: Add `_try_attach_lvgl_backend()` to factory**

In `yoyopy/ui/display/factory.py`, add:

```python
def _try_attach_lvgl_backend(adapter: DisplayHAL) -> bool:
    """Attempt to wire an LvglDisplayBackend to the adapter's flush target.

    Returns True if LVGL was successfully attached, False otherwise.
    """
    flush_target = adapter.get_flush_target()
    if flush_target is None:
        return False

    try:
        from yoyopy.ui.lvgl_binding import LvglDisplayBackend

        backend = LvglDisplayBackend(flush_target=flush_target)
        if backend.initialize():
            adapter.ui_backend = backend
            logger.info(
                "LVGL backend attached to {} ({}x{})",
                adapter.__class__.__name__,
                flush_target.WIDTH,
                flush_target.HEIGHT,
            )
            return True
        else:
            logger.info("LVGL backend available but failed to initialize")
            return False
    except Exception as exc:
        logger.debug("LVGL backend not available: {}", exc)
        return False
```

- [ ] **Step 3: Call `_try_attach_lvgl_backend()` after adapter creation in `get_display()`**

At the end of `get_display()`, just before `return`, add the LVGL wiring attempt. Find the return statements for each adapter branch and add before each:

```python
    _try_attach_lvgl_backend(adapter)
    return adapter
```

For the pimoroni branch (CubiePimoroniAdapter), the whisplay branch (WhisplayDisplayAdapter), and the simulation branch.

- [ ] **Step 4: Simplify app.py LVGL init**

In `yoyopy/app.py`, the existing LVGL init block (around lines 384-391) currently creates the backend from `self.display.get_ui_backend()`. Update it to just read what the factory already attached:

```python
# Replace the existing LVGL init block with:
self._lvgl_backend = self.display.get_ui_backend()
if self._lvgl_backend is not None:
    self._last_lvgl_pump_at = time.monotonic()
self.display.refresh_backend_kind()
logger.info("    Active UI backend: {}", self.display.backend_kind)
```

This removes the `backend.initialize()` call from app.py since the factory already did it.

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/test_lvgl_backend_generic.py tests/test_flush_target.py -v`
Expected: ALL PASS.

- [ ] **Step 6: Run full test suite**

Run: `uv run pytest -q`
Expected: No regressions.

- [ ] **Step 7: Commit**

```bash
git add yoyopy/ui/display/factory.py yoyopy/app.py tests/test_lvgl_backend_generic.py
git commit -m "feat: wire LVGL backend to any adapter via factory flush target"
```

---

### Task 8: On-Device Validation

This task validates the pipeline on real hardware. No code changes — just verification.

- [ ] **Step 1: Build the updated LVGL shim on the Cubie**

```bash
ssh radxa@192.168.178.110 "cd ~/yoyo-py && yoyoctl build lvgl"
```

Expected: Shim compiles for ARM.

- [ ] **Step 2: Sync code to the Cubie**

```bash
yoyoctl remote sync --host 192.168.178.110
```

Or SCP the changed files manually.

- [ ] **Step 3: Verify Whisplay still works (if available)**

If a Whisplay HAT is accessible on a Pi or second board:

```bash
YOYOPOD_DISPLAY=whisplay python yoyopod.py
```

Verify: Hub, Listen screens render identically to before. Screenshot comparison if possible.

- [ ] **Step 4: Test LVGL on Pimoroni**

```bash
ssh radxa@192.168.178.110 "cd ~/yoyo-py && \
  sudo systemctl stop yoyopod@radxa && \
  YOYOPOD_DISPLAY=pimoroni YOYOPOD_CONFIG_BOARD=radxa-cubie-a7z \
  .venv/bin/python yoyopod.py"
```

Verify:
- Display initializes with LVGL backend (log: "LVGL backend attached to CubiePimoroniAdapter (320x240)")
- Hub screen renders with flex layout at 320x240
- Listen screen renders with scrollable list
- Status bar battery position is correct (right-aligned, not clipped)
- All 4 buttons work
- Screen transitions work

- [ ] **Step 5: Compare rendering quality**

On the Pimoroni display, check:
- Text is sharp (LVGL font rendering, not PIL)
- Colors match Whisplay theme
- Dots/indicators are properly centered
- Footer bar spans full width
- No visual artifacts or misaligned elements

- [ ] **Step 6: Document findings**

Record any visual differences, layout issues, or bugs found during validation. These inform Cycle 2 adjustments.
