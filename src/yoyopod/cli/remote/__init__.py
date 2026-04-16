"""src/yoyopod/cli/remote/__init__.py — remote command group (SSH wrapper commands)."""

from __future__ import annotations

import typer

from yoyopod.cli.remote.infra import config, power, service
from yoyopod.cli.remote.lvgl import lvgl_soak
from yoyopod.cli.remote.ops import (
    logs,
    remote_preflight,
    remote_provision_test_music,
    remote_smoke,
    remote_validate,
    restart,
    rsync,
    rtc,
    screenshot,
    status,
    sync,
    whisplay,
)
from yoyopod.cli.remote.setup import setup, verify_setup

remote_app = typer.Typer(
    name="remote",
    help="Commands that SSH to the Raspberry Pi from the dev machine.",
    no_args_is_help=True,
)

remote_app.command()(status)
remote_app.command()(sync)
remote_app.command(name="validate")(remote_validate)
remote_app.command(name="smoke")(remote_smoke)
remote_app.command(name="provision-test-music")(remote_provision_test_music)
remote_app.command(name="preflight")(remote_preflight)
remote_app.command()(restart)
remote_app.command()(logs)
remote_app.command()(screenshot)
remote_app.command()(rsync)
remote_app.command(name="lvgl-soak")(lvgl_soak)


@remote_app.command(name="navigation-soak")
def navigation_soak_command(
    host: str = "",
    user: str = "",
    project_dir: str = "",
    branch: str = "",
    cycles: int = 2,
    hold_seconds: float = 0.35,
    idle_seconds: float = 3.0,
    tail_idle_seconds: float = 10.0,
    with_playback: bool = True,
    provision_test_music: bool = True,
    test_music_dir: str = "",
    skip_sleep: bool = False,
    verbose: bool = False,
) -> None:
    from yoyopod.cli.remote.navigation import navigation_soak

    return navigation_soak(
        host=host,
        user=user,
        project_dir=project_dir,
        branch=branch,
        cycles=cycles,
        hold_seconds=hold_seconds,
        idle_seconds=idle_seconds,
        tail_idle_seconds=tail_idle_seconds,
        with_playback=with_playback,
        provision_test_music=provision_test_music,
        test_music_dir=test_music_dir,
        skip_sleep=skip_sleep,
        verbose=verbose,
    )


remote_app.command()(power)
remote_app.command()(whisplay)
remote_app.command()(rtc)
remote_app.command()(config)
remote_app.command()(service)
remote_app.command()(setup)
remote_app.command(name="verify-setup")(verify_setup)
