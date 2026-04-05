import pytest

from did_you_know_reels.models import ScriptParts
from did_you_know_reels.script_generator import ScriptGenerator


def test_validate_structure_accepts_valid_script() -> None:
    script = ScriptParts(
        hook="Věděli jste, že chobotnice má tři srdce?",
        fact="Tohle je krátký fakt.",
        explanation="Tohle je vysvětlení.",
        payoff="A právě to z ní dělá zvláštního tvora.",
        cta="Sleduj pro víc.",
    )

    ScriptGenerator.validate_structure(script)


def test_validate_structure_rejects_bad_hook() -> None:
    script = ScriptParts(
        hook="Možná jste netušili, že...",
        fact="Tohle je krátký fakt.",
        explanation="Tohle je vysvětlení.",
        payoff="Tohle je payoff.",
        cta="Sleduj pro víc.",
    )

    with pytest.raises(ValueError):
        ScriptGenerator.validate_structure(script)
