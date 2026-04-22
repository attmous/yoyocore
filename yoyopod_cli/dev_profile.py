"""Developer-facing profiling wrappers around the repo-owned helper script."""

from __future__ import annotations

import subprocess
import sys
from typing import Optional

import typer

from yoyopod_cli.paths import HOST

app = typer.Typer(
    name="profile",
    help="Bounded profiling helpers for YoYoPod.",
    no_args_is_help=True,
)


def build_profile_script_command(*args: str) -> tuple[str, ...]:
    """Return the repo-owned profiling script command."""

    return (sys.executable, str(HOST.repo_root / "scripts" / "profile.py"), *args)


def _run_profile_script(*args: str) -> int:
    """Run the repo-owned profiling script from the repo root."""

    completed = subprocess.run(
        build_profile_script_command(*args),
        cwd=HOST.repo_root,
        check=False,
    )
    return completed.returncode


@app.command()
def targets() -> None:
    """List the bounded profiling targets."""

    raise typer.Exit(_run_profile_script("list-targets"))


@app.command()
def tools() -> None:
    """Show which profiling tools are available in this environment."""

    raise typer.Exit(_run_profile_script("tools"))


@app.command()
def cprofile(
    target: str = typer.Option(
        "simulate-bootstrap",
        "--target",
        help="Bounded profiling target to run.",
    ),
    iterations: Optional[int] = typer.Option(
        None,
        "--iterations",
        help="Override the target's default iteration count.",
    ),
    output: str = typer.Option(
        "",
        "--output",
        help="Write the .prof file here.",
    ),
    sort: str = typer.Option(
        "cumulative",
        "--sort",
        help="pstats sort key. Default: cumulative",
    ),
    top: int = typer.Option(
        30,
        "--top",
        help="Print this many top cProfile rows.",
    ),
) -> None:
    """Profile one bounded target with cProfile."""

    command: list[str] = ["cprofile", target, "--sort", sort, "--top", str(top)]
    if iterations is not None:
        command.extend(["--iterations", str(iterations)])
    if output:
        command.extend(["--output", output])
    raise typer.Exit(_run_profile_script(*command))


@app.command()
def pyinstrument(
    target: str = typer.Option(
        "simulate-bootstrap",
        "--target",
        help="Bounded profiling target to run.",
    ),
    iterations: Optional[int] = typer.Option(
        None,
        "--iterations",
        help="Override the target's default iteration count.",
    ),
    output: str = typer.Option(
        "",
        "--output",
        help="Write the report here.",
    ),
    interval: float = typer.Option(
        0.001,
        "--interval",
        help="Sampling interval in seconds.",
    ),
    html: bool = typer.Option(
        False,
        "--html",
        help="Write an HTML report instead of plain text.",
    ),
) -> None:
    """Profile one bounded target with pyinstrument."""

    command: list[str] = [
        "pyinstrument",
        target,
        "--interval",
        str(interval),
    ]
    if iterations is not None:
        command.extend(["--iterations", str(iterations)])
    if output:
        command.extend(["--output", output])
    if html:
        command.append("--html")
    raise typer.Exit(_run_profile_script(*command))


@app.command()
def pyperf(
    target: str = typer.Option(
        "simulate-bootstrap",
        "--target",
        help="Bounded profiling target to benchmark.",
    ),
    iterations: Optional[int] = typer.Option(
        None,
        "--iterations",
        help="Override the target's default iteration count.",
    ),
    output: str = typer.Option(
        "",
        "--output",
        help="Write the benchmark JSON here.",
    ),
    name: str = typer.Option(
        "",
        "--name",
        help="Optional benchmark name. Default: target name",
    ),
    fast: bool = typer.Option(
        False,
        "--fast",
        help="Use pyperf fast mode.",
    ),
    rigorous: bool = typer.Option(
        False,
        "--rigorous",
        help="Use pyperf rigorous mode.",
    ),
    track_memory: bool = typer.Option(
        False,
        "--track-memory",
        help="Benchmark peak RSS instead of elapsed time.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        help="Hide pyperf stability warnings.",
    ),
) -> None:
    """Benchmark one bounded target with pyperf command."""

    if fast and rigorous:
        raise typer.BadParameter("Choose either --fast or --rigorous, not both.")

    command: list[str] = ["pyperf", target]
    if iterations is not None:
        command.extend(["--iterations", str(iterations)])
    if output:
        command.extend(["--output", output])
    if name:
        command.extend(["--name", name])
    if fast:
        command.append("--fast")
    if rigorous:
        command.append("--rigorous")
    if track_memory:
        command.append("--track-memory")
    if quiet:
        command.append("--quiet")
    raise typer.Exit(_run_profile_script(*command))
