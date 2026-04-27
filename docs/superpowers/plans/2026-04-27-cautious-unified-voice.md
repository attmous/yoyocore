# Cautious Unified Voice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one coherent YoYo voice surface that strips optional `yoyo` / `hey yoyo` prefixes, routes confident local commands first, and falls back to Ask for non-command speech.

**Architecture:** Keep screen code presentation-only. Add focused voice integration units for activation normalization, mutable command dictionary loading, routing decisions, and future wake detection. `VoiceRuntimeCoordinator` owns command-first/Ask-fallback routing, while `VoiceCommandExecutor` owns allowlisted side effects.

**Tech Stack:** Python 3.12, dataclasses, PyYAML through existing config helpers, pytest, existing OpenAI STT seam, existing LVGL Ask screen.

---

## File Structure

Create:

- `yoyopod/integrations/voice/activation.py` - strips optional YoYo activation prefixes from transcripts.
- `yoyopod/integrations/voice/dictionary.py` - loads built-in command grammar plus mutable `data/voice/commands.yaml` overrides and safe actions.
- `yoyopod/integrations/voice/router.py` - command-first routing decision layer.
- `yoyopod/integrations/voice/wake.py` - future wake detector interface and no-op implementation.
- `tests/integrations/test_voice_activation.py`
- `tests/integrations/test_voice_dictionary.py`
- `tests/integrations/test_voice_router.py`
- `tests/integrations/test_voice_wake.py`

Modify:

- `config/voice/assistant.yaml` - add default activation/routing/dictionary settings.
- `config/people/contacts.seed.yaml` - add initial `aliases` field for Mama.
- `yoyopod/config/models/voice.py` - typed config fields for activation prefixes, command routing, and dictionary path.
- `yoyopod/integrations/voice/models.py` - runtime `VoiceSettings` fields for the same policy.
- `yoyopod/integrations/voice/settings.py` - resolve config into `VoiceSettings`.
- `yoyopod/integrations/voice/commands.py` - allow matching against an injected grammar tuple.
- `yoyopod/integrations/voice/executor.py` - accept router matches and execute allowlisted route actions.
- `yoyopod/integrations/voice/runtime.py` - use router for command-first/Ask-fallback flow.
- `yoyopod/integrations/voice/__init__.py` - export new voice integration types.
- `yoyopod/integrations/contacts/models.py` - add contact aliases to people data.
- `yoyopod/integrations/contacts/directory.py` - support alias-aware lookup helpers.
- `yoyopod/ui/screens/navigation/ask/__init__.py` - update YoYo-facing copy, keep parsing out of screen.
- `yoyopod/ui/screens/router.py` - add safe route names emitted by voice outcomes.
- `tests/config/test_config_voice_device_persistence.py` - cover new config defaults without persistence regressions.
- `tests/integrations/test_voice_runtime.py` - cover command-first and Ask-fallback runtime behavior.
- `tests/integrations/test_voice_service.py` - cover injected grammar matching.
- `tests/ui/test_screen_routing.py` - cover safe voice route names and Ask screen copy/state behavior.
- `docs/VOICE_COMMAND_PLAN.md` or a new note in `docs/README.md` - mark the new spec as the current design reference.

Do not modify raw LVGL binding files for this feature. Raw LVGL remains confined to `yoyopod/ui/lvgl_binding/` and existing LVGL view modules.

Before every commit in this plan, including task commits, run both required project gates:

```bash
uv run python scripts/quality.py gate
uv run pytest -q
```

---

### Task 1: Activation Prefix Normalizer

**Files:**
- Create: `yoyopod/integrations/voice/activation.py`
- Modify: `yoyopod/integrations/voice/__init__.py`
- Test: `tests/integrations/test_voice_activation.py`

- [ ] **Step 1: Write failing activation tests**

Create `tests/integrations/test_voice_activation.py`:

```python
"""Tests for YoYo voice activation prefix normalization."""

from __future__ import annotations

import pytest

from yoyopod.integrations.voice.activation import (
    VoiceActivationNormalizer,
    normalize_voice_activation,
)


@pytest.mark.parametrize(
    ("transcript", "expected_text", "expected_prefix"),
    [
        ("hey yoyo call mama", "call mama", "hey yoyo"),
        ("yoyo make it louder", "make it louder", "yoyo"),
        ("Hey, YoYo, why is the sky blue?", "why is the sky blue", "hey yoyo"),
        ("yo yo play music", "play music", "yoyo"),
        ("hey yoyo hey yoyo call mom", "call mom", "hey yoyo"),
        ("please call mom", "please call mom", ""),
    ],
)
def test_normalize_voice_activation_strips_configured_prefixes(
    transcript: str,
    expected_text: str,
    expected_prefix: str,
) -> None:
    result = normalize_voice_activation(transcript, prefixes=("hey yoyo", "yoyo"))

    assert result.original_text == transcript
    assert result.normalized_text == expected_text
    assert result.stripped_prefix == expected_prefix


def test_activation_normalizer_uses_settings_prefix_order() -> None:
    normalizer = VoiceActivationNormalizer(prefixes=("hey yoyo", "yoyo", "computer"))

    result = normalizer.normalize("computer open talk")

    assert result.normalized_text == "open talk"
    assert result.stripped_prefix == "computer"


def test_activation_normalizer_preserves_empty_and_whitespace_text() -> None:
    result = normalize_voice_activation("   ", prefixes=("hey yoyo", "yoyo"))

    assert result.normalized_text == ""
    assert result.stripped_prefix == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest -q tests/integrations/test_voice_activation.py
```

Expected: import failure for `yoyopod.integrations.voice.activation`.

- [ ] **Step 3: Implement activation normalizer**

Create `yoyopod/integrations/voice/activation.py`:

```python
"""Normalize optional YoYo activation phrases from voice transcripts."""

from __future__ import annotations

from dataclasses import dataclass
import re

_TOKEN_RE = re.compile(r"[a-z0-9']+")


@dataclass(slots=True, frozen=True)
class VoiceActivationResult:
    """Normalized voice transcript plus any stripped activation prefix."""

    original_text: str
    normalized_text: str
    stripped_prefix: str = ""


class VoiceActivationNormalizer:
    """Strip optional wake-style prefixes after button-gated activation."""

    def __init__(self, *, prefixes: tuple[str, ...]) -> None:
        self._prefixes = tuple(
            normalized for prefix in prefixes if (normalized := _normalize_phrase(prefix))
        )
        self._prefix_tokens = tuple(
            (prefix, _tokenize(prefix)) for prefix in self._prefixes if _tokenize(prefix)
        )

    def normalize(self, transcript: str) -> VoiceActivationResult:
        """Return transcript text with repeated configured activation prefixes stripped."""

        original = transcript
        tokens = list(_tokenize(transcript))
        stripped_prefix = ""
        while tokens:
            matched = False
            for prefix, prefix_tokens in self._prefix_tokens:
                if _tokens_start_with(tokens, prefix_tokens):
                    stripped_prefix = stripped_prefix or prefix
                    tokens = tokens[len(prefix_tokens) :]
                    matched = True
                    break
            if not matched:
                break
        return VoiceActivationResult(
            original_text=original,
            normalized_text=" ".join(tokens),
            stripped_prefix=stripped_prefix,
        )


def normalize_voice_activation(
    transcript: str,
    *,
    prefixes: tuple[str, ...],
) -> VoiceActivationResult:
    """Convenience wrapper for one-off activation normalization."""

    return VoiceActivationNormalizer(prefixes=prefixes).normalize(transcript)


def _normalize_phrase(value: str) -> str:
    return " ".join(_tokenize(value))


def _tokenize(text: str) -> tuple[str, ...]:
    tokens = list(_TOKEN_RE.findall(text.lower()))
    normalized: list[str] = []
    index = 0
    while index < len(tokens):
        if index + 1 < len(tokens) and tokens[index] == "yo" and tokens[index + 1] == "yo":
            normalized.append("yoyo")
            index += 2
            continue
        normalized.append(tokens[index])
        index += 1
    return tuple(normalized)


def _tokens_start_with(tokens: list[str], prefix_tokens: tuple[str, ...]) -> bool:
    return len(tokens) >= len(prefix_tokens) and tuple(tokens[: len(prefix_tokens)]) == prefix_tokens


__all__ = [
    "VoiceActivationNormalizer",
    "VoiceActivationResult",
    "normalize_voice_activation",
]
```

Modify `yoyopod/integrations/voice/__init__.py`:

```python
if TYPE_CHECKING:
    from yoyopod.integrations.voice.activation import (
        VoiceActivationNormalizer,
        VoiceActivationResult,
        normalize_voice_activation,
    )
```

Add entries to `_PUBLIC_EXPORTS`:

```python
    "VoiceActivationNormalizer": (
        "yoyopod.integrations.voice.activation",
        "VoiceActivationNormalizer",
    ),
    "VoiceActivationResult": (
        "yoyopod.integrations.voice.activation",
        "VoiceActivationResult",
    ),
    "normalize_voice_activation": (
        "yoyopod.integrations.voice.activation",
        "normalize_voice_activation",
    ),
```

Add entries to `__all__`:

```python
    "VoiceActivationNormalizer",
    "VoiceActivationResult",
    "normalize_voice_activation",
```

- [ ] **Step 4: Run activation tests**

Run:

```bash
uv run pytest -q tests/integrations/test_voice_activation.py
```

Expected: all tests pass.

- [ ] **Step 5: Commit activation normalizer**

Run:

```bash
uv run python scripts/quality.py gate
uv run pytest -q
git add yoyopod/integrations/voice/activation.py yoyopod/integrations/voice/__init__.py tests/integrations/test_voice_activation.py
git commit -m "feat: add YoYo voice activation normalizer"
```

---

### Task 2: Mutable Command Dictionary And Injected Grammar

**Files:**
- Create: `yoyopod/integrations/voice/dictionary.py`
- Modify: `yoyopod/integrations/voice/commands.py`
- Modify: `yoyopod/integrations/voice/__init__.py`
- Test: `tests/integrations/test_voice_dictionary.py`
- Test: `tests/integrations/test_voice_service.py`

- [ ] **Step 1: Write failing dictionary tests**

Create `tests/integrations/test_voice_dictionary.py`:

```python
"""Tests for mutable voice command dictionary loading."""

from __future__ import annotations

from pathlib import Path

import yaml

from yoyopod.integrations.voice.commands import VoiceCommandIntent, match_voice_command
from yoyopod.integrations.voice.dictionary import (
    SAFE_VOICE_ROUTE_ACTIONS,
    VoiceCommandDictionary,
    load_voice_command_dictionary,
)


def test_dictionary_defaults_include_builtin_voice_commands() -> None:
    dictionary = VoiceCommandDictionary.from_builtins()

    grammar = dictionary.to_grammar()

    assert match_voice_command("call mom", grammar=grammar).intent is VoiceCommandIntent.CALL_CONTACT
    assert match_voice_command("play music", grammar=grammar).intent is VoiceCommandIntent.PLAY_MUSIC


def test_dictionary_adds_aliases_from_mutable_yaml(tmp_path: Path) -> None:
    commands_file = tmp_path / "commands.yaml"
    commands_file.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "intents": {
                    "volume_up": {
                        "aliases": ["boost sound"],
                        "examples": ["boost sound"],
                    }
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    dictionary = load_voice_command_dictionary(commands_file)

    assert (
        match_voice_command("boost sound", grammar=dictionary.to_grammar()).intent
        is VoiceCommandIntent.VOLUME_UP
    )


def test_dictionary_can_disable_mutable_intent(tmp_path: Path) -> None:
    commands_file = tmp_path / "commands.yaml"
    commands_file.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "intents": {
                    "play_music": {
                        "enabled": False,
                    }
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    dictionary = load_voice_command_dictionary(commands_file)

    assert (
        match_voice_command("play music", grammar=dictionary.to_grammar()).intent
        is VoiceCommandIntent.UNKNOWN
    )


def test_dictionary_rejects_unsafe_actions(tmp_path: Path) -> None:
    commands_file = tmp_path / "commands.yaml"
    commands_file.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "actions": {
                    "open_talk": {
                        "aliases": ["open talk"],
                        "route": "open_talk",
                    },
                    "shell": {
                        "aliases": ["run update"],
                        "route": "powershell",
                    },
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    dictionary = load_voice_command_dictionary(commands_file)

    assert dictionary.actions["open_talk"].route == "open_talk"
    assert "shell" not in dictionary.actions
    assert "open_talk" in SAFE_VOICE_ROUTE_ACTIONS


def test_dictionary_invalid_yaml_uses_builtins(tmp_path: Path) -> None:
    commands_file = tmp_path / "commands.yaml"
    commands_file.write_text("intents: [", encoding="utf-8")

    dictionary = load_voice_command_dictionary(commands_file)

    assert (
        match_voice_command("volume up", grammar=dictionary.to_grammar()).intent
        is VoiceCommandIntent.VOLUME_UP
    )
```

In `tests/integrations/test_voice_service.py`, add this test:

```python
def test_match_voice_command_accepts_injected_grammar() -> None:
    """Callers should be able to match against dictionary-derived grammar."""

    from yoyopod.integrations.voice.commands import VoiceCommandTemplate

    grammar = (
        VoiceCommandTemplate(
            intent=VoiceCommandIntent.VOLUME_UP,
            trigger_phrases=("boost sound",),
            examples=("boost sound",),
            fuzzy_threshold=0.9,
        ),
    )

    assert match_voice_command("boost sound", grammar=grammar).intent is VoiceCommandIntent.VOLUME_UP
    assert match_voice_command("volume up", grammar=grammar).intent is VoiceCommandIntent.UNKNOWN
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest -q tests/integrations/test_voice_dictionary.py tests/integrations/test_voice_service.py::test_match_voice_command_accepts_injected_grammar
```

Expected: import failure for `dictionary.py` and signature failure for `match_voice_command(..., grammar=...)`.

- [ ] **Step 3: Add optional grammar parameter**

Modify `yoyopod/integrations/voice/commands.py`.

Change the signature:

```python
def match_voice_command(
    transcript: str,
    *,
    grammar: tuple[VoiceCommandTemplate, ...] | None = None,
) -> VoiceCommandMatch:
```

At the top of the function body, set the effective grammar:

```python
    effective_grammar = VOICE_COMMAND_GRAMMAR if grammar is None else grammar
```

Change calls to `_match_slot_command` and `_match_fixed_command`:

```python
    slot_match = _match_slot_command(tokens, transcript, grammar=effective_grammar)
    fixed_match = _match_fixed_command(tokens, transcript, grammar=effective_grammar)
```

Change helper signatures:

```python
def _match_slot_command(
    tokens: tuple[str, ...],
    transcript: str,
    *,
    grammar: tuple[VoiceCommandTemplate, ...],
) -> VoiceCommandMatch | None:
```

```python
def _match_fixed_command(
    tokens: tuple[str, ...],
    transcript: str,
    *,
    grammar: tuple[VoiceCommandTemplate, ...],
) -> VoiceCommandMatch | None:
```

Inside both helpers, replace:

```python
    for template in VOICE_COMMAND_GRAMMAR:
```

with:

```python
    for template in grammar:
```

- [ ] **Step 4: Implement dictionary loader**

Create `yoyopod/integrations/voice/dictionary.py`:

```python
"""Mutable voice command dictionary layered over built-in grammar."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

from yoyopod.integrations.voice.commands import (
    VOICE_COMMAND_GRAMMAR,
    VoiceCommandIntent,
    VoiceCommandTemplate,
)

SAFE_VOICE_ROUTE_ACTIONS = frozenset(
    {
        "open_talk",
        "open_listen",
        "open_setup",
        "go_home",
        "back",
    }
)


@dataclass(slots=True, frozen=True)
class VoiceCommandAction:
    """One safe dictionary-defined route action."""

    name: str
    aliases: tuple[str, ...]
    route: str


@dataclass(slots=True, frozen=True)
class VoiceCommandDictionary:
    """Merged command grammar and safe route actions."""

    grammar: tuple[VoiceCommandTemplate, ...]
    actions: dict[str, VoiceCommandAction]

    @classmethod
    def from_builtins(cls) -> "VoiceCommandDictionary":
        """Return dictionary data backed only by built-in command grammar."""

        return cls(grammar=VOICE_COMMAND_GRAMMAR, actions={})

    def to_grammar(self) -> tuple[VoiceCommandTemplate, ...]:
        """Return grammar templates used by deterministic command matching."""

        action_templates = tuple(
            VoiceCommandTemplate(
                intent=VoiceCommandIntent.UNKNOWN,
                trigger_phrases=action.aliases,
                examples=action.aliases,
                fuzzy_threshold=0.9,
                exact_trigger_phrases=action.aliases,
            )
            for action in self.actions.values()
        )
        return self.grammar + action_templates


def load_voice_command_dictionary(path: str | Path | None) -> VoiceCommandDictionary:
    """Load mutable command dictionary data, falling back to built-in grammar."""

    dictionary = VoiceCommandDictionary.from_builtins()
    if path is None:
        return dictionary
    commands_path = Path(path)
    if not commands_path.exists():
        return dictionary
    try:
        with commands_path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
    except Exception as exc:
        logger.warning("Voice command dictionary could not be loaded from {}: {}", path, exc)
        return dictionary
    if not isinstance(payload, dict):
        logger.warning("Voice command dictionary ignored because root is not a mapping: {}", path)
        return dictionary
    return _merge_dictionary_payload(dictionary, payload)


def _merge_dictionary_payload(
    dictionary: VoiceCommandDictionary,
    payload: dict[str, Any],
) -> VoiceCommandDictionary:
    grammar = _merge_intent_payload(dictionary.grammar, payload.get("intents"))
    actions = _load_actions(payload.get("actions"))
    return VoiceCommandDictionary(grammar=grammar, actions=actions)


def _merge_intent_payload(
    grammar: tuple[VoiceCommandTemplate, ...],
    payload: object,
) -> tuple[VoiceCommandTemplate, ...]:
    if not isinstance(payload, dict):
        return grammar
    by_intent = {template.intent.value: template for template in grammar}
    disabled: set[str] = set()
    for intent_name, raw_config in payload.items():
        if not isinstance(intent_name, str) or not isinstance(raw_config, dict):
            continue
        template = by_intent.get(intent_name)
        if template is None:
            logger.warning("Ignoring unknown voice command intent {}", intent_name)
            continue
        if raw_config.get("enabled") is False:
            disabled.add(intent_name)
            continue
        aliases = _string_tuple(raw_config.get("aliases"))
        examples = _string_tuple(raw_config.get("examples"))
        threshold = raw_config.get("fuzzy_threshold", template.fuzzy_threshold)
        by_intent[intent_name] = replace(
            template,
            trigger_phrases=_dedupe(template.trigger_phrases + aliases),
            examples=_dedupe(template.examples + examples),
            fuzzy_threshold=float(threshold),
        )
    return tuple(
        template
        for template in by_intent.values()
        if template.intent.value not in disabled
    )


def _load_actions(payload: object) -> dict[str, VoiceCommandAction]:
    if not isinstance(payload, dict):
        return {}
    actions: dict[str, VoiceCommandAction] = {}
    for name, raw_config in payload.items():
        if not isinstance(name, str) or not isinstance(raw_config, dict):
            continue
        route = str(raw_config.get("route", "")).strip()
        if route not in SAFE_VOICE_ROUTE_ACTIONS:
            logger.warning("Ignoring unsafe voice route action {} -> {}", name, route)
            continue
        aliases = _string_tuple(raw_config.get("aliases"))
        if not aliases:
            logger.warning("Ignoring voice route action {} without aliases", name)
            continue
        actions[name] = VoiceCommandAction(name=name, aliases=aliases, route=route)
    return actions


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value.strip()))


__all__ = [
    "SAFE_VOICE_ROUTE_ACTIONS",
    "VoiceCommandAction",
    "VoiceCommandDictionary",
    "load_voice_command_dictionary",
]
```

- [ ] **Step 5: Export dictionary types**

Modify `yoyopod/integrations/voice/__init__.py`.

Add `TYPE_CHECKING` imports:

```python
    from yoyopod.integrations.voice.dictionary import (
        SAFE_VOICE_ROUTE_ACTIONS,
        VoiceCommandAction,
        VoiceCommandDictionary,
        load_voice_command_dictionary,
    )
```

Add `_PUBLIC_EXPORTS` entries:

```python
    "SAFE_VOICE_ROUTE_ACTIONS": (
        "yoyopod.integrations.voice.dictionary",
        "SAFE_VOICE_ROUTE_ACTIONS",
    ),
    "VoiceCommandAction": (
        "yoyopod.integrations.voice.dictionary",
        "VoiceCommandAction",
    ),
    "VoiceCommandDictionary": (
        "yoyopod.integrations.voice.dictionary",
        "VoiceCommandDictionary",
    ),
    "load_voice_command_dictionary": (
        "yoyopod.integrations.voice.dictionary",
        "load_voice_command_dictionary",
    ),
```

Add `__all__` entries:

```python
    "SAFE_VOICE_ROUTE_ACTIONS",
    "VoiceCommandAction",
    "VoiceCommandDictionary",
    "load_voice_command_dictionary",
```

- [ ] **Step 6: Run dictionary tests**

Run:

```bash
uv run pytest -q tests/integrations/test_voice_dictionary.py tests/integrations/test_voice_service.py::test_match_voice_command_accepts_injected_grammar
```

Expected: all tests pass.

- [ ] **Step 7: Commit dictionary work**

Run:

```bash
uv run python scripts/quality.py gate
uv run pytest -q
git add yoyopod/integrations/voice/commands.py yoyopod/integrations/voice/dictionary.py yoyopod/integrations/voice/__init__.py tests/integrations/test_voice_dictionary.py tests/integrations/test_voice_service.py
git commit -m "feat: load mutable voice command dictionary"
```

---

### Task 3: Voice Config And Runtime Settings

**Files:**
- Modify: `config/voice/assistant.yaml`
- Modify: `yoyopod/config/models/voice.py`
- Modify: `yoyopod/integrations/voice/models.py`
- Modify: `yoyopod/integrations/voice/settings.py`
- Test: `tests/config/test_config_voice_device_persistence.py`
- Test: `tests/integrations/test_voice_runtime.py`

- [ ] **Step 1: Write failing config tests**

Add to `tests/config/test_config_voice_device_persistence.py`:

```python
def test_voice_config_loads_activation_and_dictionary_defaults(tmp_path: Path) -> None:
    cfg_dir = tmp_path / "config"
    voice_dir = cfg_dir / "voice"
    voice_dir.mkdir(parents=True)
    (voice_dir / "assistant.yaml").write_text(
        yaml.safe_dump(
            {
                "assistant": {
                    "activation_prefixes": ["yoyo", "hey yoyo"],
                    "command_dictionary_path": "data/voice/commands.yaml",
                    "command_routing": {
                        "mode": "command_first",
                        "ask_fallback_enabled": True,
                        "fallback_min_command_confidence": 0.83,
                    },
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    manager = ConfigManager(config_dir=str(cfg_dir))
    settings = manager.get_voice_settings().assistant

    assert settings.activation_prefixes == ["yoyo", "hey yoyo"]
    assert settings.command_dictionary_path == "data/voice/commands.yaml"
    assert settings.command_routing.mode == "command_first"
    assert settings.command_routing.ask_fallback_enabled is True
    assert settings.command_routing.fallback_min_command_confidence == 0.83
```

Add to `tests/integrations/test_voice_runtime.py`:

```python
def test_voice_settings_resolver_includes_command_routing_config() -> None:
    config_manager = _FakeConfigManager([])
    voice_cfg = config_manager.get_voice_settings()
    voice_cfg.assistant.activation_prefixes = ["yoyo", "hey yoyo"]
    voice_cfg.assistant.command_dictionary_path = "data/voice/commands.yaml"
    voice_cfg.assistant.command_routing = SimpleNamespace(
        mode="command_first",
        ask_fallback_enabled=False,
        fallback_min_command_confidence=0.91,
    )

    settings = VoiceSettingsResolver(
        context=None,
        config_manager=config_manager,
    ).defaults()

    assert settings.activation_prefixes == ("yoyo", "hey yoyo")
    assert settings.command_dictionary_path == "data/voice/commands.yaml"
    assert settings.command_routing_mode == "command_first"
    assert settings.ask_fallback_enabled is False
    assert settings.fallback_min_command_confidence == 0.91
```

Update `_FakeConfigManager` in `tests/integrations/test_voice_runtime.py` so its `assistant` namespace contains the new defaults:

```python
                activation_prefixes=["yoyo", "hey yoyo"],
                command_dictionary_path="data/voice/commands.yaml",
                command_routing=SimpleNamespace(
                    mode="command_first",
                    ask_fallback_enabled=True,
                    fallback_min_command_confidence=0.82,
                ),
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest -q tests/config/test_config_voice_device_persistence.py::test_voice_config_loads_activation_and_dictionary_defaults tests/integrations/test_voice_runtime.py::test_voice_settings_resolver_includes_command_routing_config
```

Expected: missing config fields on `VoiceAssistantConfig` and `VoiceSettings`.

- [ ] **Step 3: Add typed config models**

Modify `yoyopod/config/models/voice.py`.

Add below `DEFAULT_CLOUD_TTS_INSTRUCTIONS`:

```python
@dataclass(slots=True)
class VoiceCommandRoutingConfig:
    """Command-first routing policy for YoYo voice interactions."""

    mode: str = config_value(default="command_first", env="YOYOPOD_VOICE_ROUTING_MODE")
    ask_fallback_enabled: bool = config_value(
        default=True,
        env="YOYOPOD_VOICE_ASK_FALLBACK_ENABLED",
    )
    fallback_min_command_confidence: float = config_value(
        default=0.82,
        env="YOYOPOD_VOICE_COMMAND_CONFIDENCE",
    )
```

Add fields to `VoiceAssistantConfig`:

```python
    activation_prefixes: list[str] = config_value(
        default_factory=lambda: ["yoyo", "hey yoyo"],
        env="YOYOPOD_VOICE_ACTIVATION_PREFIXES",
    )
    command_dictionary_path: str = config_value(
        default="data/voice/commands.yaml",
        env="YOYOPOD_VOICE_COMMAND_DICTIONARY",
    )
    command_routing: VoiceCommandRoutingConfig = config_value(
        default_factory=VoiceCommandRoutingConfig
    )
```

Modify `yoyopod/config/models/__init__.py` if it explicitly exports voice config classes. Add `VoiceCommandRoutingConfig` beside the existing voice exports.

- [ ] **Step 4: Add runtime settings fields**

Modify `yoyopod/integrations/voice/models.py`.

Add fields to `VoiceSettings`:

```python
    activation_prefixes: tuple[str, ...] = ("yoyo", "hey yoyo")
    command_dictionary_path: str = "data/voice/commands.yaml"
    command_routing_mode: str = "command_first"
    ask_fallback_enabled: bool = True
    fallback_min_command_confidence: float = 0.82
```

- [ ] **Step 5: Resolve config into runtime settings**

Modify `VoiceSettingsResolver.defaults()` in `yoyopod/integrations/voice/settings.py`.

Before returning `VoiceSettings(...)`, compute:

```python
        routing_cfg = getattr(assistant_cfg, "command_routing", None)
        activation_prefixes = tuple(
            str(prefix).strip()
            for prefix in getattr(
                assistant_cfg,
                "activation_prefixes",
                defaults.activation_prefixes,
            )
            if str(prefix).strip()
        )
```

Add fields to the returned `VoiceSettings`:

```python
            activation_prefixes=activation_prefixes or defaults.activation_prefixes,
            command_dictionary_path=getattr(
                assistant_cfg,
                "command_dictionary_path",
                defaults.command_dictionary_path,
            ),
            command_routing_mode=getattr(
                routing_cfg,
                "mode",
                defaults.command_routing_mode,
            ),
            ask_fallback_enabled=getattr(
                routing_cfg,
                "ask_fallback_enabled",
                defaults.ask_fallback_enabled,
            ),
            fallback_min_command_confidence=getattr(
                routing_cfg,
                "fallback_min_command_confidence",
                defaults.fallback_min_command_confidence,
            ),
```

- [ ] **Step 6: Update default YAML**

Modify `config/voice/assistant.yaml` under `assistant:`:

```yaml
  activation_prefixes:
    - "yoyo"
    - "hey yoyo"
  command_dictionary_path: "data/voice/commands.yaml"
  command_routing:
    mode: "command_first"
    ask_fallback_enabled: true
    fallback_min_command_confidence: 0.82
```

- [ ] **Step 7: Run config tests**

Run:

```bash
uv run pytest -q tests/config/test_config_voice_device_persistence.py::test_voice_config_loads_activation_and_dictionary_defaults tests/integrations/test_voice_runtime.py::test_voice_settings_resolver_includes_command_routing_config
```

Expected: both tests pass.

- [ ] **Step 8: Commit config settings**

Run:

```bash
uv run python scripts/quality.py gate
uv run pytest -q
git add config/voice/assistant.yaml yoyopod/config/models/voice.py yoyopod/config/models/__init__.py yoyopod/integrations/voice/models.py yoyopod/integrations/voice/settings.py tests/config/test_config_voice_device_persistence.py tests/integrations/test_voice_runtime.py
git commit -m "feat: configure unified voice routing policy"
```

---

### Task 4: Command-First Router

**Files:**
- Create: `yoyopod/integrations/voice/router.py`
- Modify: `yoyopod/integrations/voice/__init__.py`
- Test: `tests/integrations/test_voice_router.py`

- [ ] **Step 1: Write failing router tests**

Create `tests/integrations/test_voice_router.py`:

```python
"""Tests for command-first YoYo voice routing."""

from __future__ import annotations

from yoyopod.integrations.voice.dictionary import VoiceCommandDictionary
from yoyopod.integrations.voice.router import (
    VoiceRouteKind,
    VoiceRouter,
)


def test_router_strips_activation_prefix_and_routes_command() -> None:
    router = VoiceRouter(
        dictionary=VoiceCommandDictionary.from_builtins(),
        activation_prefixes=("hey yoyo", "yoyo"),
        ask_fallback_enabled=True,
    )

    decision = router.route("hey yoyo call mama")

    assert decision.kind is VoiceRouteKind.COMMAND
    assert decision.normalized_text == "call mama"
    assert decision.command is not None
    assert decision.command.contact_name == "mama"
    assert decision.reason == "command_match"


def test_router_falls_back_to_ask_for_non_command() -> None:
    router = VoiceRouter(
        dictionary=VoiceCommandDictionary.from_builtins(),
        activation_prefixes=("hey yoyo", "yoyo"),
        ask_fallback_enabled=True,
    )

    decision = router.route("yoyo why is the sky blue")

    assert decision.kind is VoiceRouteKind.ASK_FALLBACK
    assert decision.normalized_text == "why is the sky blue"
    assert decision.command is None
    assert decision.reason == "ask_fallback"


def test_router_returns_local_help_when_fallback_disabled() -> None:
    router = VoiceRouter(
        dictionary=VoiceCommandDictionary.from_builtins(),
        activation_prefixes=("hey yoyo", "yoyo"),
        ask_fallback_enabled=False,
    )

    decision = router.route("tell me a story")

    assert decision.kind is VoiceRouteKind.LOCAL_HELP
    assert decision.normalized_text == "tell me a story"
    assert decision.reason == "no_command_no_fallback"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest -q tests/integrations/test_voice_router.py
```

Expected: import failure for `router.py`.

- [ ] **Step 3: Implement router**

Create `yoyopod/integrations/voice/router.py`:

```python
"""Command-first routing for unified YoYo voice interactions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from yoyopod.integrations.voice.activation import VoiceActivationNormalizer
from yoyopod.integrations.voice.commands import VoiceCommandMatch, match_voice_command
from yoyopod.integrations.voice.dictionary import VoiceCommandDictionary


class VoiceRouteKind(StrEnum):
    """Possible post-transcription voice routing decisions."""

    COMMAND = "command"
    ASK_FALLBACK = "ask_fallback"
    LOCAL_HELP = "local_help"


@dataclass(slots=True, frozen=True)
class VoiceRouteDecision:
    """Decision returned after normalizing and routing one transcript."""

    kind: VoiceRouteKind
    original_text: str
    normalized_text: str
    stripped_prefix: str
    command: VoiceCommandMatch | None = None
    confidence: float = 0.0
    reason: str = ""


class VoiceRouter:
    """Route one transcribed phrase to command execution or Ask fallback."""

    def __init__(
        self,
        *,
        dictionary: VoiceCommandDictionary,
        activation_prefixes: tuple[str, ...],
        ask_fallback_enabled: bool,
    ) -> None:
        self._dictionary = dictionary
        self._normalizer = VoiceActivationNormalizer(prefixes=activation_prefixes)
        self._ask_fallback_enabled = ask_fallback_enabled

    def route(self, transcript: str) -> VoiceRouteDecision:
        """Return a command-first routing decision for one transcript."""

        activation = self._normalizer.normalize(transcript)
        command = match_voice_command(
            activation.normalized_text,
            grammar=self._dictionary.to_grammar(),
        )
        if command.is_command:
            return VoiceRouteDecision(
                kind=VoiceRouteKind.COMMAND,
                original_text=transcript,
                normalized_text=activation.normalized_text,
                stripped_prefix=activation.stripped_prefix,
                command=command,
                confidence=1.0,
                reason="command_match",
            )
        if self._ask_fallback_enabled and activation.normalized_text:
            return VoiceRouteDecision(
                kind=VoiceRouteKind.ASK_FALLBACK,
                original_text=transcript,
                normalized_text=activation.normalized_text,
                stripped_prefix=activation.stripped_prefix,
                reason="ask_fallback",
            )
        return VoiceRouteDecision(
            kind=VoiceRouteKind.LOCAL_HELP,
            original_text=transcript,
            normalized_text=activation.normalized_text,
            stripped_prefix=activation.stripped_prefix,
            reason="no_command_no_fallback",
        )


__all__ = [
    "VoiceRouteDecision",
    "VoiceRouteKind",
    "VoiceRouter",
]
```

- [ ] **Step 4: Export router types**

Modify `yoyopod/integrations/voice/__init__.py`.

Add `TYPE_CHECKING` imports:

```python
    from yoyopod.integrations.voice.router import (
        VoiceRouteDecision,
        VoiceRouteKind,
        VoiceRouter,
    )
```

Add `_PUBLIC_EXPORTS` entries:

```python
    "VoiceRouteDecision": ("yoyopod.integrations.voice.router", "VoiceRouteDecision"),
    "VoiceRouteKind": ("yoyopod.integrations.voice.router", "VoiceRouteKind"),
    "VoiceRouter": ("yoyopod.integrations.voice.router", "VoiceRouter"),
```

Add `__all__` entries:

```python
    "VoiceRouteDecision",
    "VoiceRouteKind",
    "VoiceRouter",
```

- [ ] **Step 5: Run router tests**

Run:

```bash
uv run pytest -q tests/integrations/test_voice_router.py
```

Expected: all tests pass.

- [ ] **Step 6: Commit router**

Run:

```bash
uv run python scripts/quality.py gate
uv run pytest -q
git add yoyopod/integrations/voice/router.py yoyopod/integrations/voice/__init__.py tests/integrations/test_voice_router.py
git commit -m "feat: add command-first voice router"
```

---

### Task 5: Contact Aliases And Safe Route Actions

**Files:**
- Modify: `yoyopod/integrations/contacts/models.py`
- Modify: `yoyopod/integrations/contacts/directory.py`
- Modify: `yoyopod/integrations/voice/executor.py`
- Modify: `yoyopod/ui/screens/router.py`
- Modify: `config/people/contacts.seed.yaml`
- Test: `tests/integrations/test_voice_runtime.py`
- Test: `tests/ui/test_screen_routing.py`

- [ ] **Step 1: Write failing contact alias and route action tests**

Add to `tests/integrations/test_voice_runtime.py`:

```python
def test_voice_command_executor_uses_contact_aliases() -> None:
    context = AppContext()
    voip_manager = _FakeVoipManager()
    contact = _FakeContact("Hagar", "sip:mama@example.com", notes="Mama")
    contact.aliases = ["mama", "mommy"]
    executor = _build_executor(
        context=context,
        config_manager=_FakeConfigManager([contact]),
        voip_manager=voip_manager,
    )

    outcome = executor.execute("call mommy")

    assert outcome == VoiceCommandOutcome(
        "Calling",
        "Calling Mama.",
        auto_return=False,
    )
    assert voip_manager.make_calls == [("sip:mama@example.com", "Mama")]
```

Add to `tests/ui/test_screen_routing.py`:

```python
def test_ask_router_supports_safe_voice_route_actions() -> None:
    from yoyopod.ui.screens.router import ScreenRouter

    router = ScreenRouter()

    assert router.resolve("ask", "open_talk").target == "call"
    assert router.resolve("ask", "open_listen").target == "listen"
    assert router.resolve("ask", "open_setup").target == "power"
    assert router.resolve("ask", "go_home").operation == "replace"
    assert router.resolve("ask", "go_home").target == "hub"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest -q tests/integrations/test_voice_runtime.py::test_voice_command_executor_uses_contact_aliases tests/ui/test_screen_routing.py::test_ask_router_supports_safe_voice_route_actions
```

Expected: route assertions fail and contact alias support is incomplete.

- [ ] **Step 3: Add contact aliases to people model**

Modify `yoyopod/integrations/contacts/models.py`.

Add field to `Contact`:

```python
    aliases: list[str] = field(default_factory=list)
```

Update imports:

```python
from dataclasses import dataclass, field
```

In `contacts_from_mapping`, pass aliases:

```python
            aliases=[
                str(alias).strip()
                for alias in contact_data.get("aliases", [])
                if str(alias).strip()
            ],
```

In `contacts_to_mapping`, include aliases when present:

```python
        if contact.aliases:
            entry["aliases"] = list(contact.aliases)
```

Modify `PeopleManager.add_contact` in `yoyopod/integrations/contacts/directory.py`:

```python
    def add_contact(
        self,
        name: str,
        sip_address: str,
        favorite: bool = False,
        notes: str = "",
        aliases: list[str] | None = None,
    ) -> Contact:
```

Pass aliases:

```python
            aliases=list(aliases or []),
```

Add method:

```python
    def get_contact_by_alias(self, alias: str) -> Contact | None:
        """Return one contact matched by name, display name, notes, or alias."""

        normalized = " ".join(alias.strip().lower().split())
        if not normalized:
            return None
        for contact in self.contacts:
            labels = {
                contact.name,
                contact.display_name,
                contact.notes,
                *contact.aliases,
            }
            if normalized in {" ".join(label.strip().lower().split()) for label in labels if label}:
                return contact
        return None
```

Modify `config/people/contacts.seed.yaml`:

```yaml
    aliases:
      - "mama"
      - "mom"
      - "mommy"
```

- [ ] **Step 4: Update executor contact lookup and safe routes**

Modify `_contact_labels` in `yoyopod/integrations/voice/executor.py`:

```python
        labels = {
            cls._normalize_label(contact.name),
            cls._normalize_label(contact.display_name),
            cls._normalize_label(getattr(contact, "notes", "")),
            *{
                cls._normalize_label(alias)
                for alias in getattr(contact, "aliases", [])
            },
        }
```

Keep the existing family alias expansion.

Add route actions to `ScreenRouter._default_routes()` under `"ask"`:

```python
                "open_talk": NavigationRequest.push("call"),
                "open_listen": NavigationRequest.push("listen"),
                "open_setup": NavigationRequest.push("power"),
                "go_home": NavigationRequest.replace("hub"),
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
uv run pytest -q tests/integrations/test_voice_runtime.py::test_voice_command_executor_uses_contact_aliases tests/ui/test_screen_routing.py::test_ask_router_supports_safe_voice_route_actions
```

Expected: both tests pass.

- [ ] **Step 6: Commit aliases and routes**

Run:

```bash
uv run python scripts/quality.py gate
uv run pytest -q
git add yoyopod/integrations/contacts/models.py yoyopod/integrations/contacts/directory.py yoyopod/integrations/voice/executor.py yoyopod/ui/screens/router.py config/people/contacts.seed.yaml tests/integrations/test_voice_runtime.py tests/ui/test_screen_routing.py
git commit -m "feat: support voice contact aliases and safe routes"
```

---

### Task 6: Runtime Command-First Ask Fallback

**Files:**
- Modify: `yoyopod/integrations/voice/runtime.py`
- Modify: `yoyopod/ui/screens/navigation/ask/__init__.py`
- Test: `tests/integrations/test_voice_runtime.py`
- Test: `tests/ui/test_screen_routing.py`

- [ ] **Step 1: Write failing runtime fallback tests**

Add to `tests/integrations/test_voice_runtime.py`:

```python
def test_begin_ask_runs_command_before_ask_fallback() -> None:
    context = AppContext()
    service = _FakeVoiceService("hey yoyo play music")
    ask_client = _FakeAskClient(["unused"])
    outcomes: list[VoiceCommandOutcome] = []
    coordinator = VoiceRuntimeCoordinator(
        context=context,
        settings_resolver=VoiceSettingsResolver(
            context=context,
            settings_provider=lambda: VoiceSettings(
                mode="cloud",
                activation_prefixes=("hey yoyo", "yoyo"),
                ask_fallback_enabled=True,
            ),
        ),
        command_executor=_build_executor(context=context, play_music_action=lambda: True),
        voice_service_factory=lambda settings: service,
        output_player=_FakeOutputPlayer(),
        ask_client=ask_client,
    )
    coordinator.bind(state_listener=lambda state: None, outcome_listener=outcomes.append)

    coordinator.begin_ask(async_capture=False)

    assert ask_client.ask_calls == []
    assert outcomes[-1] == VoiceCommandOutcome(
        "Playing",
        "Starting local music.",
        should_speak=False,
        route_name="shuffle_started",
    )
    assert context.voice.last_transcript == "play music"


def test_begin_ask_falls_back_to_ask_for_non_command() -> None:
    context = AppContext()
    service = _FakeVoiceService("hey yoyo why is the sky blue")
    ask_client = _FakeAskClient(["Because sunlight scatters in the air."])
    outcomes: list[VoiceCommandOutcome] = []
    coordinator = VoiceRuntimeCoordinator(
        context=context,
        settings_resolver=VoiceSettingsResolver(
            context=context,
            settings_provider=lambda: VoiceSettings(
                mode="cloud",
                activation_prefixes=("hey yoyo", "yoyo"),
                ask_fallback_enabled=True,
            ),
        ),
        command_executor=_build_executor(context=context),
        voice_service_factory=lambda settings: service,
        output_player=_FakeOutputPlayer(),
        ask_client=ask_client,
    )
    coordinator.bind(state_listener=lambda state: None, outcome_listener=outcomes.append)

    coordinator.begin_ask(async_capture=False)

    assert ask_client.ask_calls[0]["question"] == "why is the sky blue"
    assert outcomes[-1] == VoiceCommandOutcome(
        "Answer",
        "Because sunlight scatters in the air.",
        auto_return=False,
    )


def test_begin_ask_returns_local_help_when_fallback_disabled() -> None:
    context = AppContext()
    service = _FakeVoiceService("hey yoyo tell me a story")
    ask_client = _FakeAskClient(["unused"])
    outcomes: list[VoiceCommandOutcome] = []
    coordinator = VoiceRuntimeCoordinator(
        context=context,
        settings_resolver=VoiceSettingsResolver(
            context=context,
            settings_provider=lambda: VoiceSettings(
                mode="cloud",
                activation_prefixes=("hey yoyo", "yoyo"),
                ask_fallback_enabled=False,
            ),
        ),
        command_executor=_build_executor(context=context),
        voice_service_factory=lambda settings: service,
        output_player=_FakeOutputPlayer(),
        ask_client=ask_client,
    )
    coordinator.bind(state_listener=lambda state: None, outcome_listener=outcomes.append)

    coordinator.begin_ask(async_capture=False)

    assert ask_client.ask_calls == []
    assert outcomes[-1] == VoiceCommandOutcome(
        "Try Again",
        "Try saying call mom, play music, or volume up.",
        should_speak=False,
        auto_return=False,
    )
```

Add to `tests/ui/test_screen_routing.py`:

```python
def test_ask_screen_uses_yoyo_surface_copy() -> None:
    ask = AskScreen(display=object(), context=AppContext(), voice_runtime=_StubVoiceRuntime())

    ask._on_voice_runtime_state_changed(
        SimpleNamespace(
            phase="idle",
            headline="YoYo",
            body="How can I help?",
            capture_in_flight=False,
            ptt_active=False,
            generation=0,
        )
    )

    assert ask.current_view_model()[0] == "YoYo"
    assert ask.current_view_model()[1] == "How can I help?"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest -q tests/integrations/test_voice_runtime.py::test_begin_ask_runs_command_before_ask_fallback tests/integrations/test_voice_runtime.py::test_begin_ask_falls_back_to_ask_for_non_command tests/integrations/test_voice_runtime.py::test_begin_ask_returns_local_help_when_fallback_disabled tests/ui/test_screen_routing.py::test_ask_screen_uses_yoyo_surface_copy
```

Expected: Ask currently sends all normal Ask phrases to the Ask worker, and UI copy still defaults to `Ask`.

- [ ] **Step 3: Add router construction helper to runtime**

Modify `yoyopod/integrations/voice/runtime.py`.

Add imports:

```python
from yoyopod.integrations.voice.dictionary import load_voice_command_dictionary
from yoyopod.integrations.voice.router import VoiceRouteKind, VoiceRouter
```

Add method to `VoiceRuntimeCoordinator`:

```python
    def _voice_router(self, settings: VoiceSettings) -> VoiceRouter:
        return VoiceRouter(
            dictionary=load_voice_command_dictionary(settings.command_dictionary_path),
            activation_prefixes=settings.activation_prefixes,
            ask_fallback_enabled=settings.ask_fallback_enabled,
        )
```

Add local help helper:

```python
    def _local_voice_help_outcome(self) -> VoiceCommandOutcome:
        return VoiceCommandOutcome(
            "Try Again",
            "Try saying call mom, play music, or volume up.",
            should_speak=False,
            auto_return=False,
        )
```

- [ ] **Step 4: Route Ask transcripts before worker calls**

In `_run_ask_cycle`, after `question = transcript.text.strip()` and before exit phrase handling, replace direct Ask routing with:

```python
        router = self._voice_router(settings)
        decision = router.route(question)
        if decision.kind is VoiceRouteKind.COMMAND and decision.command is not None:
            self._dispatch_ask_outcome(
                self.handle_transcript(decision.normalized_text),
                generation,
            )
            return
        if decision.kind is VoiceRouteKind.LOCAL_HELP:
            self._dispatch_ask_outcome(self._local_voice_help_outcome(), generation)
            return

        question = decision.normalized_text
```

Then keep the existing exit phrase and Ask worker logic using the normalized `question`.

If calling `handle_transcript()` inside `_run_ask_cycle` causes duplicate state dispatch in tests, extract command execution into a helper:

```python
    def _execute_command_transcript(self, transcript: str) -> VoiceCommandOutcome:
        outcome = self._command_executor.execute(transcript)
        logger.info(
            "Voice command outcome headline={} should_speak={} route={} auto_return={} transcript={}",
            outcome.headline,
            outcome.should_speak,
            outcome.route_name or "",
            outcome.auto_return,
            _preview_voice_text(transcript),
        )
        return outcome
```

Then have `handle_transcript()` call `_execute_command_transcript()` and `_apply_outcome()`, while `_run_ask_cycle` uses `_execute_command_transcript()` and `_dispatch_ask_outcome()`.

- [ ] **Step 5: Update YoYo UI copy**

Modify `AskScreen.__init__` in `yoyopod/ui/screens/navigation/ask/__init__.py`:

```python
        self._headline: str = "YoYo"
        self._body: str = "How can I help?"
```

Modify `_screen_summary`:

```python
        if self._quick_command:
            return "You are using YoYo. Say a command or question now."
        return "You are on YoYo. Ask a question or say a command."
```

Modify `VoiceRuntimeCoordinator.reset_to_idle()` in `runtime.py`:

```python
        self._set_state("idle", "YoYo", "How can I help?")
```

Modify `VoiceRuntimeCoordinator.begin_ask()` listening state body:

```python
            "Say YoYo, then ask or command...",
```

- [ ] **Step 6: Run focused runtime/UI tests**

Run:

```bash
uv run pytest -q tests/integrations/test_voice_runtime.py::test_begin_ask_runs_command_before_ask_fallback tests/integrations/test_voice_runtime.py::test_begin_ask_falls_back_to_ask_for_non_command tests/integrations/test_voice_runtime.py::test_begin_ask_returns_local_help_when_fallback_disabled tests/ui/test_screen_routing.py::test_ask_screen_uses_yoyo_surface_copy
```

Expected: all tests pass.

- [ ] **Step 7: Run broader voice and screen tests**

Run:

```bash
uv run pytest -q tests/integrations/test_voice_runtime.py tests/integrations/test_voice_service.py tests/ui/test_screen_routing.py
```

Expected: all tests pass.

- [ ] **Step 8: Commit runtime integration**

Run:

```bash
uv run python scripts/quality.py gate
uv run pytest -q
git add yoyopod/integrations/voice/runtime.py yoyopod/ui/screens/navigation/ask/__init__.py tests/integrations/test_voice_runtime.py tests/ui/test_screen_routing.py
git commit -m "feat: route YoYo voice commands before Ask fallback"
```

---

### Task 7: Future Wake Detector Interface

**Files:**
- Create: `yoyopod/integrations/voice/wake.py`
- Modify: `yoyopod/integrations/voice/__init__.py`
- Test: `tests/integrations/test_voice_wake.py`

- [ ] **Step 1: Write failing wake interface tests**

Create `tests/integrations/test_voice_wake.py`:

```python
"""Tests for future wake detector seam."""

from __future__ import annotations

from yoyopod.integrations.voice.wake import NoopWakeDetector, WakeDetectionResult


def test_noop_wake_detector_is_button_gated_only() -> None:
    detector = NoopWakeDetector()

    assert detector.is_available() is False
    assert detector.start() is False
    assert detector.poll() == WakeDetectionResult(detected=False, phrase="")
    detector.stop()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest -q tests/integrations/test_voice_wake.py
```

Expected: import failure for `wake.py`.

- [ ] **Step 3: Implement no-op wake seam**

Create `yoyopod/integrations/voice/wake.py`:

```python
"""Future wake-word detector seam for YoYo voice activation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True, frozen=True)
class WakeDetectionResult:
    """Result returned by a wake detector poll."""

    detected: bool
    phrase: str = ""


class WakeDetector(Protocol):
    """Backend interface for future always-listening wake detection."""

    def is_available(self) -> bool:
        """Return True when this backend can run on the current device."""

    def start(self) -> bool:
        """Start wake detection."""

    def poll(self) -> WakeDetectionResult:
        """Return the latest wake detection state."""

    def stop(self) -> None:
        """Stop wake detection and release resources."""


class NoopWakeDetector:
    """Button-gated wake detector used until hardware wake listening ships."""

    def is_available(self) -> bool:
        return False

    def start(self) -> bool:
        return False

    def poll(self) -> WakeDetectionResult:
        return WakeDetectionResult(detected=False, phrase="")

    def stop(self) -> None:
        return None


__all__ = [
    "NoopWakeDetector",
    "WakeDetectionResult",
    "WakeDetector",
]
```

- [ ] **Step 4: Export wake types**

Modify `yoyopod/integrations/voice/__init__.py`.

Add `TYPE_CHECKING` imports:

```python
    from yoyopod.integrations.voice.wake import (
        NoopWakeDetector,
        WakeDetectionResult,
        WakeDetector,
    )
```

Add `_PUBLIC_EXPORTS` entries:

```python
    "NoopWakeDetector": ("yoyopod.integrations.voice.wake", "NoopWakeDetector"),
    "WakeDetectionResult": ("yoyopod.integrations.voice.wake", "WakeDetectionResult"),
    "WakeDetector": ("yoyopod.integrations.voice.wake", "WakeDetector"),
```

Add `__all__` entries:

```python
    "NoopWakeDetector",
    "WakeDetectionResult",
    "WakeDetector",
```

- [ ] **Step 5: Run wake tests**

Run:

```bash
uv run pytest -q tests/integrations/test_voice_wake.py
```

Expected: all tests pass.

- [ ] **Step 6: Commit wake seam**

Run:

```bash
uv run python scripts/quality.py gate
uv run pytest -q
git add yoyopod/integrations/voice/wake.py yoyopod/integrations/voice/__init__.py tests/integrations/test_voice_wake.py
git commit -m "feat: add future voice wake detector seam"
```

---

### Task 8: Docs, Quality Gate, And Final Verification

**Files:**
- Modify: `docs/README.md`
- Modify: `docs/VOICE_COMMAND_PLAN.md`
- Review: `docs/superpowers/specs/2026-04-27-cautious-unified-voice-design.md`

- [ ] **Step 1: Update docs index and stale plan note**

Modify `docs/README.md` voice section so the new spec is listed as the current voice design:

```markdown
- [`superpowers/specs/2026-04-27-cautious-unified-voice-design.md`](superpowers/specs/2026-04-27-cautious-unified-voice-design.md), current design for unified YoYo voice command and Ask routing
```

Modify the top note in `docs/VOICE_COMMAND_PLAN.md`:

```markdown
> Current note: this document is historical. The current direction for YoYo voice command and Ask coherence is `docs/superpowers/specs/2026-04-27-cautious-unified-voice-design.md`, which defines the button-gated, command-first, Ask-fallback design.
```

- [ ] **Step 2: Run focused tests for all changed voice surfaces**

Run:

```bash
uv run pytest -q tests/integrations/test_voice_activation.py tests/integrations/test_voice_dictionary.py tests/integrations/test_voice_router.py tests/integrations/test_voice_wake.py tests/integrations/test_voice_runtime.py tests/integrations/test_voice_service.py tests/config/test_config_voice_device_persistence.py tests/ui/test_screen_routing.py
```

Expected: all tests pass.

- [ ] **Step 3: Run required pre-commit gate**

Run:

```bash
uv run python scripts/quality.py gate
```

Expected: `result=passed`.

- [ ] **Step 4: Run full test suite**

Run:

```bash
uv run pytest -q
```

Expected on Windows: existing known Windows-only failures may appear. If failures appear, compare them to the repository's current Windows note and isolate whether they touch files changed by this plan. If no new failures appear, record the pass count in the final message.

- [ ] **Step 5: Commit docs and final verification**

Run:

```bash
uv run python scripts/quality.py gate
uv run pytest -q
git add docs/README.md docs/VOICE_COMMAND_PLAN.md
git commit -m "docs: mark cautious unified voice as current direction"
```

- [ ] **Step 6: Final implementation summary**

In the final implementation response, include:

- The chosen behavior: button-gated YoYo activation, command-first routing, Ask fallback.
- The exact test commands and results.
- Any Windows-only test failures if they occurred.
- A note that always-listening wake remains a no-op interface for future hardware validation.

Before any final commit or push, run both required commands:

```bash
uv run python scripts/quality.py gate
uv run pytest -q
```
