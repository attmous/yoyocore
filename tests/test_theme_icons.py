"""Tests for image-backed theme icons."""

from __future__ import annotations

from PIL import Image

from yoyopy.ui.display import Display
from yoyopy.ui.screens.theme import ICON_ASSET_DIR, draw_icon


def test_phosphor_icon_assets_exist_and_are_64px() -> None:
    """The checked-in Phosphor PNG assets should be present at the expected size."""
    expected_files = [
        "headphones.png",
        "chat-circle-dots.png",
        "microphone.png",
        "gear-six.png",
    ]

    for filename in expected_files:
        path = ICON_ASSET_DIR / filename
        assert path.exists(), f"Missing icon asset: {filename}"
        with Image.open(path) as image:
            assert image.size == (64, 64)


def test_draw_icon_renders_phosphor_png_into_buffer() -> None:
    """The root-mode icons should render via the PNG asset path on PIL-backed displays."""
    display = Display(simulate=True)
    try:
        buffer = display.get_adapter().buffer
        assert buffer is not None

        icon_names = ["listen", "talk", "ask", "setup"]
        for index, icon_name in enumerate(icon_names):
            draw_icon(display, icon_name, 10 + (index * 40), 10, 24, (255, 255, 255))

        cropped = buffer.crop((0, 0, 200, 50))
        assert cropped.getbbox() is not None
    finally:
        display.cleanup()
