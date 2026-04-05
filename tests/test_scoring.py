from did_you_know_reels.models import Scene, ScriptParts
from did_you_know_reels.scoring import DraftScorer


def test_scoring_returns_weighted_score() -> None:
    scorer = DraftScorer(
        {
            "hook_weight": 0.25,
            "brevity_weight": 0.15,
            "surprise_weight": 0.2,
            "duration_weight": 0.15,
            "readability_weight": 0.1,
            "scene_diversity_weight": 0.15,
            "target_word_count_min": 35,
            "target_word_count_max": 85,
        }
    )
    script = ScriptParts(
        hook="Věděli jste, že Venuše má delší den než rok?",
        fact="Otáčí se velmi pomalu a to je zvláštní.",
        explanation="Jedna otočka zabere víc času než oběh kolem Slunce.",
        payoff="A ještě divnější je, že se točí opačně než většina planet.",
        cta="Sleduj pro víc.",
    )
    scenes = [
        Scene(i, purpose, "text", "overlay", "prompt", 4.0, "placeholder")
        for i, purpose in enumerate(["hook", "fact", "explanation", "payoff", "cta"], start=1)
    ]

    score = scorer.score(script, scenes, "titulek jedna.\ntitulek dvě.")

    assert score.overall > 0
    assert score.hook >= 90
    assert score.diversity == 100.0

