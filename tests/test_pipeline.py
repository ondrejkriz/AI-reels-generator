from pathlib import Path

from did_you_know_reels.config import load_config
from did_you_know_reels.models import FactSource
from did_you_know_reels.pipeline import ReelPipeline


def test_generate_draft_persists_expected_outputs(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    config_path.write_text(
        """
app:
  log_file: "./logs/test.log"
video:
  background_colors:
    - "#111111"
    - "#222222"
    - "#333333"
    - "#444444"
        """.strip(),
        encoding="utf-8",
    )
    env_path.write_text("LLM_PROVIDER=mock", encoding="utf-8")
    (tmp_path / "assets" / "backgrounds").mkdir(parents=True)

    pipeline = ReelPipeline(load_config(config_path, env_path))
    draft, paths = pipeline.generate_draft("space", str(tmp_path / "output"), dry_run=True)

    assert draft.provider_name == "mock"
    assert Path(paths["script"]).exists()
    assert Path(paths["scene"]).exists()
    assert Path(paths["subtitles"]).exists()
    assert Path(paths["report"]).exists()
    assert draft.validation.status == "needs_review"
    assert draft.sources == []


def test_render_draft_returns_plan_when_ffmpeg_is_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    config_path.write_text(
        """
app:
  log_file: "./logs/test.log"
video:
  ffmpeg_binary: "ffmpeg-that-does-not-exist"
        """.strip(),
        encoding="utf-8",
    )
    env_path.write_text("LLM_PROVIDER=mock", encoding="utf-8")
    (tmp_path / "assets" / "backgrounds").mkdir(parents=True)

    pipeline = ReelPipeline(load_config(config_path, env_path))
    output_root = tmp_path / "output"
    draft, _ = pipeline.generate_draft("animals", str(output_root), dry_run=False)
    result = pipeline.render_draft(draft, str(output_root), dry_run=False)

    assert result["status"] == "ffmpeg_missing"
    assert Path(result["render_plan_path"]).exists()


def test_generate_draft_uses_wikipedia_source_when_available(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    config_path.write_text(
        """
app:
  log_file: "./logs/test.log"
        """.strip(),
        encoding="utf-8",
    )
    env_path.write_text("LLM_PROVIDER=mock", encoding="utf-8")
    (tmp_path / "assets" / "backgrounds").mkdir(parents=True)

    pipeline = ReelPipeline(load_config(config_path, env_path))

    class StubWikiClient:
        def fetch_source(self, query: str) -> FactSource | None:
            return FactSource(
                source_name="wikipedia",
                source_title="Venuše",
                source_url="https://cs.wikipedia.org/wiki/Venu%C5%A1e",
                summary="Venuše je planeta. Venuše se otáčí velmi pomalu a opačným směrem.",
                retrieved_at="2026-04-02T00:00:00+00:00",
                language="cs",
            )

    pipeline.fact_validator.wikipedia_client = StubWikiClient()
    draft, _ = pipeline.generate_draft("space", str(tmp_path / "output"), dry_run=True)

    assert draft.sources
    assert draft.sources[0].source_name == "wikipedia"
    assert draft.validation.status == "partially_validated"
