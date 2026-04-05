"""Configuration loading from YAML and .env with typed access helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import os


JsonDict = dict[str, Any]


@dataclass(slots=True)
class AppConfig:
    """Typed wrapper around merged configuration."""

    raw: JsonDict
    project_root: Path
    config_path: Path
    env_path: Path

    @property
    def app(self) -> JsonDict:
        return self.raw["app"]

    @property
    def provider(self) -> JsonDict:
        return self.raw["provider"]

    @property
    def video(self) -> JsonDict:
        return self.raw["video"]

    @property
    def scoring(self) -> JsonDict:
        return self.raw["scoring"]

    @property
    def content(self) -> JsonDict:
        return self.raw["content"]

    @property
    def sources(self) -> JsonDict:
        return self.raw["sources"]

    @property
    def tts(self) -> JsonDict:
        return self.raw["tts"]

    def resolve_path(self, value: str | Path) -> Path:
        """Resolve project-relative paths against the config directory."""

        path = Path(value)
        if path.is_absolute():
            return path
        return (self.project_root / path).resolve()


def load_dotenv(env_path: str | Path = ".env") -> dict[str, str]:
    """Load a minimal KEY=VALUE style dotenv file."""

    payload: dict[str, str] = {}
    path = Path(env_path)
    if not path.exists():
        return payload

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        payload[key.strip()] = value.strip().strip("\"'")
    return payload


def _deep_merge(base: JsonDict, updates: JsonDict) -> JsonDict:
    merged = dict(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if value.startswith(("\"", "'")) and value.endswith(("\"", "'")) and len(value) >= 2:
        return value[1:-1]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _simple_yaml_load(content: str) -> JsonDict:
    """Parse the limited YAML subset used by this project."""

    lines = [
        (len(raw) - len(raw.lstrip(" ")), raw.strip())
        for raw in content.splitlines()
        if raw.strip() and not raw.lstrip().startswith("#")
    ]

    def parse_block(index: int, expected_indent: int) -> tuple[Any, int]:
        if index >= len(lines):
            return {}, index

        current_indent, current_line = lines[index]
        if current_indent != expected_indent:
            raise ValueError("Invalid YAML indentation for current config subset.")

        if current_line.startswith("- "):
            items: list[Any] = []
            while index < len(lines):
                indent, line = lines[index]
                if indent < expected_indent or indent != expected_indent or not line.startswith("- "):
                    break
                items.append(_parse_scalar(line[2:].strip()))
                index += 1
            return items, index

        mapping: JsonDict = {}
        while index < len(lines):
            indent, line = lines[index]
            if indent < expected_indent:
                break
            if indent != expected_indent:
                raise ValueError("Invalid nested YAML indentation.")
            if line.startswith("- "):
                break

            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            index += 1

            if value:
                mapping[key] = _parse_scalar(value)
                continue

            if index >= len(lines):
                mapping[key] = {}
                continue

            next_indent, _ = lines[index]
            if next_indent <= indent:
                mapping[key] = {}
                continue

            child, index = parse_block(index, next_indent)
            mapping[key] = child
        return mapping, index

    if not lines:
        return {}
    parsed, _ = parse_block(0, lines[0][0])
    if not isinstance(parsed, dict):
        raise ValueError("Top-level YAML must be a mapping.")
    return parsed


def load_config(config_path: str | Path = "config.yaml", env_path: str | Path = ".env") -> AppConfig:
    """Load YAML configuration and apply environment overrides."""

    config_file = Path(config_path).resolve()
    env_file = Path(env_path).resolve()
    if not config_file.exists():
        raise FileNotFoundError(f"Missing config file: {config_file}")

    raw_config = _simple_yaml_load(config_file.read_text(encoding="utf-8")) or {}
    env_values = load_dotenv(env_file)
    env = {**env_values, **os.environ}

    if env.get("LLM_PROVIDER"):
        raw_config.setdefault("provider", {})
        raw_config["provider"]["default"] = env["LLM_PROVIDER"]

    if env.get("OPENAI_MODEL"):
        raw_config.setdefault("provider", {})
        raw_config["provider"]["openai_model"] = env["OPENAI_MODEL"]

    if env.get("OPENAI_API_KEY"):
        raw_config.setdefault("provider", {})
        raw_config["provider"]["openai_api_key"] = env["OPENAI_API_KEY"]

    if env.get("FACT_VALIDATION_STRICT"):
        raw_config.setdefault("content", {})
        raw_config["content"]["fact_validation_strict"] = env["FACT_VALIDATION_STRICT"].lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    if env.get("FFMPEG_BINARY"):
        raw_config.setdefault("video", {})
        raw_config["video"]["ffmpeg_binary"] = env["FFMPEG_BINARY"]

    if env.get("LOG_LEVEL"):
        raw_config.setdefault("app", {})
        raw_config["app"]["log_level"] = env["LOG_LEVEL"]

    defaults: JsonDict = {
        "app": {
            "language": "cs",
            "default_output_dir": "./output",
            "log_file": "./logs/app.log",
            "min_duration_seconds": 15,
            "max_duration_seconds": 35,
            "target_platforms": ["youtube_shorts", "tiktok", "instagram_reels"],
            "log_level": "INFO",
        },
        "provider": {
            "default": "mock",
            "temperature": 0.7,
            "max_tokens": 900,
            "request_timeout_seconds": 45,
            "openai_api_key": "",
        },
        "video": {
            "width": 1080,
            "height": 1920,
            "fps": 30,
            "default_scene_duration": 4.0,
            "title_safe_margin": 110,
            "subtitle_safe_margin": 220,
            "background_colors": ["#101820", "#19323c", "#2d3047", "#275d63"],
            "transition_text": "Věděli jste, že...?",
            "ffmpeg_binary": "ffmpeg",
        },
        "scoring": {
            "hook_weight": 0.25,
            "brevity_weight": 0.15,
            "surprise_weight": 0.2,
            "duration_weight": 0.15,
            "readability_weight": 0.1,
            "scene_diversity_weight": 0.15,
            "target_word_count_min": 35,
            "target_word_count_max": 85,
        },
        "content": {
            "cta": "Sleduj pro víc.",
            "fact_status_without_validation": "needs_review",
            "supported_topics": ["animals", "history", "science", "space"],
            "fact_validation_strict": False,
        },
        "sources": {
            "wikipedia": {
                "enabled": True,
                "language": "cs",
                "timeout_seconds": 10,
                "user_agent": "did-you-know-reels-generator/0.1",
            }
        },
        "tts": {
            "engine": "windows_sapi",
            "voice_name": "",
            "rate": 0,
            "volume": 100,
        },
    }

    merged = _deep_merge(defaults, raw_config)
    return AppConfig(
        raw=merged,
        project_root=config_file.parent,
        config_path=config_file,
        env_path=env_file,
    )
