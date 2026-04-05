"""Prompt generation for image or video scene synthesis."""

from __future__ import annotations

from .models import Scene


class PromptBuilder:
    """Creates generation prompts for each scene."""

    def build(self, topic: str, scenes: list[Scene]) -> list[dict[str, str]]:
        prompts: list[dict[str, str]] = []
        for scene in scenes:
            prompts.append(
                {
                    "scene_id": f"scene_{scene.scene_number:02}",
                    "prompt": (
                        f"Create a vertical 9:16 reel scene about {topic}. "
                        f"Purpose: {scene.purpose}. "
                        f"Visual style: high contrast, scroll-stopping, readable text-safe composition. "
                        f"Action: {scene.visual_prompt}. "
                        f"Overlay focus: {scene.overlay_text}"
                    ),
                }
            )
        return prompts

