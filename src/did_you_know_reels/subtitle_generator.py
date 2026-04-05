"""Subtitle generation in SRT format."""

from __future__ import annotations

from .models import Scene
from .utils import seconds_to_srt_timestamp


class SubtitleGenerator:
    """Converts scenes into subtitles."""

    def build(self, scenes: list[Scene]) -> str:
        current_time = 0.0
        entries: list[str] = []
        for index, scene in enumerate(scenes, start=1):
            start = current_time
            end = current_time + scene.duration_seconds
            entries.append(
                "\n".join(
                    [
                        str(index),
                        f"{seconds_to_srt_timestamp(start)} --> {seconds_to_srt_timestamp(end)}",
                        scene.narration,
                    ]
                )
            )
            current_time = end
        return "\n\n".join(entries) + "\n"

