"""
yoyopod — app launcher and CLI dispatcher.

Usage:
    yoyopod                      # Launch the YoyoPod app
    yoyopod deploy               # Sync code to the Pi and restart
    yoyopod status               # Pi health dashboard
    yoyopod logs [-f --errors]   # Tail logs from the Pi
    yoyopod restart              # Restart the app on the Pi
    yoyopod validate             # Run the validation suite on the Pi
    yoyopod remote <cmd>         # Dev-machine → Pi commands
    yoyopod pi <cmd>             # On-device commands
    yoyopod build <cmd>          # Native extension builds
    yoyopod setup <cmd>          # Host and Pi setup
"""

from __future__ import annotations

import typer

from yoyopod_cli import __version__

app = typer.Typer(
    name="yoyopod",
    help="YoyoPod app launcher and CLI.",
    no_args_is_help=False,
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"yoyopod {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Launch the YoyoPod app when invoked with no subcommand."""
    if ctx.invoked_subcommand is None:
        from yoyopod.main import main as launch_app

        launch_app()


def run() -> None:
    """Entry-point shim used by ``[project.scripts]``."""
    app()


# --- subapps ---
from yoyopod_cli import build as _build

app.add_typer(_build.app, name="build")

from yoyopod_cli import setup as _setup

app.add_typer(_setup.app, name="setup")

# --- remote group (assembled from flat sub-modules)
from yoyopod_cli import (
    remote_config as _remote_config,
    remote_infra as _remote_infra,
    remote_ops as _remote_ops,
    remote_setup as _remote_setup,
    remote_validate as _remote_validate,
)
from yoyopod_cli.remote_shared import build_remote_app as _build_remote_app

remote_app = _build_remote_app("remote", "Dev-machine -> Pi commands via SSH.")

# ops commands
remote_app.command(name="status")(_remote_ops.status)
remote_app.command(name="sync")(_remote_ops.sync)
remote_app.command(name="restart")(_remote_ops.restart)
remote_app.command(name="logs")(_remote_ops.logs)
remote_app.command(name="screenshot")(_remote_ops.screenshot)

# validate / preflight
remote_app.command(name="preflight")(_remote_validate.preflight)
remote_app.command(name="validate")(_remote_validate.validate)

# infra
remote_app.command(name="power")(_remote_infra.power)
remote_app.command(name="rtc")(_remote_infra.rtc)
remote_app.command(name="service")(_remote_infra.service)

# setup
remote_app.command(name="setup")(_remote_setup.setup)
remote_app.command(name="verify-setup")(_remote_setup.verify_setup)

# config (operates on local files — its own subgroup)
remote_app.add_typer(_remote_config.app, name="config")

app.add_typer(remote_app, name="remote")

# --- pi group (commands that run on the Pi directly)
from yoyopod_cli import (
    pi_network as _pi_network,
    pi_power as _pi_power,
    pi_validate as _pi_validate,
    pi_voip as _pi_voip,
)

pi_app = typer.Typer(name="pi", help="Commands that run on the Raspberry Pi.", no_args_is_help=True)
pi_app.add_typer(_pi_validate.app, name="validate")
pi_app.add_typer(_pi_voip.app, name="voip")
pi_app.add_typer(_pi_power.app, name="power")
pi_app.add_typer(_pi_network.app, name="network")

app.add_typer(pi_app, name="pi")
