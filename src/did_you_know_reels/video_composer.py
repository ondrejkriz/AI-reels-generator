"""FFmpeg-based placeholder-first vertical video composition."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import shutil
import subprocess

from .models import ReelDraft
from .utils import ensure_directory, write_text

LOGGER = logging.getLogger(__name__)


def _escape_drawtext(value: str) -> str:
    """Escape text values passed into ffmpeg drawtext."""

    return value.replace("\\", r"\\").replace(":", r"\:").replace("'", r"\'").replace("%", r"\%").replace(",", r"\,")


def _escape_filter_path(path: Path) -> str:
    """Escape file paths used inside ffmpeg filter graphs."""

    return path.resolve().as_posix().replace(":", r"\:")


class VideoComposer:
    """Creates a 9:16 MP4 from placeholder scenes and subtitles."""

    def __init__(self, ffmpeg_binary: str, width: int, height: int, fps: int) -> None:
        self.ffmpeg_binary = ffmpeg_binary
        self.width = width
        self.height = height
        self.fps = fps

    def compose(
        self,
        draft: ReelDraft,
        output_root: str,
        dry_run: bool = False,
        voiceover_audio_path: str | None = None,
    ) -> dict[str, str]:
        """Render a video or gracefully export a render plan when rendering is unavailable."""

        video_dir = ensure_directory(Path(output_root) / "videos")
        work_dir = ensure_directory(video_dir / f"{draft.draft_id}_work")
        output_video = video_dir / f"{draft.draft_id}.mp4"
        subtitle_path = Path(output_root) / "subtitles" / f"{draft.draft_id}.srt"
        render_plan = {
            "ffmpeg_binary": self.ffmpeg_binary,
            "scene_count": len(draft.scenes),
            "output_video": str(output_video),
            "subtitle_path": str(subtitle_path),
            "voiceover_audio_path": voiceover_audio_path or "",
            "scene_assets": draft.render_plan.get("scene_assets", []) if draft.render_plan else [],
            "dry_run": dry_run,
        }
        plan_path = write_text(work_dir / "render_plan.json", json.dumps(render_plan, ensure_ascii=False, indent=2))

        if dry_run:
            return {"video_path": "", "render_plan_path": str(plan_path), "status": "dry_run"}

        if not shutil.which(self.ffmpeg_binary):
            LOGGER.warning("FFmpeg binary '%s' not found. Returning render plan only.", self.ffmpeg_binary)
            return {"video_path": "", "render_plan_path": str(plan_path), "status": "ffmpeg_missing"}

        clip_paths: list[Path] = []
        scene_assets = draft.render_plan.get("scene_assets", []) if draft.render_plan else []
        overlay_mode = "drawtext"
        for index, scene in enumerate(draft.scenes, start=1):
            clip_path = work_dir / f"scene_{index:02}.mp4"
            asset = scene_assets[index - 1] if index - 1 < len(scene_assets) else {}
            color = str(asset.get("placeholder_color", "#101820"))
            try:
                self._render_scene_clip(
                    clip_path,
                    color,
                    scene.duration_seconds,
                    scene.scene_number,
                    scene.purpose,
                    scene.overlay_text,
                    with_drawtext=overlay_mode == "drawtext",
                )
            except RuntimeError as exc:
                if overlay_mode == "drawtext" and "No such filter: 'drawtext'" in str(exc):
                    LOGGER.warning("drawtext filter is unavailable in this ffmpeg build. Falling back to plain scene backgrounds.")
                    overlay_mode = "none"
                    self._render_scene_clip(
                        clip_path,
                        color,
                        scene.duration_seconds,
                        scene.scene_number,
                        scene.purpose,
                        scene.overlay_text,
                        with_drawtext=False,
                    )
                else:
                    raise
            clip_paths.append(clip_path)

        concat_file = work_dir / "concat.txt"
        write_text(concat_file, "\n".join(f"file '{clip.resolve().as_posix()}'" for clip in clip_paths))
        merged_video = work_dir / "merged.mp4"
        self._run([self.ffmpeg_binary, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(merged_video)])
        subtitle_mode = "burned"
        processed_video = work_dir / "processed.mp4"
        try:
            self._run(
                [
                    self.ffmpeg_binary,
                    "-y",
                    "-i",
                    str(merged_video),
                    "-vf",
                    f"subtitles='{_escape_filter_path(subtitle_path)}'",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "medium",
                    "-crf",
                    "22",
                    "-pix_fmt",
                    "yuv420p",
                    str(processed_video),
                ]
            )
        except RuntimeError as exc:
            LOGGER.warning("Burned subtitles failed for this ffmpeg build. Exporting video without burned subtitles. Error: %s", exc)
            subtitle_mode = "external_only"
            processed_video = merged_video

        audio_track = Path(voiceover_audio_path) if voiceover_audio_path else work_dir / "audio_bed.wav"
        audio_mode = "voiceover_tts" if voiceover_audio_path and Path(voiceover_audio_path).exists() else "synthetic_bed"
        if audio_mode == "synthetic_bed":
            total_duration = sum(scene.duration_seconds for scene in draft.scenes)
            self._run(
                [
                    self.ffmpeg_binary,
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    f"sine=frequency=220:sample_rate=44100:duration={total_duration}",
                    "-filter:a",
                    "volume=0.05",
                    str(audio_track),
                ]
            )
        self._run(
            [
                self.ffmpeg_binary,
                "-y",
                "-i",
                str(processed_video),
                "-i",
                str(audio_track),
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-af",
                "apad",
                "-shortest",
                str(output_video),
            ]
        )
        return {
            "video_path": str(output_video),
            "render_plan_path": str(plan_path),
            "status": "rendered",
            "overlay_mode": overlay_mode,
            "subtitle_mode": subtitle_mode,
            "audio_mode": audio_mode,
        }

    def _render_scene_clip(
        self,
        clip_path: Path,
        color: str,
        duration_seconds: float,
        scene_number: int,
        purpose: str,
        overlay_text: str,
        *,
        with_drawtext: bool,
    ) -> None:
        """Render one scene clip, with text overlay when supported."""

        command = [
            self.ffmpeg_binary,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s={self.width}x{self.height}:d={duration_seconds}:r={self.fps}",
        ]
        if with_drawtext:
            badge_text = _escape_drawtext(f"{scene_number:02}  {purpose.upper()}")
            headline_text = _escape_drawtext(overlay_text)
            command.extend(
                [
                    "-vf",
                    (
                        "drawbox=x=70:y=120:w=940:h=240:color=black@0.35:t=fill,"
                        "drawbox=x=70:y=1500:w=940:h=240:color=black@0.18:t=fill,"
                        "drawtext="
                        f"text='{badge_text}':"
                        "fontcolor=white:fontsize=28:"
                        "x=110:y=150:"
                        "box=1:boxcolor=white@0.08:boxborderw=12,"
                        "drawtext="
                        f"text='{headline_text}':"
                        "fontcolor=white:fontsize=62:"
                        "x=110:y=260:"
                        "box=0:"
                        "line_spacing=12"
                    ),
                ]
            )
        command.extend(["-pix_fmt", "yuv420p", str(clip_path)])
        self._run(command)

    def _run(self, command: list[str]) -> None:
        """Execute an ffmpeg command and surface stderr on failure."""

        LOGGER.info("Running FFmpeg command: %s", " ".join(command))
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(exc.stderr.strip() or "FFmpeg command failed.") from exc
