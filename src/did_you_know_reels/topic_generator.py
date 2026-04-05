"""Topic generation service."""

from __future__ import annotations

from .models import TopicIdea
from .providers import BaseLLMProvider


class TopicGenerator:
    """Generates candidate topic ideas for the requested niche."""

    def __init__(self, provider: BaseLLMProvider) -> None:
        self.provider = provider

    def generate(self, niche: str) -> TopicIdea:
        return self.provider.generate_topic(niche)

