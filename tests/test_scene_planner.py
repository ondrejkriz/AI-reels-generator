from did_you_know_reels.models import ScriptParts
from did_you_know_reels.scene_planner import ScenePlanner


def test_scene_planner_creates_five_scenes() -> None:
    planner = ScenePlanner(default_scene_duration=4.0)
    script = ScriptParts(
        hook="Věděli jste, že lidské tělo slabě svítí?",
        fact="Buňky tvoří biofotony.",
        explanation="Oko je nevidí.",
        payoff="Takže technicky jemně záříte.",
        cta="Sleduj pro víc.",
    )

    scenes = planner.plan(script)

    assert len(scenes) == 5
    assert scenes[0].purpose == "hook"
    assert scenes[-1].purpose == "cta"
