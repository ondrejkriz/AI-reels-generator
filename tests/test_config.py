from pathlib import Path

from did_you_know_reels.config import load_config


def test_load_config_merges_env_override(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"

    config_path.write_text(
        """
app:
  log_file: "./logs/test.log"
provider:
  default: "mock"
video:
  width: 720
  background_colors:
    - "#111111"
    - "#222222"
        """.strip(),
        encoding="utf-8",
    )
    env_path.write_text(
        "LLM_PROVIDER=openai\nFFMPEG_BINARY=ffmpeg-custom\nOPENAI_API_KEY=demo-key",
        encoding="utf-8",
    )

    config = load_config(config_path, env_path)

    assert config.provider["default"] == "openai"
    assert config.provider["openai_api_key"] == "demo-key"
    assert config.video["ffmpeg_binary"] == "ffmpeg-custom"
    assert config.video["width"] == 720
    assert config.video["background_colors"] == ["#111111", "#222222"]
    assert config.resolve_path("assets/backgrounds") == tmp_path / "assets" / "backgrounds"
