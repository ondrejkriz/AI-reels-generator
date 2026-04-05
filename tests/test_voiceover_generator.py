from pathlib import Path

from did_you_know_reels.models import Scene
from did_you_know_reels.voiceover_generator import VoiceoverGenerator


def test_voiceover_generator_builds_multiline_script() -> None:
    generator = VoiceoverGenerator()
    scenes = [
        Scene(1, "hook", "Line one", "Overlay one", "Prompt one", 4.0, "placeholder"),
        Scene(2, "fact", "Line two", "Overlay two", "Prompt two", 4.0, "placeholder"),
    ]

    voiceover_text = generator.build(scenes)

    assert voiceover_text == "Line one\nLine two"


def test_voiceover_generator_skips_audio_synthesis_in_dry_run(tmp_path: Path) -> None:
    generator = VoiceoverGenerator()

    result = generator.synthesize("Test voiceover", tmp_path / "voice.wav", dry_run=True)

    assert result is None
    assert not (tmp_path / "voice.wav").exists()
