"""LLM provider abstraction with mock and optional OpenAI integration."""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
import logging
import random
from typing import Any

from .models import ScriptParts, TopicIdea, ValidationResult

LOGGER = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Base interface for topic, script and validation generation."""

    name = "base"

    @abstractmethod
    def generate_topic(self, niche: str) -> TopicIdea:
        """Return a topic idea for the requested niche."""

    @abstractmethod
    def generate_script(self, niche: str, topic: TopicIdea, cta: str) -> ScriptParts:
        """Return a structured reel script."""

    @abstractmethod
    def validate_fact(self, script: ScriptParts) -> ValidationResult:
        """Return fact validation metadata."""


class MockProvider(BaseLLMProvider):
    """Deterministic local fallback for offline or dry-run usage."""

    name = "mock"

    def __init__(self, seed: int = 42) -> None:
        self.random = random.Random(seed)

    def generate_topic(self, niche: str) -> TopicIdea:
        angle_map = {
            "animals": "zvíře s nečekanou schopností",
            "history": "historická kuriozita s moderním dopadem",
            "science": "vědecký jev, který zní skoro nemožně",
            "space": "vesmírný detail, který působí neskutečně",
            "bizarre facts": "bizarní fakt, který je ale reálný",
            "dark facts": "temnější detail s edukativním rámcem",
        }
        angle = angle_map.get(niche.lower(), "překvapivý fakt, který zaujme během prvních 2 sekund")
        return TopicIdea(topic=niche, angle=angle, source_note="mock_provider_seeded", confidence=0.62)

    def generate_script(self, niche: str, topic: TopicIdea, cta: str) -> ScriptParts:
        templates = {
            "space": ScriptParts(
                hook="Věděli jste, že na Venuši trvá jeden den déle než jeden rok?",
                fact="Planeta se otáčí tak pomalu, že jedna otočka kolem osy zabere víc času než oběh kolem Slunce.",
                explanation="To znamená, že kdybyste tam stáli na povrchu, čekali byste na další východ Slunce extrémně dlouho.",
                payoff="Ještě zvláštnější je, že Venuše se navíc otáčí opačným směrem než většina planet.",
                cta=cta,
            ),
            "animals": ScriptParts(
                hook="Věděli jste, že chobotnice má tři srdce?",
                fact="Dvě srdce pumpují krev do žaber a třetí zásobuje zbytek těla.",
                explanation="Když plave, hlavní srdce se může na chvíli zastavit, a proto se rychle unaví.",
                payoff="Právě proto někdy vypadá jako dokonalý mimozemšťan z našeho oceánu.",
                cta=cta,
            ),
            "history": ScriptParts(
                hook="Věděli jste, že nejkratší válka v historii trvala méně než hodinu?",
                fact="Válka mezi Británií a Zanzibarem v roce 1896 skončila přibližně po 38 minutách.",
                explanation="Britové rychle zničili odpor a konflikt skončil dřív, než byste dokoukali jeden seriálový díl.",
                payoff="Nejdivnější je, že některé dnešní porady trvají déle než celá tahle válka.",
                cta=cta,
            ),
            "science": ScriptParts(
                hook="Věděli jste, že lidské tělo slabě svítí?",
                fact="Naše buňky vytvářejí extrémně slabé biofotony během chemických procesů.",
                explanation="Oko je nevidí, protože jsou mnohem slabší než běžné světlo kolem nás.",
                payoff="Technicky vzato tedy ve tmě opravdu záříte, jen moc jemně na to, abyste si toho všimli.",
                cta=cta,
            ),
        }
        default_script = ScriptParts(
            hook=f"Věděli jste, že jeden z nejzvláštnějších faktů je, jak {niche.lower()} umí překvapit?",
            fact=f"U tématu {niche.lower()} často existuje detail, který běžně nezazní, ale okamžitě zaujme.",
            explanation="Krátký reel funguje nejlépe, když vysvětlí pointu rychle, srozumitelně a bez omáčky.",
            payoff="A právě tenhle kontrast mezi jednoduchostí a překvapením dělá z faktu silný hook.",
            cta=cta,
        )
        return templates.get(niche.lower(), default_script)

    def validate_fact(self, script: ScriptParts) -> ValidationResult:
        return ValidationResult(
            status="needs_review",
            confidence=0.45,
            notes=[
                "Mock provider does not verify external sources.",
                "Human review required before publishing factual claims.",
            ],
        )


class OpenAIProvider(BaseLLMProvider):
    """Optional OpenAI-backed provider with graceful fallback expectations."""

    name = "openai"

    def __init__(self, model: str, api_key: str) -> None:
        self.model = model
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError("Install the openai extra to use OpenAIProvider.") from exc
        self.client = OpenAI(api_key=api_key)

    def _json_completion(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
        )
        return json.loads(response.output_text)

    def generate_topic(self, niche: str) -> TopicIdea:
        payload = self._json_completion(
            system_prompt="You create safe, factual did-you-know short-form content ideas in Czech.",
            user_prompt=f"Return JSON with keys topic, angle, source_note, confidence for niche: {niche}",
        )
        return TopicIdea(**payload)

    def generate_script(self, niche: str, topic: TopicIdea, cta: str) -> ScriptParts:
        payload = self._json_completion(
            system_prompt="You write short, engaging Czech reel scripts.",
            user_prompt=(
                "Return JSON with keys hook, fact, explanation, payoff, cta. "
                f"Niche: {niche}. Topic angle: {topic.angle}. CTA: {cta}"
            ),
        )
        return ScriptParts(**payload)

    def validate_fact(self, script: ScriptParts) -> ValidationResult:
        payload = self._json_completion(
            system_prompt="You are a careful fact consistency checker.",
            user_prompt=(
                "Assess whether this short script sounds factually consistent. "
                "Return JSON with keys status, confidence, notes. "
                f"Script: {script.full_script}"
            ),
        )
        return ValidationResult(**payload)


def build_provider(config: dict[str, Any]) -> BaseLLMProvider:
    """Create the configured provider and fall back to mock on failure."""

    provider_name = str(config.get("default", "mock")).lower()
    if provider_name == "openai":
        try:
            return OpenAIProvider(
                model=str(config.get("openai_model", "gpt-4.1-mini")),
                api_key=str(config.get("openai_api_key", "")),
            )
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("OpenAI provider unavailable, falling back to mock: %s", exc)
    return MockProvider()
