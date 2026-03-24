# AI Video Tutorial Generator

Automated website tutorial video generator using Playwright.

## Setup

```bash
# Install Python dependencies
pip install playwright --break-system-packages
playwright install chromium

# Install FFmpeg (for video post-processing)
sudo apt install ffmpeg -y

# Install Google Generative AI (for voice narration)
pip install google-generativeai --break-system-packages
```

## Project Structure

```
video-tutorial-generator/
├── scripts/
│   ├── common.py              # Shared utilities (click indicators, overlays, logging)
│   ├── video_processor.py     # FFmpeg post-processing (captions, compression)
│   ├── narration_generator.py # Gemini audio narration
│   ├── demo_screener.py       # Screener.in stock research
│   ├── demo_zoho_invoice.py   # Zoho Invoice creation
│   ├── demo_tinkercad.py      # TinkerCAD 3D design
│   ├── demo_overpass.py       # Overpass Turbo geo queries
│   └── run_all.py             # Run all demos and build final page
├── templates/
│   └── demo_page.html         # Final demo page template
├── videos/                    # Raw recorded videos
├── screenshots/               # Step screenshots
└── output/                    # Final processed videos + demo page
```

## Usage

```bash
# Run a single demo
python scripts/demo_screener.py

# Run all demos and generate the demo page
python scripts/run_all.py

# Process raw video with captions
python scripts/video_processor.py --input videos/screener_raw.webm --steps screenshots/screener_steps.json --output output/screener_final.webm
```

## Demo Websites

| # | Website | Category | Login Required |
|---|---|---|---|
| 1 | Screener.in | Stock Analysis | No |
| 2 | Zoho Invoice | Business Invoicing | Throwaway email |
| 3 | TinkerCAD | 3D Design | Guest mode |
| 4 | Overpass Turbo | Geographic Data | No |

## Video Specs (per Anand's requirements)
- Duration: 10-30 seconds (max 2 min)
- FPS: 3-5
- CRF: 55+
- Format: WebM
- Includes: Click indicators, keyboard overlays, captions, audio narration
