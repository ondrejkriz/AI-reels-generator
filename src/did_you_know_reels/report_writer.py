"""Persist JSON reports and intermediate output files."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .models import ReelDraft
from .utils import ensure_directory, write_json, write_text


class ReportWriter:
    """Handles saving all generated artifacts to disk."""

    def persist(self, draft: ReelDraft, prompts: list[dict[str, str]]) -> dict[str, str]:
        """Persist all draft outputs and return their paths."""

        output_root = Path(draft.output_root)
        for name in ["scripts", "scenes", "subtitles", "voiceover", "prompts", "videos", "metadata", "reports"]:
            ensure_directory(output_root / name)

        script_path = write_json(output_root / "scripts" / f"{draft.draft_id}.json", draft.to_dict())
        scene_path = write_json(
            output_root / "scenes" / f"{draft.draft_id}_scenes.json",
            {"draft_id": draft.draft_id, "scenes": [asdict(scene) for scene in draft.scenes]},
        )
        subtitle_path = write_text(output_root / "subtitles" / f"{draft.draft_id}.srt", draft.subtitles)
        voiceover_path = write_text(output_root / "voiceover" / f"{draft.draft_id}.txt", draft.voiceover_text)
        prompt_path = write_json(output_root / "prompts" / f"{draft.draft_id}_prompts.json", {"prompts": prompts})
        metadata_path = write_json(output_root / "metadata" / f"{draft.draft_id}.json", asdict(draft.metadata))
        report_path = write_json(
            output_root / "reports" / f"{draft.draft_id}_report.json",
            {
                "draft_id": draft.draft_id,
                "topic": draft.topic,
                "provider": draft.provider_name,
                "validation": asdict(draft.validation),
                "sources": [asdict(source) for source in draft.sources],
                "score": asdict(draft.score),
                "render_plan": draft.render_plan or {},
                "dry_run": draft.dry_run,
            },
        )
        return {
            "script": str(script_path),
            "scene": str(scene_path),
            "subtitles": str(subtitle_path),
            "voiceover": str(voiceover_path),
            "prompts": str(prompt_path),
            "metadata": str(metadata_path),
            "report": str(report_path),
        }
