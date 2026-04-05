"""End-to-end orchestration of generation and render steps."""

from __future__ import annotations

import logging
from pathlib import Path

from .config import AppConfig

from .asset_manager import AssetManager
from .fact_validator import FactValidator
from .metadata_generator import MetadataGenerator
from .models import DraftScore, FactSource, MetadataBundle, ReelDraft, Scene, ScriptParts, TopicIdea, ValidationResult
from .prompt_builder import PromptBuilder
from .providers import build_provider
from .report_writer import ReportWriter
from .scene_planner import ScenePlanner
from .scoring import DraftScorer
from .script_generator import ScriptGenerator
from .subtitle_generator import SubtitleGenerator
from .topic_generator import TopicGenerator
from .utils import read_json, slugify, utc_now_iso
from .video_composer import VideoComposer
from .voiceover_generator import VoiceoverGenerator
from .wikipedia_client import WikipediaClient

LOGGER = logging.getLogger(__name__)


class ReelPipeline:
    """High-level application service for draft generation and rendering."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.provider = build_provider(config.provider)
        wikipedia_cfg = dict(config.sources.get("wikipedia", {}))
        wikipedia_client = None
        if wikipedia_cfg.get("enabled", True):
            wikipedia_client = WikipediaClient(
                language=str(wikipedia_cfg.get("language", "cs")),
                timeout_seconds=int(wikipedia_cfg.get("timeout_seconds", 10)),
                user_agent=str(wikipedia_cfg.get("user_agent", "did-you-know-reels-generator/0.1")),
            )
        self.topic_generator = TopicGenerator(self.provider)
        self.script_generator = ScriptGenerator(self.provider, config.content["cta"])
        self.fact_validator = FactValidator(
            self.provider,
            config.content["fact_status_without_validation"],
            wikipedia_client=wikipedia_client,
        )
        self.scene_planner = ScenePlanner(float(config.video["default_scene_duration"]))
        self.prompt_builder = PromptBuilder()
        self.voiceover_generator = VoiceoverGenerator(
            voice_name=str(config.tts.get("voice_name", "")),
            rate=int(config.tts.get("rate", 0)),
            volume=int(config.tts.get("volume", 100)),
        )
        self.subtitle_generator = SubtitleGenerator()
        self.asset_manager = AssetManager(
            str(config.resolve_path("assets/backgrounds")),
            list(config.video["background_colors"]),
        )
        self.metadata_generator = MetadataGenerator()
        self.scorer = DraftScorer(config.scoring)
        self.report_writer = ReportWriter()
        self.video_composer = VideoComposer(
            ffmpeg_binary=str(config.video["ffmpeg_binary"]),
            width=int(config.video["width"]),
            height=int(config.video["height"]),
            fps=int(config.video["fps"]),
        )

    def generate_draft(self, topic: str, output_root: str, index: int = 1, dry_run: bool = False) -> tuple[ReelDraft, dict[str, str]]:
        """Generate a draft plus all intermediate artifacts."""

        normalized_output_root = self._normalize_output_root(output_root)
        idea = self.topic_generator.generate(topic)
        script = self.script_generator.generate(topic, idea)
        scenes = self.scene_planner.plan(script)
        prompts = self.prompt_builder.build(topic, scenes)
        voiceover = self.voiceover_generator.build(scenes)
        subtitles = self.subtitle_generator.build(scenes)
        validation, sources = self.fact_validator.validate(script, topic)
        metadata = self.metadata_generator.build(topic, script)
        score = self.scorer.score(script, scenes, subtitles)
        draft_id = f"{slugify(topic)}_{index:03}"
        scene_assets = self.asset_manager.build_scene_assets(scenes)
        render_plan = {"scene_assets": scene_assets, "video_settings": self.config.video}

        draft = ReelDraft(
            draft_id=draft_id,
            topic=topic,
            niche=topic,
            idea=idea,
            script=script,
            scenes=scenes,
            voiceover_text=voiceover,
            subtitles=subtitles,
            validation=validation,
            sources=sources,
            metadata=metadata,
            score=score,
            output_root=str(normalized_output_root),
            created_at=utc_now_iso(),
            provider_name=self.provider.name,
            dry_run=dry_run,
            render_plan=render_plan,
        )
        paths = self.report_writer.persist(draft, prompts)
        return draft, paths

    def render_draft(self, draft: ReelDraft, output_root: str, dry_run: bool = False) -> dict[str, str]:
        normalized_output_root = self._normalize_output_root(output_root)
        voiceover_audio_path = None
        try:
            voiceover_audio_path = self.voiceover_generator.synthesize(
                draft.voiceover_text,
                normalized_output_root / "voiceover" / f"{draft.draft_id}.wav",
                dry_run=dry_run,
            )
        except Exception as exc:
            LOGGER.warning("Local TTS synthesis failed, falling back to synthetic bed: %s", exc)
        result = self.video_composer.compose(
            draft,
            output_root=str(normalized_output_root),
            dry_run=dry_run,
            voiceover_audio_path=voiceover_audio_path,
        )
        LOGGER.info("Render result for %s: %s", draft.draft_id, result)
        return result

    def load_draft_from_script(self, script_path: str) -> ReelDraft:
        """Load a persisted draft from its stored script JSON."""

        payload = read_json(script_path)
        return ReelDraft(
            draft_id=payload["draft_id"],
            topic=payload["topic"],
            niche=payload["niche"],
            idea=TopicIdea(**payload["idea"]),
            script=ScriptParts(
                hook=payload["script"]["hook"],
                fact=payload["script"]["fact"],
                explanation=payload["script"]["explanation"],
                payoff=payload["script"]["payoff"],
                cta=payload["script"]["cta"],
                language=payload["script"].get("language", "cs"),
            ),
            scenes=[Scene(**scene) for scene in payload["scenes"]],
            voiceover_text=payload["voiceover_text"],
            subtitles=payload["subtitles"],
            validation=ValidationResult(**payload["validation"]),
            sources=[FactSource(**source) for source in payload.get("sources", [])],
            metadata=MetadataBundle(**payload["metadata"]),
            score=DraftScore(**payload["score"]),
            output_root=payload["output_root"],
            created_at=payload["created_at"],
            provider_name=payload["provider_name"],
            dry_run=bool(payload.get("dry_run", False)),
            render_plan=payload.get("render_plan"),
        )

    def _normalize_output_root(self, output_root: str) -> Path:
        """Resolve CLI output paths against the project root."""

        candidate = Path(output_root)
        if candidate.is_absolute():
            return candidate
        return (self.config.project_root / candidate).resolve()
