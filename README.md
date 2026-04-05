# did-you-know-reels-generator

Production-friendly MVP for generating original vertical "Did you know...?" short videos for YouTube Shorts, TikTok, and Instagram Reels.

The project is designed as a local-first, API-optional pipeline. It can run in `dry-run` mode without external API keys and still produce scripts, scene plans, prompts, subtitles, metadata, and JSON reports.

## What The Project Does

The pipeline can:

1. generate a topic angle for a short factual reel,
2. write a short viral-friendly script,
3. split the script into visually distinct scenes,
4. build prompts for video or image generation,
5. prepare voiceover text,
6. generate subtitles,
7. compose a final 9:16 video with FFmpeg,
8. save metadata, scores, validation status, and a structured report.

It does not scrape third-party videos, reupload other creators' content, bypass copyright, or automate platform uploads.

## Core Features

- Python 3.11+
- modular architecture
- CLI interface
- configuration via `.env` and `config.yaml`
- structured logging
- `dry-run` mode
- pytest-based test suite
- type hints across modules
- FFmpeg-based render pipeline
- AI provider abstraction with a working fallback when no API key is available
- fact validation layer with Wikipedia lookup support
- placeholder rendering workflow when premium assets or external generation APIs are unavailable

## Repository Layout

```text
src/did_you_know_reels/
tests/
examples/
output/
prompts/
configs/
```

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .[dev]
```

If you want to experiment with an OpenAI-backed provider:

```bash
pip install -e .[dev,openai]
```

## FFmpeg Installation

Install FFmpeg and make sure `ffmpeg.exe` is available in your `PATH`.

Quick verification:

```bash
ffmpeg -version
```

If FFmpeg is not on `PATH`, set it explicitly in `.env`:

```env
FFMPEG_BINARY=ffmpeg
```

or:

```env
FFMPEG_BINARY=C:\path\to\ffmpeg.exe
```

## Environment Setup

Create a local environment file:

```bash
copy .env.example .env
```

Example:

```env
APP_ENV=development
LOG_LEVEL=INFO
LLM_PROVIDER=mock
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
FACT_VALIDATION_STRICT=false
FFMPEG_BINARY=ffmpeg
```

## Fallback Behavior Without API Keys

The project remains usable without external API access:

- `MockProvider` is used automatically when no API key is available.
- outputs are marked as `needs_review` unless external validation succeeds
- script, scenes, subtitles, prompts, metadata, and reports are still generated
- if FFmpeg is missing, the project writes a `render_plan.json` instead of crashing
- if external video generation is unavailable, placeholder scenes are rendered instead

## CLI Usage

Generate one draft:

```bash
python -m did_you_know_reels generate --topic "space" --output ./output
```

Render a final video from an existing draft:

```bash
python -m did_you_know_reels render --input ./output/scripts/space_001.json --output ./output
```

Run the full pipeline:

```bash
python -m did_you_know_reels run --topic "animals" --output ./output
```

Generate multiple variants:

```bash
python -m did_you_know_reels run --topic "history" --count 5 --output ./output
```

Run in dry mode:

```bash
python -m did_you_know_reels run --topic "science" --dry-run --output ./output
```

## Example `config.yaml`

```yaml
app:
  language: "cs"
  default_output_dir: "./output"
  log_file: "./logs/app.log"
  max_duration_seconds: 35
  min_duration_seconds: 15

provider:
  default: "mock"

video:
  width: 1080
  height: 1920
  fps: 30

scoring:
  hook_weight: 0.25
  brevity_weight: 0.15
  surprise_weight: 0.20

content:
  cta: "Sleduj pro vic."

sources:
  wikipedia:
    enabled: true
    language: "cs"
```

## Output Structure

The pipeline writes artifacts into:

- `output/scripts/*.json`
- `output/scenes/*.json`
- `output/subtitles/*.srt`
- `output/voiceover/*.txt` and optional `.wav`
- `output/prompts/*.json`
- `output/videos/*.mp4`
- `output/metadata/*.json`
- `output/reports/*.json`
- `logs/app.log`

## Fact Validation

The project includes a validation layer:

- when a supporting source is available, the draft may be marked `validated` or `partially_validated`
- when validation is unavailable or inconclusive, the draft is marked `needs_review`
- each reel report stores confidence information and validation notes
- Wikipedia can be used as a lightweight source lookup for MVP validation

Important: factual outputs should always be reviewed by a human before publishing.

## Current Limitations

- no platform auto-upload
- no scraping of third-party videos
- no copyright circumvention workflows
- local TTS quality depends on the available Windows voice
- video visuals remain placeholder-first unless you plug in better assets or generation providers
- factual validation is still a lightweight MVP layer and should not be treated as publication-grade verification

## Safety Notice

This project is intended for generating original AI-first content from prompts, public-domain or properly licensed assets, and your own inputs.

It is not intended for copyright infringement, scraping, or bypassing platform rules.

## Running The MVP

Minimal local run without external API keys:

```bash
copy .env.example .env
python -m did_you_know_reels run --topic "space" --dry-run --output ./output
```

If FFmpeg is installed and available:

```bash
python -m did_you_know_reels run --topic "space" --output ./output
```

## Tests

The MVP includes tests for:

- config loading
- script structure validation
- scene planning
- metadata generation
- scoring
- provider fallback behavior
- pipeline fallback behavior
- fact validation helpers

Run tests with:

```bash
pytest
```

## Next Steps

- integrate a stronger TTS provider
- add optional AI image and video generation providers
- improve factual validation with more reliable sources
- add richer visual templates and motion design
- expand platform-specific caption and export presets
