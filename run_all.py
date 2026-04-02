"""
run_all.py - Run all demos and generate the final demo showcase page.
Usage: python scripts/run_all.py [--record] [--process] [--page-only]
"""

import sys
import os
import json
import argparse
import shutil

sys.path.insert(0, os.path.dirname(__file__))
from showcase_builder import build_showcase

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
ROOT_INDEX_PATH = os.path.join(BASE_DIR, "index.html")
VIDEO_DIR = os.path.join(BASE_DIR, "videos")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
LEGACY_OUTPUT_VIDEO_DIR = os.path.join(BASE_DIR, "output_videos")
TUTORIAL_PAGE_DIR = os.path.join(BASE_DIR, "tutorials")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# All demos
DEMOS = [
    {
        "module": "demo_screener",
        "name": "screener",
        "title": "Stock Research on Screener.in",
        "description": "Choose stocks with a repeatable Screener workflow: inspect Reliance first, then use the High Growth, High RoE, Low PE screen to shortlist and verify Ganesh Infra.",
        "prompt": "Go to screener.in and show how to choose stocks step by step: open Reliance Industries as the example company, review the key metrics, quarterly results, profit and loss, and balance sheet, then click Screens, clearly point at the High Growth, High RoE, Low PE card, open it, compare the results, and drill into Ganesh Infra.",
        "category": "Financial Literacy",
        "icon": "STK",
    },
    {
        "module": "demo_zoho_invoice",
        "name": "zoho_invoice",
        "title": "Create a GST Invoice on Zoho",
        "description": "Create a professional invoice with multiple line items, GST calculation, client details, and download as PDF.",
        "prompt": "Go to Zoho Invoice, create a new invoice for 'Acme Corp' with 3 line items including GST, preview and download as PDF",
        "category": "Business Operations",
        "icon": "INV",
    },
    {
        "module": "demo_tinkercad",
        "name": "tinkercad",
        "title": "3D Design in TinkerCAD",
        "description": "Design a 3D object by dragging shapes, resizing, combining, and exporting as STL for 3D printing.",
        "prompt": "Go to TinkerCAD, start a new design, create a simple phone stand using basic shapes, group them, and export as STL",
        "category": "Engineering & Design",
        "icon": "3D",
    },
    {
        "module": "demo_overpass",
        "name": "overpass_turbo",
        "title": "Query Geographic Data with Overpass Turbo",
        "description": "Find hospitals, EV charging stations, and schools in any city using plain English queries, then export as GeoJSON.",
        "prompt": "Go to overpass-turbo.eu, find all hospitals in Hyderabad, view on map, query EV charging stations, export as GeoJSON",
        "category": "Data & Research",
        "icon": "MAP",
    },
    {
        "module": "demo_mondula_form",
        "name": "mondula_form",
        "title": "Complete a Multi-Page Form on Mondula",
        "description": "Fill a real multi-step form with text fields, date inputs, radios, checkboxes, dropdowns, and final contact details.",
        "prompt": "Go to mondula.com/msf-demo, complete each page, fill at least 6 input fields, and reach the submit-ready final step.",
        "category": "Workflow Automation",
        "icon": "FORM",
    },
    {
        "module": "demo_indian_visa",
        "name": "indian_visa",
        "title": "Indian eVisa Form Walkthrough",
        "description": "Fill the Indian eVisa application start form with safe dummy data and stop before captcha submission.",
        "prompt": "Open indianvisaonline.gov.in eVisa form, enter fake applicant details, and stop safely at captcha.",
        "category": "Public Services",
        "icon": "VISA",
    },
    {
        "module": "demo_ebay",
        "name": "ebay_advanced",
        "title": "eBay Advanced Search Automation",
        "description": "Complete a real multi-input search form with keywords, price range, checkboxes, and submit.",
        "prompt": "Go to eBay advanced search, fill multiple fields, set filters, and run the search.",
        "category": "E-commerce",
        "icon": "SHOP",
    },
]


def selected_demos(selected_names: list[str] | None = None) -> list[dict]:
    """Return all demos or a user-selected subset by name."""
    if not selected_names:
        return DEMOS
    selected = set(selected_names)
    return [demo for demo in DEMOS if demo["name"] in selected]


def get_demo_runner(module):
    """Return the module's recording entry point."""
    for attr in ("run", "run_demo", "run_ebay_demo"):
        candidate = getattr(module, attr, None)
        if callable(candidate):
            return candidate
    raise AttributeError(
        f"Module '{module.__name__}' does not expose a supported runner function"
    )


def run_recordings(selected_names: list[str] | None = None):
    """Record all demos."""
    for demo in selected_demos(selected_names):
        print(f"\n{'#'*60}")
        print(f"  Recording: {demo['title']}")
        print(f"{'#'*60}")

        module = __import__(demo["module"])
        runner = get_demo_runner(module)
        runner()


def process_videos(selected_names: list[str] | None = None):
    """Post-process all recorded videos."""
    from video_processor import process_demo

    for demo in selected_demos(selected_names):
        process_demo(demo["name"])


def generate_narrations(selected_names: list[str] | None = None):
    """Generate audio narration for all demos."""
    from narration_generator import generate_narration

    for demo in selected_demos(selected_names):
        generate_narration(demo["name"])


def clean_generated_artifacts():
    """Remove generated demo media and derived files for a clean rerun."""
    print(f"\n{'='*60}")
    print("  Cleaning Generated Artifacts")
    print(f"{'='*60}\n")

    for directory in [VIDEO_DIR, SCREENSHOT_DIR, OUTPUT_DIR, LEGACY_OUTPUT_VIDEO_DIR, TUTORIAL_PAGE_DIR]:
        if not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
            continue

        for entry in os.listdir(directory):
            target = os.path.join(directory, entry)
            if os.path.isdir(target):
                shutil.rmtree(target)
            else:
                os.remove(target)

        print(f"Cleared: {directory}")


def build_demo_page():
    """Generate the final HTML demo showcase page."""
    return build_showcase(DEMOS)

    # Build demo cards HTML
    cards_html = ""
    for i, demo in enumerate(DEMOS):
        video_file = f"{demo['name']}_final.webm"
        video_path = os.path.join(OUTPUT_DIR, video_file)
        video_version = str(int(os.path.getmtime(video_path))) if os.path.exists(video_path) else "missing"
        video_src = f"output/{video_file}?v={video_version}"
        transcript_file = f"{demo['name']}_transcript.md"

        # Read transcript if available
        transcript_path = os.path.join(OUTPUT_DIR, transcript_file)
        transcript_html = ""
        if os.path.exists(transcript_path):
            with open(transcript_path, encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith("**Step"):
                        step_text = line.replace("**", "")
                        transcript_html += f'<div class="step-item">{step_text}</div>\n'
                    elif line.startswith("##"):
                        continue
                    elif line.startswith("- URL:"):
                        continue

        cards_html += f"""
        <div class="demo-card" id="demo-{i}">
            <div class="card-header">
                <span class="card-icon">{demo['icon']}</span>
                <div>
                    <span class="card-category">{demo['category']}</span>
                    <h2 class="card-title">{demo['title']}</h2>
                </div>
            </div>

            <p class="card-description">{demo['description']}</p>

            <div class="prompt-box">
                <span class="prompt-label">INPUT PROMPT:</span>
                <p class="prompt-text">{demo['prompt']}</p>
            </div>

            <div class="video-container">
                <video controls preload="metadata" poster="">
                    <source src="{video_src}" type="video/webm">
                    Your browser does not support the video tag.
                </video>
            </div>

            <div class="transcript-section">
                <h3 class="transcript-title" onclick="this.parentElement.classList.toggle('expanded')">
                    Step-by-Step Instructions
                    <span class="expand-icon">v</span>
                </h3>
                <div class="transcript-content">
                    {transcript_html if transcript_html else '<p class="no-transcript">Transcript will be generated after recording.</p>'}
                </div>
            </div>
        </div>
        """

    # Full HTML page
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Video Tutorial Generator - Demo Showcase</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0a0a1a;
            color: #e0e0e0;
            line-height: 1.6;
        }}

        .hero {{
            text-align: center;
            padding: 60px 20px 40px;
            background: linear-gradient(135deg, #0a0a2e 0%, #1a1a3e 50%, #0a0a2e 100%);
            border-bottom: 1px solid rgba(100, 120, 255, 0.2);
        }}

        .hero h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #6b8aff, #a78bfa, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 12px;
        }}

        .hero p {{
            font-size: 1.1rem;
            color: #8888aa;
            max-width: 700px;
            margin: 0 auto;
        }}

        .stats-bar {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 30px;
            flex-wrap: wrap;
        }}

        .stat {{
            text-align: center;
        }}

        .stat-number {{
            font-size: 2rem;
            font-weight: 700;
            color: #6b8aff;
        }}

        .stat-label {{
            font-size: 0.85rem;
            color: #6666aa;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
        }}

        .demo-card {{
            background: #12122a;
            border: 1px solid rgba(100, 120, 255, 0.15);
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 32px;
            transition: border-color 0.3s;
        }}

        .demo-card:hover {{
            border-color: rgba(100, 120, 255, 0.4);
        }}

        .card-header {{
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 16px;
        }}

        .card-icon {{
            font-size: 2.5rem;
        }}

        .card-category {{
            font-size: 0.75rem;
            color: #6b8aff;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-weight: 600;
        }}

        .card-title {{
            font-size: 1.5rem;
            font-weight: 600;
            color: #ffffff;
            margin-top: 4px;
        }}

        .card-description {{
            color: #9999bb;
            margin-bottom: 20px;
            font-size: 1rem;
        }}

        .prompt-box {{
            background: rgba(100, 120, 255, 0.08);
            border: 1px solid rgba(100, 120, 255, 0.2);
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 24px;
        }}

        .prompt-label {{
            font-size: 0.7rem;
            color: #6b8aff;
            font-weight: 700;
            letter-spacing: 2px;
        }}

        .prompt-text {{
            color: #ccccee;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            margin-top: 8px;
            line-height: 1.5;
        }}

        .video-container {{
            border-radius: 10px;
            overflow: hidden;
            background: #000;
            margin-bottom: 20px;
        }}

        .video-container video {{
            width: 100%;
            display: block;
        }}

        .transcript-section {{
            border-top: 1px solid rgba(100, 120, 255, 0.1);
            padding-top: 16px;
        }}

        .transcript-title {{
            font-size: 1rem;
            color: #8888bb;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
        }}

        .transcript-title:hover {{
            color: #aaaadd;
        }}

        .expand-icon {{
            transition: transform 0.3s;
            font-size: 0.8rem;
        }}

        .transcript-section.expanded .expand-icon {{
            transform: rotate(180deg);
        }}

        .transcript-content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.4s ease;
        }}

        .transcript-section.expanded .transcript-content {{
            max-height: 2000px;
        }}

        .step-item {{
            padding: 10px 16px;
            margin: 6px 0;
            background: rgba(100, 120, 255, 0.05);
            border-left: 3px solid #6b8aff;
            border-radius: 0 8px 8px 0;
            font-size: 0.9rem;
            color: #bbbbdd;
        }}

        .no-transcript {{
            color: #555577;
            font-style: italic;
            padding: 12px;
        }}

        .footer {{
            text-align: center;
            padding: 40px 20px;
            color: #444466;
            font-size: 0.85rem;
            border-top: 1px solid rgba(100, 120, 255, 0.1);
        }}

        @media (max-width: 600px) {{
            .hero h1 {{ font-size: 1.8rem; }}
            .demo-card {{ padding: 20px; }}
            .stats-bar {{ gap: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="hero">
        <h1>AI Video Tutorial Generator</h1>
        <p>
            Automated website tutorials created by an AI coding agent.
            Point it to any website, give it one prompt, and it generates
            a video walkthrough with captions, keyboard overlays, and narration.
        </p>
        <div class="stats-bar">
            <div class="stat">
                <div class="stat-number">{len(DEMOS)}</div>
                <div class="stat-label">Tutorials</div>
            </div>
            <div class="stat">
                <div class="stat-number">1</div>
                <div class="stat-label">Prompt Each</div>
            </div>
            <div class="stat">
                <div class="stat-number">&lt;2min</div>
                <div class="stat-label">Per Video</div>
            </div>
            <div class="stat">
                <div class="stat-number">0</div>
                <div class="stat-label">Manual Editing</div>
            </div>
        </div>
    </div>

    <div class="container">
        {cards_html}
    </div>

    <div class="footer">
        Built with Playwright + FFmpeg + Gemini Audio | AI Video Tutorial Generator
    </div>
</body>
</html>"""

    legacy_output_path = os.path.join(OUTPUT_DIR, "index.html")
    if os.path.exists(legacy_output_path):
        os.remove(legacy_output_path)

    with open(ROOT_INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Demo page generated: {ROOT_INDEX_PATH}")
    return ROOT_INDEX_PATH


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run all demos")
    parser.add_argument("--record", action="store_true", help="Record all demos")
    parser.add_argument("--process", action="store_true", help="Process recorded videos")
    parser.add_argument("--narrate", action="store_true", help="Generate narrations")
    parser.add_argument("--page-only", action="store_true", help="Only build the demo page")
    parser.add_argument("--clean", action="store_true", help="Delete generated demo artifacts before continuing")
    parser.add_argument("--all", action="store_true", help="Run everything")
    parser.add_argument(
        "--demo",
        action="append",
        choices=[demo["name"] for demo in DEMOS],
        help="Run only the named demo. Repeat the flag to select multiple demos.",
    )
    parser.add_argument("--list-demos", action="store_true", help="Print all available demo names and exit")

    args = parser.parse_args()

    if args.list_demos:
        print("Available demos:")
        for demo in DEMOS:
            print(f"- {demo['name']}: {demo['title']}")
        sys.exit(0)

    if args.clean:
        clean_generated_artifacts()

    if args.page_only:
        build_demo_page()
    elif args.all:
        run_recordings(args.demo)
        generate_narrations(args.demo)
        process_videos(args.demo)
        build_demo_page()
    else:
        if args.record:
            run_recordings(args.demo)
        if args.narrate:
            generate_narrations(args.demo)
        if args.process:
            process_videos(args.demo)

        # Always build the page
        build_demo_page()


