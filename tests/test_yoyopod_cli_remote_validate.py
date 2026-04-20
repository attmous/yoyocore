"""Tests for yoyopod_cli.remote_validate."""
from __future__ import annotations

from typer.testing import CliRunner

from yoyopod_cli.remote_validate import app, _build_validate, _build_preflight_steps


def _collect_option_names(click_cmd: object) -> set[str]:
    names: set[str] = set()
    for param in getattr(click_cmd, "params", []):
        names.update(getattr(param, "opts", []))
    return names


def test_build_preflight_steps_include_git_and_quality() -> None:
    steps = _build_preflight_steps()
    assert any("git diff" in " ".join(argv) for _, argv in steps)
    assert any("quality.py" in " ".join(argv) for _, argv in steps)


def test_build_validate_minimal() -> None:
    shell = _build_validate(with_music=False, with_voip=False, with_lvgl_soak=False, with_navigation=False)
    assert "yoyopod pi validate deploy" in shell
    assert "yoyopod pi validate smoke" in shell
    assert "voip" not in shell
    assert "lvgl" not in shell
    assert "navigation" not in shell


def test_build_validate_all_flags() -> None:
    shell = _build_validate(with_music=True, with_voip=True, with_lvgl_soak=True, with_navigation=True)
    assert "yoyopod pi validate music" in shell
    assert "yoyopod pi validate voip" in shell
    assert "yoyopod pi validate lvgl" in shell
    assert "yoyopod pi validate navigation" in shell


def test_build_validate_only_music() -> None:
    shell = _build_validate(with_music=True, with_voip=False, with_lvgl_soak=False, with_navigation=False)
    assert "yoyopod pi validate music" in shell
    assert "voip" not in shell


def test_preflight_help() -> None:
    runner = CliRunner(env={'COLUMNS': '200'})
    result = runner.invoke(app, ["preflight", "--help"])
    assert result.exit_code == 0


def test_validate_has_all_with_flags() -> None:
    import typer.main

    click_cmd = typer.main.get_command(app)
    validate_cmd = click_cmd.commands["validate"]  # type: ignore[attr-defined]
    names = _collect_option_names(validate_cmd)
    for flag in ("--with-music", "--with-voip", "--with-lvgl-soak", "--with-navigation"):
        assert flag in names
