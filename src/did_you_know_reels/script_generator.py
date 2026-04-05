"""Script generation and structure validation."""

from __future__ import annotations

from .models import ScriptParts, TopicIdea
from .providers import BaseLLMProvider


class ScriptGenerator:
    """Creates short, structured reel scripts."""

    def __init__(self, provider: BaseLLMProvider, cta: str) -> None:
        self.provider = provider
        self.cta = cta

    def generate(self, niche: str, idea: TopicIdea) -> ScriptParts:
        """Generate a structured script and validate its format."""

        script = self.provider.generate_script(niche, idea, self.cta)
        self.validate_structure(script)
        return script

    @staticmethod
    def validate_structure(script: ScriptParts) -> None:
        """Ensure the script contains all required sections and the right hook style."""

        missing = [
            key
            for key, value in {
                "hook": script.hook,
                "fact": script.fact,
                "explanation": script.explanation,
                "payoff": script.payoff,
                "cta": script.cta,
            }.items()
            if not value.strip()
        ]
        if missing:
            raise ValueError(f"Script is missing required parts: {', '.join(missing)}")

        normalized_hook = script.hook.strip().lower()
        if not (
            normalized_hook.startswith("věděli jste, že")
            or normalized_hook.startswith("vedeli jste, ze")
        ):
            raise ValueError("Hook must start with the required Czech opening phrase.")

        if not script.cta.strip().endswith("."):
            raise ValueError("CTA must be a complete sentence.")
