"""Voiceover text preparation and local TTS synthesis."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess

from .models import Scene
from .utils import ensure_directory


class VoiceoverGenerator:
    """Builds narration text and optionally synthesizes local speech audio."""

    def __init__(self, voice_name: str = "", rate: int = 0, volume: int = 100) -> None:
        self.voice_name = voice_name
        self.rate = rate
        self.volume = volume

    def build(self, scenes: list[Scene]) -> str:
        """Flatten scene narration into a TTS-ready script."""

        return "\n".join(self._pace_line(scene.narration, scene.purpose) for scene in scenes)

    def synthesize(self, text: str, output_path: str | Path, dry_run: bool = False) -> str | None:
        """Generate a WAV voiceover using the built-in Windows speech engine."""

        if dry_run:
            return None

        target = Path(output_path)
        ensure_directory(target.parent)

        escaped_path = str(target.resolve()).replace("'", "''")
        escaped_text = text.replace("'", "''")
        escaped_voice = self.voice_name.replace("'", "''")

        script_lines = [
            "$ErrorActionPreference='Stop'",
            "$voice = New-Object -ComObject SAPI.SpVoice",
            "$stream = New-Object -ComObject SAPI.SpFileStream",
            f"$stream.Open('{escaped_path}', 3, $false)",
            "$voice.AudioOutputStream = $stream",
            f"$voice.Volume = {self.volume}",
            f"$voice.Rate = {self.rate}",
        ]
        if escaped_voice:
            script_lines.append(
                f"$token = $voice.GetVoices() | Where-Object {{ $_.GetDescription() -eq '{escaped_voice}' }} | Select-Object -First 1"
            )
            script_lines.append("if ($token) { $voice.Voice = $token }")
        script_lines.extend(
            [
                f"$voice.Speak('{escaped_text}') | Out-Null",
                "$stream.Close()",
            ]
        )

        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", "; ".join(script_lines)],
            check=True,
            capture_output=True,
            text=True,
        )
        return str(target)

    @staticmethod
    def _pace_line(text: str, purpose: str) -> str:
        """Add light pacing hints so local TTS sounds less flat."""

        cleaned = text.strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        if purpose == "hook":
            return cleaned.replace("?", "...?")
        if purpose == "payoff":
            return cleaned + " ..."
        if purpose == "cta":
            return cleaned.replace(".", " ...")
        return cleaned
