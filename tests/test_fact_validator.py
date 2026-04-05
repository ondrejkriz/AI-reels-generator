from did_you_know_reels.fact_validator import FactValidator
from did_you_know_reels.models import FactSource, ScriptParts
from did_you_know_reels.providers import MockProvider


class StubWikiClient:
    def __init__(self, source: FactSource | None) -> None:
        self.source = source

    def fetch_source(self, query: str) -> FactSource | None:
        return self.source


def test_fact_validator_returns_sources_and_partial_validation() -> None:
    validator = FactValidator(
        provider=MockProvider(),
        fallback_status="needs_review",
        wikipedia_client=StubWikiClient(
            FactSource(
                source_name="wikipedia",
                source_title="Venuše",
                source_url="https://cs.wikipedia.org/wiki/Venu%C5%A1e",
                summary="Venuše je planeta, která se otáčí velmi pomalu a opačným směrem.",
                retrieved_at="2026-04-02T00:00:00+00:00",
                language="cs",
            )
        ),
    )
    script = ScriptParts(
        hook="Věděli jste, že na Venuši trvá jeden den déle než jeden rok?",
        fact="Planeta se otáčí tak pomalu, že jedna otočka zabere víc času než oběh kolem Slunce.",
        explanation="To je důvod, proč působí tak zvláštně.",
        payoff="A ještě divnější je, že se točí opačným směrem.",
        cta="Sleduj pro víc.",
    )

    result, sources = validator.validate(script, "space")

    assert result.status == "partially_validated"
    assert sources[0].source_name == "wikipedia"


def test_fact_validator_falls_back_when_source_missing() -> None:
    validator = FactValidator(
        provider=MockProvider(),
        fallback_status="needs_review",
        wikipedia_client=StubWikiClient(None),
    )
    script = ScriptParts(
        hook="Věděli jste, že chobotnice má tři srdce?",
        fact="To je krátký fakt.",
        explanation="Tohle je vysvětlení.",
        payoff="A to je překvapivé.",
        cta="Sleduj pro víc.",
    )

    result, sources = validator.validate(script, "animals")

    assert result.status == "needs_review"
    assert sources == []


def test_fact_validator_ignores_disambiguation_summary() -> None:
    validator = FactValidator(
        provider=MockProvider(),
        fallback_status="needs_review",
        wikipedia_client=StubWikiClient(
            FactSource(
                source_name="wikipedia",
                source_title="Animals",
                source_url="https://cs.wikipedia.org/wiki/Animals",
                summary="Pojem Animals může mít více významů.",
                retrieved_at="2026-04-02T00:00:00+00:00",
                language="cs",
            )
        ),
    )
    script = ScriptParts(
        hook="Věděli jste, že chobotnice má tři srdce?",
        fact="To je krátký fakt.",
        explanation="Tohle je vysvětlení.",
        payoff="A to je překvapivé.",
        cta="Sleduj pro víc.",
    )

    result, sources = validator.validate(script, "animals")

    assert result.status == "needs_review"
    assert sources[0].source_title == "Animals"
