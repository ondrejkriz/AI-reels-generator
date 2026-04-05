"""Platform-ready metadata generation for short-form publishing."""

from __future__ import annotations

from .models import MetadataBundle, ScriptParts


class MetadataGenerator:
    """Builds titles, descriptions and per-platform captions."""

    def build(self, topic: str, script: ScriptParts) -> MetadataBundle:
        short_title = f"{topic.title()}: {self._trim(script.payoff, 48)}"
        hook_title = self._trim(script.hook, 58)
        description = (
            f"{script.hook} {script.fact} {script.payoff} "
            "Faktický obsah před publikací zkontrolujte."
        )
        tags = [
            "vedelijsteze",
            "fakta",
            "reels",
            "shorts",
            "tiktokfacts",
            topic.lower().replace(" ", ""),
        ]
        captions = {
            "youtube_shorts": f"{hook_title}\n\n{script.payoff}\n#Shorts #VedelijsteZe #{topic.title().replace(' ', '')}",
            "tiktok": f"{hook_title} {script.payoff} Sleduj pro další fakta. #{topic.replace(' ', '')} #fakta #didyouknow",
            "instagram_reels": f"{hook_title}\n{script.explanation}\n.\n.\n.\n#{topic.replace(' ', '')} #reels #facts",
        }
        return MetadataBundle(
            title=short_title,
            hook_title=hook_title,
            description=description,
            tags=tags,
            captions=captions,
        )

    @staticmethod
    def _trim(text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        return text[: limit - 3].rstrip() + "..."

