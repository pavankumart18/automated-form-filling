# AI Video Tutorial Generator

Automated website tutorial generator built with Playwright, FFmpeg, and optional voice narration.

It records browser walkthroughs, captures step screenshots, generates transcripts, builds final captioned WebM videos, and now publishes both a root-level `index.html` card gallery and separate `tutorials/*.html` detail pages with screenshots, narration beats, and reproducibility metadata.

## Current Output Layout

- `index.html`
  Root card gallery for local viewing or GitHub Pages style hosting.
- `tutorials/*.html`
  One detail page per automation demo with screenshots, prompt, rerun commands, and validation notes.
- `output/*_final.webm`
  Final published demo videos.
- `output/*_transcript.md`
  Step-by-step transcript for each demo.
- `output/*_manifest.json`
  Reproducibility manifest with commands, toolchain, counts, and step metadata.
- `output/*_narration_beats.json`
  Story-first narration beats with suggested pause timings.
- `output/screenshots/<demo>/step_*.png`
  Publishable screenshot copies used by the detail pages.
- `videos/`
  Raw recordings used during processing.
- `screenshots/`
  Per-step screenshots and step JSON metadata.

## Included Demos

1. Screener.in stock research
2. Zoho Invoice walkthrough
3. TinkerCAD learning flow
4. Overpass Turbo geographic queries
5. Mondula multi-step form
6. Indian eVisa start form
7. eBay advanced search

## Setup

### Python packages

```bash
pip install playwright python-dotenv google-genai gtts
playwright install chromium
```

### FFmpeg

Install FFmpeg and make sure both `ffmpeg` and `ffprobe` are available on `PATH`.

### Environment variables

Create a local `.env` file:

```env
GEMINI_API_KEY=your_key_here
GEMINI_TTS_MODEL=gemini-2.5-flash-preview-tts
GEMINI_VOICE_NAME=charon
```

Notes:

- `.env` is ignored by `.gitignore`.
- Narration tries Gemini TTS first.
- If Gemini TTS is unavailable or quota-limited, the project can fall back to `gTTS` if installed.

## Main Commands

### Run everything from scratch

```bash
python run_all.py --clean --all
```

This clears generated artifacts, records all demos, generates narration, processes videos, and rebuilds the root `index.html` plus all detail pages in `tutorials/`.

### Run one demo end-to-end

```bash
python run_all.py --demo screener --record --narrate --process
```

This is the fastest reproducible command when you only want to refresh one workflow.

### List available demos

```bash
python run_all.py --list-demos
```

### Rebuild only the dashboard page

```bash
python run_all.py --page-only
```

### Record demos only

```bash
python run_all.py --record
```

### Generate narration only

```bash
python run_all.py --narrate
```

### Process videos only

```bash
python run_all.py --process
```

### Run one narration job

```bash
python narration_generator.py screener
```

### Process one demo

```bash
python video_processor.py screener
```

## Per-Demo Reproducibility

Every generated detail page now includes:

- the exact input prompt
- the Python module used for capture
- the rerun commands for record, narration, process, and page rebuild
- the published screenshots tied to each logged step
- validation checks that compare screenshots, transcript counts, narration beats, and final video assets

## Publishing Notes

- The dashboard is written to `index.html` at the repo root.
- Detail pages are written to `tutorials/<demo>.html`.
- Video paths inside the dashboard point to `output/*.webm`.
- Cache-busting query strings are added automatically when the page is rebuilt.
- If you want the dashboard on GitHub, commit `index.html`, `tutorials/`, the final `output/*_final.webm` files, `output/*_transcript.md`, `output/*_manifest.json`, `output/*_narration_beats.json`, and `output/screenshots/`.

## Git Ignore Behavior

The repo ignores:

- `.env`
- `videos/`
- `screenshots/`
- `output_videos/`
- intermediate output files such as compressed videos, captioned videos, timed videos, narration audio, and SRT files

The final publishable assets are intentionally left trackable:

- `index.html`
- `tutorials/`
- `output/*_final.webm`
- `output/*_transcript.md`
- `output/*_manifest.json`
- `output/*_narration_beats.json`
- `output/screenshots/`

## Implementation Notes

- Raw recordings are normalized to one canonical file per demo inside `videos/<demo>/<demo>.webm`.
- Caption timing is based on step text length instead of equal splits.
- Narration is generated from structured step metadata, then rewritten into shorter story-first beats with built-in pause suggestions.
- If narration is longer than the base video, the processor extends the video so caption timing and spoken audio can stay in sync.
- The showcase build validates step counts across screenshots, transcripts, narration beats, and final pages so UI mismatches surface during generation instead of review.
