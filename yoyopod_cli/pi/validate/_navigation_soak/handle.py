"""Navigation soak app handle protocol and adapters."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Protocol

from yoyopod_cli.pi.support.input import InputAction, InteractionProfile
from .plan import NavigationSoakError


class _NavigationSoakAppHandle(Protocol):
    """Minimal runtime surface used by soak helpers."""

    @property
    def config_dir(self) -> str:
        """Return the config directory used for the soak app."""

    @property
    def simulate(self) -> bool:
        """Return whether the soak app is running in simulation mode."""

    @property
    def display(self) -> Any:
        """Return the active display facade."""

    @property
    def screen_manager(self) -> Any:
        """Return the active screen manager."""

    @property
    def input_manager(self) -> Any:
        """Return the active input manager."""

    @property
    def local_music_service(self) -> Any:
        """Return the local music service used by the soak."""

    @property
    def music_backend(self) -> Any:
        """Return the music backend used by the soak."""

    @property
    def runtime_loop(self) -> Any:
        """Return the runtime loop service."""

    @property
    def worker_supervisor(self) -> Any:
        """Return the managed worker supervisor."""

    @property
    def recovery_service(self) -> Any:
        """Return the recovery service."""

    @property
    def power_runtime(self) -> Any:
        """Return the power runtime facade."""

    @property
    def screen_power_service(self) -> Any:
        """Return the screen power service."""

    @property
    def scheduler(self) -> Any:
        """Return the main-thread scheduler used by the soak app."""

    @property
    def bus(self) -> Any:
        """Return the typed event bus."""

    @property
    def event_bus(self) -> Any:
        """Return the typed event bus."""

    @property
    def context(self) -> Any:
        """Return the shared runtime context."""

    def setup(self) -> bool:
        """Initialize app resources."""

    def stop(self) -> None:
        """Shut down app resources."""

    @property
    def voip_iterate_interval_seconds(self) -> float:
        """Return the configured runtime-loop VoIP iterate cadence."""

    @property
    def screen_timeout_seconds(self) -> float:
        """Return the configured inactivity timeout used for screen sleep."""

    @property
    def shutdown_completed(self) -> bool:
        """Return whether the app completed shutdown during the soak."""

    def simulate_inactivity(self, *, idle_for_seconds: float) -> None:
        """Pretend the app has been idle long enough to trigger sleep."""


@dataclass(slots=True)
class _YoyoPodAppNavigationSoakHandle:
    """Adapter that exposes a stable soak surface for ``YoyoPodApp``."""

    _app: Any

    @property
    def config_dir(self) -> str:
        return str(self._app.config_dir)

    @property
    def simulate(self) -> bool:
        return bool(self._app.simulate)

    @property
    def display(self) -> Any:
        return self._app.display

    @property
    def screen_manager(self) -> Any:
        return self._app.screen_manager

    @property
    def input_manager(self) -> Any:
        return self._app.input_manager

    @property
    def local_music_service(self) -> Any:
        return self._app.local_music_service

    @property
    def music_backend(self) -> Any:
        return self._app.music_backend

    @property
    def runtime_loop(self) -> Any:
        return self._app.runtime_loop

    @property
    def worker_supervisor(self) -> Any:
        return self._app.worker_supervisor

    @property
    def recovery_service(self) -> Any:
        return self._app.recovery_service

    @property
    def power_runtime(self) -> Any:
        return self._app.power_runtime

    @property
    def screen_power_service(self) -> Any:
        return self._app.screen_power_service

    @property
    def scheduler(self) -> Any:
        return self._app.scheduler

    @property
    def bus(self) -> Any:
        return self._app.bus

    @property
    def event_bus(self) -> Any:
        return self._app.bus

    @property
    def context(self) -> Any:
        return self._app.context

    def setup(self) -> bool:
        return bool(self._app.setup())

    def stop(self) -> None:
        self._app.stop()

    @property
    def voip_iterate_interval_seconds(self) -> float:
        runtime_loop = self.runtime_loop
        if runtime_loop is None:
            from yoyopod_cli.pi.validate._navigation_soak.plan import NavigationSoakError

            raise NavigationSoakError("runtime loop is unavailable for navigation soak")
        return float(runtime_loop.configured_voip_iterate_interval_seconds)

    @property
    def screen_timeout_seconds(self) -> float:
        return float(getattr(self._app, "_screen_timeout_seconds", 0.0))

    @property
    def shutdown_completed(self) -> bool:
        return bool(getattr(self._app, "_shutdown_completed", False))

    def simulate_inactivity(self, *, idle_for_seconds: float) -> None:
        setattr(
            self._app,
            "_last_user_activity_at",
            time.monotonic() - max(0.0, idle_for_seconds),
        )


class _NavigationSoakAppFactory(Protocol):
    """Factory for constructing a narrow app handle for soak execution."""

    def __call__(self, *, config_dir: str, simulate: bool) -> _NavigationSoakAppHandle:
        """Create a new app handle for a soak run."""


def _default_app_factory(*, config_dir: str, simulate: bool) -> _NavigationSoakAppHandle:
    """Default app factory used when callers do not provide one."""

    try:
        from yoyopod_cli.pi.support.display import Display
    except Exception as exc:
        raise NavigationSoakError(f"navigation soak display support is unavailable: {exc}") from exc

    display = Display(simulate=simulate)
    return _ValidationNavigationSoakApp(
        config_dir=config_dir,
        simulate=simulate,
        display=display,
    )


@dataclass(slots=True)
class _ValidationCard:
    mode: str


@dataclass(slots=True)
class _ValidationItem:
    key: str


@dataclass(slots=True)
class _ValidationTrack:
    name: str
    uri: str


class _ValidationScreen:
    """Small screen double that exposes the route fields used by soak validation."""

    def __init__(self, route_name: str) -> None:
        self.route_name = route_name
        self.name = route_name
        self.selected_index = 0


class _ValidationHubScreen(_ValidationScreen):
    def __init__(self) -> None:
        super().__init__("hub")
        self._cards = [
            _ValidationCard("listen"),
            _ValidationCard("talk"),
            _ValidationCard("ask"),
            _ValidationCard("setup"),
        ]

    def cards(self) -> list[_ValidationCard]:
        return list(self._cards)


class _ValidationListenScreen(_ValidationScreen):
    def __init__(self) -> None:
        super().__init__("listen")
        self.items = [
            _ValidationItem("playlists"),
            _ValidationItem("recent"),
            _ValidationItem("shuffle"),
        ]


class _ValidationPlaylistScreen(_ValidationScreen):
    def __init__(self) -> None:
        super().__init__("playlists")
        self.playlists = [SimpleNamespace(name="Validation")]


class _ValidationScreenManager:
    """Deterministic one-button navigation graph for target-side soak checks."""

    def __init__(self, music_backend: "_ValidationMusicBackend") -> None:
        self._music_backend = music_backend
        self.hub = _ValidationHubScreen()
        self.listen = _ValidationListenScreen()
        self.playlists = _ValidationPlaylistScreen()
        self.recent_tracks = _ValidationScreen("recent_tracks")
        self.now_playing = _ValidationScreen("now_playing")
        self.call = _ValidationScreen("call")
        self.ask = _ValidationScreen("ask")
        self.power = _ValidationScreen("power")
        self.current_screen: _ValidationScreen = self.hub
        self._now_playing_back_target = "listen"

    def get_current_screen(self) -> _ValidationScreen:
        return self.current_screen

    def replace_screen(self, screen_name: str) -> None:
        self.current_screen = self._screen(screen_name)

    def refresh_current_screen(self) -> None:
        return None

    def _screen(self, screen_name: str) -> _ValidationScreen:
        screen = getattr(self, screen_name, None)
        if not isinstance(screen, _ValidationScreen):
            raise NavigationSoakError(f"unknown validation screen: {screen_name}")
        return screen

    def advance(self) -> None:
        screen = self.current_screen
        if isinstance(screen, _ValidationHubScreen):
            screen.selected_index = (screen.selected_index + 1) % len(screen.cards())
            return
        if isinstance(screen, _ValidationListenScreen):
            screen.selected_index = (screen.selected_index + 1) % len(screen.items)

    def select(self) -> None:
        screen = self.current_screen
        if isinstance(screen, _ValidationHubScreen):
            mode = screen.cards()[screen.selected_index % len(screen.cards())].mode
            target = {
                "listen": "listen",
                "talk": "call",
                "ask": "ask",
                "setup": "power",
            }.get(mode)
            if target is not None:
                self.replace_screen(target)
            return

        if isinstance(screen, _ValidationListenScreen):
            key = screen.items[screen.selected_index % len(screen.items)].key
            if key == "playlists":
                self.replace_screen("playlists")
            elif key == "recent":
                self.replace_screen("recent_tracks")
            elif key == "shuffle":
                self._now_playing_back_target = "listen"
                self._music_backend.start_playback()
                self.replace_screen("now_playing")
            return

        if isinstance(screen, _ValidationPlaylistScreen):
            self._now_playing_back_target = "playlists"
            self._music_backend.start_playback()
            self.replace_screen("now_playing")

    def back(self) -> None:
        route_name = self.current_screen.route_name
        if route_name == "hub":
            return
        if route_name in {"call", "ask", "power"}:
            self.replace_screen("hub")
            return
        if route_name in {"playlists", "recent_tracks"}:
            self.replace_screen("listen")
            return
        if route_name == "now_playing":
            self.replace_screen(self._now_playing_back_target)
            return
        self.replace_screen("hub")


class _ValidationInputManager:
    """Input facade that drives the validation navigation graph."""

    interaction_profile = InteractionProfile.ONE_BUTTON.value

    def __init__(
        self,
        screen_manager: _ValidationScreenManager,
        music_backend: "_ValidationMusicBackend",
        context: SimpleNamespace,
    ) -> None:
        self._screen_manager = screen_manager
        self._music_backend = music_backend
        self._context = context

    def simulate_action(self, action: InputAction) -> None:
        self._context.screen.awake = True
        if action == InputAction.ADVANCE:
            self._screen_manager.advance()
        elif action == InputAction.SELECT:
            self._screen_manager.select()
        elif action == InputAction.BACK:
            self._screen_manager.back()
        elif action == InputAction.NEXT_TRACK:
            self._music_backend.next_track()


class _ValidationMusicBackend:
    is_connected = True

    def __init__(self) -> None:
        self._tracks = self._load_env_tracks()
        self._index: int | None = None

    @staticmethod
    def _load_env_tracks() -> list[_ValidationTrack]:
        music_dir = os.environ.get("YOYOPOD_MUSIC_DIR")
        if music_dir:
            track_paths = sorted(Path(music_dir).expanduser().rglob("*.wav"))
            if track_paths:
                return [
                    _ValidationTrack(path.stem.replace("-", " ").title(), str(path))
                    for path in track_paths
                ]

        return [
            _ValidationTrack("Validation Track A", "validation://track-a"),
            _ValidationTrack("Validation Track B", "validation://track-b"),
        ]

    def start_playback(self) -> None:
        if self._index is None:
            self._index = 0

    def next_track(self) -> None:
        self.start_playback()
        assert self._index is not None
        self._index = (self._index + 1) % len(self._tracks)

    def get_current_track(self) -> _ValidationTrack | None:
        if self._index is None:
            return None
        return self._tracks[self._index]

    def get_playback_state(self) -> str:
        return "playing" if self._index is not None else "stopped"


class _ValidationRuntimeLoop:
    configured_voip_iterate_interval_seconds = 0.05

    def __init__(self, display: Any) -> None:
        self._display = display
        self._last_iteration_at = time.monotonic()

    def run_iteration(
        self,
        *,
        monotonic_now: float,
        current_time: float,
        last_screen_update: float,
        screen_update_interval: float,
    ) -> float:
        self._last_iteration_at = monotonic_now
        self.pump_lvgl_backend(monotonic_now)
        return last_screen_update

    def timing_snapshot(self, *, now: float) -> dict[str, float | int | str | bool | None]:
        return {
            "runtime_iteration_seconds": 0.0,
            "runtime_loop_gap_seconds": max(0.0, now - self._last_iteration_at),
            "voip_schedule_delay_seconds": 0.0,
        }

    def process_pending_main_thread_actions(self) -> None:
        return None

    def pump_lvgl_backend(self, now: float) -> None:
        backend = getattr(self._display, "get_ui_backend", lambda: None)()
        pump = None if backend is None else getattr(backend, "pump", None)
        if callable(pump):
            pump(16)


class _ValidationPowerRuntime:
    def start_watchdog(self, *, now: float) -> None:
        return None

    def poll_status(self, *, now: float) -> None:
        return None

    def feed_watchdog_if_due(self, now: float) -> None:
        return None


class _ValidationBus:
    def __init__(self, context: SimpleNamespace) -> None:
        self._context = context

    def publish(self, event: object) -> None:
        self._context.screen.awake = True


class _ValidationNavigationSoakApp:
    """CLI-owned default app used by ``pi validate navigation`` after Python runtime removal."""

    def __init__(self, *, config_dir: str, simulate: bool, display: Any) -> None:
        self._config_dir = config_dir
        self._simulate = simulate
        self._display = display
        self._context = SimpleNamespace(screen=SimpleNamespace(awake=True))
        self._music_backend = _ValidationMusicBackend()
        self._screen_manager = _ValidationScreenManager(self._music_backend)
        self._input_manager = _ValidationInputManager(
            self._screen_manager,
            self._music_backend,
            self._context,
        )
        self._runtime_loop = _ValidationRuntimeLoop(display)
        self._power_runtime = _ValidationPowerRuntime()
        self._bus = _ValidationBus(self._context)
        self._stopped = False

    @property
    def config_dir(self) -> str:
        return self._config_dir

    @property
    def simulate(self) -> bool:
        return self._simulate

    @property
    def display(self) -> Any:
        return self._display

    @property
    def screen_manager(self) -> Any:
        return self._screen_manager

    @property
    def input_manager(self) -> Any:
        return self._input_manager

    @property
    def local_music_service(self) -> Any:
        return SimpleNamespace(validation=True)

    @property
    def music_backend(self) -> Any:
        return self._music_backend

    @property
    def runtime_loop(self) -> Any:
        return self._runtime_loop

    @property
    def worker_supervisor(self) -> Any:
        return SimpleNamespace(poll=lambda: None)

    @property
    def recovery_service(self) -> Any:
        return SimpleNamespace(attempt_manager_recovery=lambda: None)

    @property
    def power_runtime(self) -> Any:
        return self._power_runtime

    @property
    def screen_power_service(self) -> Any:
        return SimpleNamespace(update_screen_power=lambda now: None)

    @property
    def scheduler(self) -> Any:
        return SimpleNamespace(run_on_main=lambda callback: callback())

    @property
    def bus(self) -> Any:
        return self._bus

    @property
    def event_bus(self) -> Any:
        return self._bus

    @property
    def context(self) -> Any:
        return self._context

    def setup(self) -> bool:
        backend = getattr(self._display, "get_ui_backend", lambda: None)()
        initialize = None if backend is None else getattr(backend, "initialize", None)
        if callable(initialize) and not initialize():
            return False
        return True

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        cleanup = getattr(self._display, "cleanup", None)
        if callable(cleanup):
            cleanup()

    @property
    def voip_iterate_interval_seconds(self) -> float:
        return float(self._runtime_loop.configured_voip_iterate_interval_seconds)

    @property
    def screen_timeout_seconds(self) -> float:
        return 1.0

    @property
    def shutdown_completed(self) -> bool:
        return False

    def simulate_inactivity(self, *, idle_for_seconds: float) -> None:
        self._context.screen.awake = False
