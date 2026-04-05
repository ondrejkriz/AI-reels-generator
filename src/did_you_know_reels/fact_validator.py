"""Fact validation layer with explicit review states."""

from __future__ import annotations

import re

from .models import FactSource, ScriptParts, ValidationResult
from .providers import BaseLLMProvider
from .wikipedia_client import WikipediaClient


class FactValidator:
    """Runs fact consistency checks via the provider."""

    def __init__(
        self,
        provider: BaseLLMProvider,
        fallback_status: str,
        wikipedia_client: WikipediaClient | None = None,
    ) -> None:
        self.provider = provider
        self.fallback_status = fallback_status
        self.wikipedia_client = wikipedia_client

    def validate(self, script: ScriptParts, topic: str) -> tuple[ValidationResult, list[FactSource]]:
        """Validate a script and enrich the result with source metadata when available."""

        result = self.provider.validate_fact(script)
        sources: list[FactSource] = []

        if self.wikipedia_client:
            source = self.wikipedia_client.fetch_source(topic)
            if source:
                sources.append(source)
                overlap = self._summary_overlap(script.full_script, source.summary)
                is_disambiguation = "může mít více významů" in source.summary.lower()
                result.notes.append(f"Wikipedia source matched: {source.source_title}")
                if is_disambiguation:
                    result.notes.append("Wikipedia result looks like a disambiguation page and was not used as validation.")
                elif result.status != "validated":
                    if overlap >= 2:
                        result.status = "partially_validated"
                        result.confidence = max(result.confidence, 0.68)
                    else:
                        result.status = result.status or self.fallback_status
            else:
                result.notes.append("Wikipedia source was not found or could not be fetched.")

        if not result.status:
            result.status = self.fallback_status
        return result, sources

    @staticmethod
    def _summary_overlap(script_text: str, summary_text: str) -> int:
        """Estimate if script and source summary talk about the same concept."""

        token_pattern = re.compile(r"[a-zA-ZÀ-ž0-9]{4,}")
        script_tokens = {token.lower() for token in token_pattern.findall(script_text)}
        summary_tokens = {token.lower() for token in token_pattern.findall(summary_text)}
        stop_words = {
            "který",
            "která",
            "které",
            "jeden",
            "jedna",
            "proto",
            "protože",
            "there",
            "with",
            "from",
        }
        return len((script_tokens - stop_words) & (summary_tokens - stop_words))
