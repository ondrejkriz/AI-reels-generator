from did_you_know_reels.metadata_generator import MetadataGenerator
from did_you_know_reels.models import ScriptParts


def test_metadata_generator_builds_platform_captions() -> None:
    generator = MetadataGenerator()
    script = ScriptParts(
        hook="Věděli jste, že Venuše má delší den než rok?",
        fact="Otáčí se extrémně pomalu.",
        explanation="Jedna otočka trvá déle než oběh.",
        payoff="A navíc se točí opačně než většina planet.",
        cta="Sleduj pro víc.",
    )

    metadata = generator.build("space", script)

    assert metadata.title
    assert "youtube_shorts" in metadata.captions
    assert "tiktok" in metadata.captions
    assert "instagram_reels" in metadata.captions
