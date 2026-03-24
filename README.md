# AI Video Tutorial Generator

Automated website tutorial generator built with Playwright, FFmpeg, and optional voice narration.

It records browser walkthroughs, captures step screenshots, generates transcripts, builds final captioned WebM videos, and publishes a root-level `index.html` dashboard that plays videos from `output/`.

## Current Output Layout

- `index.html`
  Root dashboard page for local viewing or GitHub Pages style hosting.
- `output/*_final.webm`
  Final published demo videos.
- `output/*_transcript.md`
  Step-by-step transcript for each demo.
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

This clears generated artifacts, records all demos, generates narration, processes videos, and rebuilds the root `index.html`.

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

## Publishing Notes

- The dashboard is written to `index.html` at the repo root.
- Video paths inside the dashboard point to `output/*.webm`.
- Cache-busting query strings are added automatically when the page is rebuilt.
- If you want the dashboard on GitHub, commit `index.html`, the final `output/*_final.webm` files, and the `output/*_transcript.md` files.

## Git Ignore Behavior

The repo ignores:

- `.env`
- `videos/`
- `screenshots/`
- `output_videos/`
- intermediate output files such as compressed videos, captioned videos, timed videos, narration audio, and SRT files

The final publishable assets are intentionally left trackable:

- `index.html`
- `output/*_final.webm`
- `output/*_transcript.md`

## Implementation Notes

- Raw recordings are normalized to one canonical file per demo inside `videos/<demo>/<demo>.webm`.
- Caption timing is based on step text length instead of equal splits.
- Narration script text is aligned to the same step language used in captions.
- If narration is longer than the base video, the processor extends the video so caption timing and spoken audio can stay in sync.
