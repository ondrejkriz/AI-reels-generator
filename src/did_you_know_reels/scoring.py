"""Draft scoring tuned by configurable weights."""

from __future__ import annotations

from .models import DraftScore, Scene, ScriptParts
from .utils import average_sentence_length


class DraftScorer:
    """Scores hooks, brevity and scene quality."""

    def __init__(self, scoring_config: dict[str, float | int]) -> None:
        self.config = scoring_config

    def score(self, script: ScriptParts, scenes: list[Scene], subtitles: str) -> DraftScore:
        words = script.full_script.split()
        word_count = len(words)
        min_words = int(self.config["target_word_count_min"])
        max_words = int(self.config["target_word_count_max"])

        hook_score = 1.0 if script.hook.startswith("Věděli jste, že") else 0.45
        brevity_score = self._range_score(word_count, min_words, max_words)
        surprise_score = 1.0 if any(word in script.payoff.lower() for word in ["nej", "opač", "překvap", "divn", "zvláštn"]) else 0.6
        total_duration = sum(scene.duration_seconds for scene in scenes)
        duration_score = self._range_score(total_duration, 15, 35)
        readability_score = 1.0 if average_sentence_length(subtitles) <= 14 else 0.7
        unique_purposes = len({scene.purpose for scene in scenes})
        diversity_score = min(1.0, unique_purposes / max(1, len(scenes)))

        overall = (
            hook_score * float(self.config["hook_weight"])
            + brevity_score * float(self.config["brevity_weight"])
            + surprise_score * float(self.config["surprise_weight"])
            + duration_score * float(self.config["duration_weight"])
            + readability_score * float(self.config["readability_weight"])
            + diversity_score * float(self.config["scene_diversity_weight"])
        )
        return DraftScore(
            overall=round(overall * 100, 2),
            hook=round(hook_score * 100, 2),
            brevity=round(brevity_score * 100, 2),
            surprise=round(surprise_score * 100, 2),
            duration=round(duration_score * 100, 2),
            readability=round(readability_score * 100, 2),
            diversity=round(diversity_score * 100, 2),
        )

    @staticmethod
    def _range_score(value: float, minimum: float, maximum: float) -> float:
        if minimum <= value <= maximum:
            return 1.0
        if value < minimum:
            return max(0.0, 1.0 - ((minimum - value) / max(minimum, 1)))
        return max(0.0, 1.0 - ((value - maximum) / max(maximum, 1)))

