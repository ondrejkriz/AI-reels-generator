"""Script-to-scene conversion for short vertical reels."""

from __future__ import annotations

from .models import Scene, ScriptParts


class ScenePlanner:
    """Splits a short script into visually distinct scenes."""

    def __init__(self, default_scene_duration: float) -> None:
        self.default_scene_duration = default_scene_duration

    def plan(self, script: ScriptParts) -> list[Scene]:
        scene_specs = [
            ("hook", script.hook, script.hook, "dynamic title card with bold kinetic text"),
            ("fact", script.fact, self._shorten(script.fact), "close-up visual metaphor illustrating the fact"),
            ("explanation", script.explanation, self._shorten(script.explanation), "clean infographic style motion background"),
            ("payoff", script.payoff, self._shorten(script.payoff), "surprising reveal with punchy contrast"),
            ("cta", script.cta, self._shorten(script.cta), "end card with follow prompt and branded framing"),
        ]
        scenes: list[Scene] = []
        for index, (purpose, narration, overlay, visual_prompt) in enumerate(scene_specs, start=1):
            duration = self.default_scene_duration if purpose != "cta" else max(3.0, self.default_scene_duration - 1.0)
            scenes.append(
                Scene(
                    scene_number=index,
                    purpose=purpose,
                    narration=narration,
                    overlay_text=overlay,
                    visual_prompt=visual_prompt,
                    duration_seconds=duration,
                    asset_hint=f"placeholder_or_ai_generated_{purpose}",
                )
            )
        return scenes

    @staticmethod
    def _shorten(text: str, max_words: int = 9) -> str:
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]) + "..."
