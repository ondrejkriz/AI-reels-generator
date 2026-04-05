from did_you_know_reels.providers import MockProvider, build_provider


def test_build_provider_falls_back_to_mock_without_api_key() -> None:
    provider = build_provider({"default": "openai", "openai_model": "gpt-4.1-mini", "openai_api_key": ""})
    assert provider.name == "mock"


def test_mock_provider_returns_review_status() -> None:
    provider = MockProvider()
    topic = provider.generate_topic("space")
    script = provider.generate_script("space", topic, "Sleduj pro víc.")
    validation = provider.validate_fact(script)

    assert validation.status == "needs_review"
    assert validation.confidence < 0.6
