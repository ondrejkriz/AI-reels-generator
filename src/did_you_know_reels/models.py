"""Shared dataclasses used across the reel generation pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class TopicIdea:
    """Represents a candidate factual reel topic."""

    topic: str
    angle: str
    source_note: str
    confidence: float


@dataclass(slots=True)
class ScriptParts:
    """Holds the structured short-form script."""

    hook: str
    fact: str
    explanation: str
    payoff: str
    cta: str
    language: str = "cs"

    @property
    def full_script(self) -> str:
        return " ".join(
            [
                self.hook.strip(),
                self.fact.strip(),
                self.explanation.strip(),
                self.payoff.strip(),
                self.cta.strip(),
            ]
        ).strip()


@dataclass(slots=True)
class Scene:
    """A visual block in the final reel."""

    scene_number: int
    purpose: str
    narration: str
    overlay_text: str
    visual_prompt: str
    duration_seconds: float
    asset_hint: str


@dataclass(slots=True)
class ValidationResult:
    """Fact validation status and notes."""

    status: str
    confidence: float
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FactSource:
    """Represents an external fact source used during validation."""

    source_name: str
    source_title: str
    source_url: str
    summary: str
    retrieved_at: str
    language: str


@dataclass(slots=True)
class DraftScore:
    """Score breakdown for a generated reel."""

    overall: float
    hook: float
    brevity: float
    surprise: float
    duration: float
    readability: float
    diversity: float


@dataclass(slots=True)
class MetadataBundle:
    """Publishing metadata for each platform."""

    title: str
    hook_title: str
    description: str
    tags: list[str]
    captions: dict[str, str]


@dataclass(slots=True)
class ReelDraft:
    """The main persisted payload representing a reel draft."""

    draft_id: str
    topic: str
    niche: str
    idea: TopicIdea
    script: ScriptParts
    scenes: list[Scene]
    voiceover_text: str
    subtitles: str
    validation: ValidationResult
    sources: list[FactSource]
    metadata: MetadataBundle
    score: DraftScore
    output_root: str
    created_at: str
    provider_name: str
    dry_run: bool = False
    render_plan: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["script"]["full_script"] = self.script.full_script
        return payload

    def script_path(self) -> Path:
        return Path(self.output_root) / "scripts" / f"{self.draft_id}.json"
