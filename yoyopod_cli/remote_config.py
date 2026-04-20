"""Show or edit deploy/pi-deploy.local.yaml (the per-host override file)."""

from __future__ import annotations

import os
import subprocess

import typer
import yaml

from yoyopod_cli.defaults import DEFAULT_TEST_MUSIC_TARGET_DIR
from yoyopod_cli.paths import HOST, load_pi_paths
from yoyopod_cli.remote_shared import _resolve_remote_connection

app = typer.Typer(name="config", help="Show or edit pi-deploy.local.yaml.", no_args_is_help=True)


@app.command()
def show() -> None:
    """Print the effective pi-deploy config (base merged with local override)."""
    conn = _resolve_remote_connection("", "", "", "")
    pi = load_pi_paths()

    effective = {
        "host": conn.host,
        "user": conn.user,
        "project_dir": conn.project_dir,
        "branch": conn.branch,
        "venv": pi.venv,
        "start_cmd": pi.start_cmd,
        "log_file": pi.log_file,
        "error_log_file": pi.error_log_file,
        "pid_file": pi.pid_file,
        "screenshot_path": pi.screenshot_path,
        "test_music_target_dir": pi.test_music_target_dir,
        "startup_marker": pi.startup_marker,
        "kill_processes": list(pi.kill_processes),
        "rsync_exclude": list(pi.rsync_exclude),
    }
    typer.echo(yaml.safe_dump(effective, sort_keys=False))


@app.command()
def edit() -> None:
    """Open deploy/pi-deploy.local.yaml in $EDITOR."""
    path = HOST.deploy_config_local
    if not path.exists():
        path.write_text(
            "# Host-specific overrides for deploy/pi-deploy.yaml\n"
            "# host: rpi-zero\n"
            "# user: pi\n"
            "# project_dir: ~/YoyoPod_Core\n"
            f"# test_music_target_dir: {DEFAULT_TEST_MUSIC_TARGET_DIR}\n",
            encoding="utf-8",
        )
    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, str(path)], check=False)
