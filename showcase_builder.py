"""
showcase_builder.py - Build the portfolio-style tutorial showcase.
"""

import html
import json
import os
import shutil
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
ROOT_INDEX_PATH = os.path.join(BASE_DIR, "index.html")
DETAIL_DIR = os.path.join(BASE_DIR, "tutorials")
PUBLISHED_SCREENSHOT_DIR = os.path.join(OUTPUT_DIR, "screenshots")
TOOLCHAIN = [
    "Playwright browser automation",
    "StepLogger captions and screenshots",
    "Gemini TTS with gTTS fallback",
    "FFmpeg compression and caption burn",
]


def ensure_clean_directory(path: str):
    """Create a directory and remove any existing contents."""
    if os.path.isdir(path):
        for entry in os.listdir(path):
            target = os.path.join(path, entry)
            if os.path.isdir(target):
                shutil.rmtree(target)
            else:
                os.remove(target)
    os.makedirs(path, exist_ok=True)


def ensure_parent(path: str):
    """Ensure the parent directory exists before writing a file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)


def read_json_file(path: str, default):
    """Read JSON if present, otherwise return a fallback value."""
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def file_version(path: str) -> str:
    """Return a cache-busting version for a file path."""
    if not os.path.exists(path):
        return "missing"
    return str(int(os.path.getmtime(path)))


def public_href(relative_path: str, depth: int = 0) -> str:
    """Build a relative href with cache busting for local assets."""
    prefix = "../" * depth
    normalized = relative_path.replace("\\", "/")
    absolute_path = os.path.join(BASE_DIR, *normalized.split("/"))
    version = file_version(absolute_path)
    suffix = f"?v={version}" if version != "missing" else ""
    return f"{prefix}{normalized}{suffix}"


def public_page_href(relative_path: str, depth: int = 0) -> str:
    """Build a page href without cache busting."""
    prefix = "../" * depth
    normalized = relative_path.replace("\\", "/")
    return f"{prefix}{normalized}"


def transcript_step_count(path: str) -> int:
    """Count numbered step lines in a markdown transcript."""
    if not os.path.exists(path):
        return 0

    count = 0
    with open(path, encoding="utf-8") as file:
        for line in file:
            if line.lstrip().startswith("**Step "):
                count += 1
    return count


def source_screenshot_paths(demo_name: str) -> list[str]:
    """List original step screenshots for a demo."""
    demo_dir = os.path.join(SCREENSHOT_DIR, demo_name)
    if not os.path.isdir(demo_dir):
        return []
    return sorted(
        os.path.join(demo_dir, name)
        for name in os.listdir(demo_dir)
        if name.lower().endswith(".png")
    )


def copy_publishable_screenshots(demo_name: str, steps: list[dict]) -> list[str]:
    """Copy raw screenshots into a publishable output folder."""
    destination_dir = os.path.join(PUBLISHED_SCREENSHOT_DIR, demo_name)
    ensure_clean_directory(destination_dir)

    public_paths = []
    for step in steps:
        source_path = step.get("screenshot", "")
        if not source_path or not os.path.exists(source_path):
            source_path = os.path.join(
                SCREENSHOT_DIR,
                demo_name,
                f"step_{int(step.get('step', 0)):02d}.png",
            )

        if not os.path.exists(source_path):
            public_paths.append("")
            continue

        file_name = os.path.basename(source_path)
        destination_path = os.path.join(destination_dir, file_name)
        shutil.copyfile(source_path, destination_path)
        public_paths.append(f"output/screenshots/{demo_name}/{file_name}")

    return public_paths


def demo_site_label(steps: list[dict]) -> str:
    """Create a short site label from the first captured URL."""
    if not steps:
        return "Site unavailable"

    first_url = steps[0].get("url", "")
    if not first_url:
        return "Site unavailable"

    netloc = urlparse(first_url).netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc or "Site unavailable"


def validation_warnings(
    demo_name: str,
    steps: list[dict],
    transcript_count_value: int,
    source_shots: list[str],
    beats: list[dict],
    video_path: str,
) -> list[str]:
    """Check the generated artifacts for count mismatches and missing outputs."""
    warnings = []

    if not steps:
        warnings.append("No steps JSON was found for this demo. Re-record it before publishing.")
        return warnings

    for index, step in enumerate(steps, start=1):
        if step.get("step") != index:
            warnings.append("Step numbering is not sequential in the steps JSON.")
            break

    if transcript_count_value != len(steps):
        warnings.append(
            f"Transcript count mismatch: transcript has {transcript_count_value} steps while steps JSON has {len(steps)}."
        )

    if len(source_shots) != len(steps):
        warnings.append(
            f"Screenshot count mismatch: found {len(source_shots)} screenshots for {len(steps)} logged steps."
        )

    if beats and len(beats) != len(steps):
        warnings.append(
            f"Narration beat mismatch: found {len(beats)} beats for {len(steps)} logged steps."
        )

    if not os.path.exists(video_path):
        warnings.append("Final video is missing. Run recording and processing again.")

    for step in steps:
        screenshot_path = step.get("screenshot", "")
        if screenshot_path and not os.path.exists(screenshot_path):
            warnings.append("At least one logged screenshot path is missing on disk.")
            break

    return warnings


def build_demo_manifest(demo: dict) -> dict:
    """Assemble the source-of-truth metadata for one demo."""
    name = demo["name"]
    transcript_path = os.path.join(OUTPUT_DIR, f"{name}_transcript.md")
    beats_path = os.path.join(OUTPUT_DIR, f"{name}_narration_beats.json")
    video_file = f"{name}_final.webm"
    video_path = os.path.join(OUTPUT_DIR, video_file)
    steps = read_json_file(os.path.join(SCREENSHOT_DIR, f"{name}_steps.json"), [])
    narration_beats = read_json_file(beats_path, [])
    source_shots = source_screenshot_paths(name)
    published_shots = copy_publishable_screenshots(name, steps) if steps else []
    transcript_count_value = transcript_step_count(transcript_path)

    step_entries = []
    for index, step in enumerate(steps):
        published_shot = published_shots[index] if index < len(published_shots) else ""
        beat = narration_beats[index] if index < len(narration_beats) else {}
        step_entries.append(
            {
                "step": step.get("step", index + 1),
                "caption": step.get("caption") or f"Step {step.get('step', index + 1)}: {step.get('description', '')}",
                "description": step.get("description", ""),
                "url": step.get("url", ""),
                "timestamp": step.get("timestamp", ""),
                "source_screenshot": step.get("screenshot", ""),
                "published_screenshot": published_shot,
                "narration": beat.get("narration", ""),
                "pause_ms": beat.get("pause_ms", 0),
            }
        )

    warnings = validation_warnings(
        name,
        steps,
        transcript_count_value,
        source_shots,
        narration_beats,
        video_path,
    )

    manifest = {
        "name": name,
        "module": demo["module"],
        "title": demo["title"],
        "description": demo["description"],
        "prompt": demo["prompt"],
        "category": demo["category"],
        "icon": demo["icon"],
        "site": demo_site_label(steps),
        "detail_page": f"tutorials/{name}.html",
        "video": f"output/{video_file}",
        "poster": step_entries[0]["published_screenshot"] if step_entries else "",
        "transcript": f"output/{name}_transcript.md",
        "steps_json": f"screenshots/{name}_steps.json",
        "narration_beats": f"output/{name}_narration_beats.json",
        "manifest": f"output/{name}_manifest.json",
        "toolchain": TOOLCHAIN,
        "commands": {
            "record": f"python run_all.py --demo {name} --record",
            "narrate": f"python run_all.py --demo {name} --narrate",
            "process": f"python run_all.py --demo {name} --process",
            "full_pipeline": f"python run_all.py --demo {name} --record --narrate --process",
            "page_only": "python run_all.py --page-only",
        },
        "validation": {
            "status": "validated" if not warnings else "needs_refresh",
            "status_label": "Validated" if not warnings else "Needs Refresh",
            "warnings": warnings,
            "counts": {
                "steps": len(steps),
                "transcript_steps": transcript_count_value,
                "source_screenshots": len(source_shots),
                "narration_beats": len(narration_beats),
            },
        },
        "steps": step_entries,
    }

    manifest_path = os.path.join(OUTPUT_DIR, f"{name}_manifest.json")
    ensure_parent(manifest_path)
    with open(manifest_path, "w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)

    return manifest


def shared_styles() -> str:
    """Return a shared CSS block for both the index and detail pages."""
    return """
        :root {
            --bg: #f5efe4;
            --bg-deep: #efe6d7;
            --panel: rgba(255, 255, 255, 0.78);
            --panel-strong: rgba(255, 255, 255, 0.9);
            --ink: #1b2430;
            --muted: #5f6b7a;
            --line: rgba(27, 36, 48, 0.12);
            --accent: #0f766e;
            --accent-deep: #115e59;
            --accent-soft: rgba(15, 118, 110, 0.12);
            --warm: #e76f51;
            --warm-soft: rgba(231, 111, 81, 0.12);
            --warning: #9a3412;
            --warning-soft: rgba(154, 52, 18, 0.1);
            --shadow: 0 18px 48px rgba(27, 36, 48, 0.1);
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            color: var(--ink);
            background:
                radial-gradient(circle at top left, rgba(15, 118, 110, 0.18), transparent 30%),
                radial-gradient(circle at top right, rgba(231, 111, 81, 0.16), transparent 24%),
                linear-gradient(180deg, #fcf8f1 0%, var(--bg) 45%, var(--bg-deep) 100%);
            font-family: "Trebuchet MS", "Aptos", "Segoe UI", sans-serif;
        }

        h1, h2, h3 {
            margin: 0;
            font-family: "Cambria", "Palatino Linotype", "Book Antiqua", serif;
            letter-spacing: -0.02em;
        }

        p {
            margin: 0;
        }

        a {
            color: inherit;
            text-decoration: none;
        }

        code, pre {
            font-family: "Consolas", "Courier New", monospace;
        }

        .page-shell {
            max-width: 1220px;
            margin: 0 auto;
            padding: 32px 24px 72px;
        }

        .hero-card,
        .surface,
        .demo-card,
        .shot-card,
        .beat-card,
        .meta-card {
            border: 1px solid var(--line);
            background: var(--panel);
            backdrop-filter: blur(16px);
            box-shadow: var(--shadow);
        }

        .hero-card {
            border-radius: 30px;
            padding: 30px;
            animation: riseIn 0.6s ease both;
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px 12px;
            border-radius: 999px;
            background: var(--accent-soft);
            color: var(--accent-deep);
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .hero-title {
            margin-top: 16px;
            font-size: clamp(2.2rem, 5vw, 4.2rem);
            line-height: 0.96;
            max-width: 10ch;
        }

        .hero-description {
            margin-top: 18px;
            max-width: 760px;
            color: var(--muted);
            font-size: 1.05rem;
            line-height: 1.7;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 14px;
            margin-top: 26px;
        }

        .meta-card {
            border-radius: 22px;
            padding: 18px 18px 16px;
        }

        .meta-label {
            color: var(--muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .meta-value {
            margin-top: 8px;
            font-size: 1.45rem;
            font-weight: 700;
        }

        .section {
            margin-top: 28px;
        }

        .section-heading {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 14px;
        }

        .section-heading h2 {
            font-size: clamp(1.5rem, 3vw, 2.2rem);
        }

        .section-subtext {
            color: var(--muted);
            font-size: 0.95rem;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            border-radius: 999px;
            padding: 8px 12px;
            font-size: 0.82rem;
            font-weight: 700;
        }

        .status-validated {
            background: var(--accent-soft);
            color: var(--accent-deep);
        }

        .status-needs-refresh {
            background: var(--warning-soft);
            color: var(--warning);
        }

        .card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 24px;
        }

        .demo-card {
            display: flex;
            flex-direction: column;
            border-radius: 28px;
            overflow: hidden;
            animation: riseIn 0.7s ease both;
        }

        .card-cover,
        .card-placeholder {
            aspect-ratio: 16 / 9;
            width: 100%;
            background: linear-gradient(135deg, rgba(15, 118, 110, 0.16), rgba(231, 111, 81, 0.12));
            object-fit: cover;
        }

        .card-placeholder {
            display: grid;
            place-items: center;
            color: var(--accent-deep);
            font-size: 2.8rem;
            font-weight: 800;
            letter-spacing: 0.08em;
        }

        .card-body {
            padding: 20px 20px 22px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .card-topline {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
        }

        .card-title {
            font-size: 1.6rem;
            line-height: 1.1;
        }

        .card-description {
            color: var(--muted);
            line-height: 1.65;
        }

        .tag-row,
        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .tag,
        .chip {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 8px 11px;
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.72);
            color: var(--muted);
            font-size: 0.86rem;
        }

        .prompt-box,
        .code-box,
        .warning-box,
        .video-panel,
        .detail-panel {
            border-radius: 24px;
            padding: 22px;
            border: 1px solid var(--line);
            background: var(--panel-strong);
            box-shadow: var(--shadow);
        }

        .prompt-box code {
            display: block;
            white-space: pre-wrap;
            color: var(--ink);
            line-height: 1.7;
            font-size: 0.92rem;
        }

        .card-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-top: 4px;
        }

        .button,
        .button-ghost {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 44px;
            padding: 0 16px;
            border-radius: 999px;
            font-weight: 700;
            transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease;
        }

        .button {
            background: var(--accent);
            color: #ffffff;
        }

        .button-ghost {
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.62);
            color: var(--ink);
        }

        .button:hover,
        .button-ghost:hover {
            transform: translateY(-2px);
        }

        .detail-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.15fr) minmax(300px, 0.85fr);
            gap: 22px;
            align-items: start;
        }

        .video-frame {
            margin-top: 16px;
            border-radius: 20px;
            overflow: hidden;
            background: #111827;
            border: 1px solid rgba(17, 24, 39, 0.18);
        }

        video {
            width: 100%;
            display: block;
        }

        .detail-stack {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .back-link {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 18px;
            color: var(--accent-deep);
            font-weight: 700;
        }

        .shot-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 18px;
        }

        .shot-card {
            border-radius: 22px;
            overflow: hidden;
        }

        .shot-card img,
        .shot-card .shot-placeholder {
            width: 100%;
            aspect-ratio: 16 / 9;
            display: block;
            object-fit: cover;
            background: linear-gradient(135deg, rgba(15, 118, 110, 0.14), rgba(231, 111, 81, 0.12));
        }

        .shot-placeholder {
            display: grid;
            place-items: center;
            color: var(--muted);
            font-weight: 700;
        }

        .shot-body {
            padding: 16px;
            display: grid;
            gap: 10px;
        }

        .shot-step {
            font-size: 0.8rem;
            color: var(--accent-deep);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 700;
        }

        .shot-description,
        .beat-text {
            line-height: 1.65;
        }

        .shot-url {
            font-size: 0.82rem;
            color: var(--muted);
            word-break: break-word;
        }

        .beat-grid {
            display: grid;
            gap: 14px;
        }

        .beat-card {
            border-radius: 20px;
            padding: 18px;
        }

        .beat-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 10px;
        }

        .beat-step {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--accent-deep);
            font-weight: 700;
        }

        .pause-pill {
            border-radius: 999px;
            padding: 6px 10px;
            background: rgba(15, 118, 110, 0.08);
            color: var(--accent-deep);
            font-size: 0.78rem;
            font-weight: 700;
        }

        .warning-box {
            border-color: rgba(154, 52, 18, 0.22);
            background: rgba(255, 251, 245, 0.9);
        }

        .warning-list {
            margin: 12px 0 0;
            padding-left: 18px;
            color: var(--warning);
            line-height: 1.75;
        }

        .code-box pre {
            margin: 0;
            white-space: pre-wrap;
            color: var(--ink);
            line-height: 1.65;
        }

        .artifact-list {
            margin: 12px 0 0;
            padding-left: 18px;
            line-height: 1.9;
            color: var(--muted);
        }

        .artifact-list code {
            color: var(--ink);
        }

        .footer-note {
            margin-top: 28px;
            color: var(--muted);
            font-size: 0.92rem;
        }

        @keyframes riseIn {
            from {
                opacity: 0;
                transform: translateY(14px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (max-width: 920px) {
            .detail-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 640px) {
            .page-shell {
                padding: 22px 16px 56px;
            }

            .hero-card,
            .prompt-box,
            .code-box,
            .warning-box,
            .video-panel,
            .detail-panel {
                border-radius: 22px;
                padding: 18px;
            }

            .card-grid,
            .shot-grid {
                grid-template-columns: 1fr;
            }

            .card-topline,
            .beat-head,
            .section-heading {
                flex-direction: column;
                align-items: flex-start;
            }
        }
    """


def render_card(manifest: dict) -> str:
    """Render a single demo card for the index page."""
    poster = manifest.get("poster", "")
    poster_markup = (
        f'<img class="card-cover" src="{html.escape(public_href(poster), quote=True)}" '
        f'alt="{html.escape(manifest["title"], quote=True)} screenshot preview" loading="lazy">'
        if poster
        else f'<div class="card-placeholder">{html.escape(manifest["icon"])}</div>'
    )

    validation = manifest["validation"]
    status_class = "status-validated" if validation["status"] == "validated" else "status-needs-refresh"
    step_count = validation["counts"]["steps"]
    warning_count = len(validation["warnings"])
    warning_tag = (
        f'<span class="tag">{warning_count} warning{"s" if warning_count != 1 else ""}</span>'
        if warning_count
        else ""
    )

    return f"""
        <article class="demo-card">
            {poster_markup}
            <div class="card-body">
                <div class="card-topline">
                    <span class="eyebrow">{html.escape(manifest["category"])}</span>
                    <span class="status-pill {status_class}">{html.escape(validation["status_label"])}</span>
                </div>
                <h2 class="card-title">{html.escape(manifest["title"])}</h2>
                <p class="card-description">{html.escape(manifest["description"])}</p>
                <div class="tag-row">
                    <span class="tag">{step_count} steps</span>
                    <span class="tag">{html.escape(manifest["site"])}</span>
                    <span class="tag">{html.escape(manifest["module"])}.py</span>
                    {warning_tag}
                </div>
                <div class="prompt-box">
                    <span class="meta-label">Input Prompt</span>
                    <code>{html.escape(manifest["prompt"])}</code>
                </div>
                <div class="card-actions">
                    <a class="button" href="{html.escape(public_page_href(manifest["detail_page"]), quote=True)}">Open Tutorial Page</a>
                    <a class="button-ghost" href="{html.escape(public_href(manifest["video"]), quote=True)}">Open Video</a>
                </div>
            </div>
        </article>
    """


def render_shot_cards(manifest: dict) -> str:
    """Render screenshot cards for a demo detail page."""
    cards = []
    for step in manifest["steps"]:
        published = step.get("published_screenshot", "")
        image_markup = (
            f'<img src="{html.escape(public_href(published, depth=1), quote=True)}" '
            f'alt="{html.escape(step["caption"], quote=True)}" loading="lazy">'
            if published
            else '<div class="shot-placeholder">Screenshot missing</div>'
        )
        url_markup = (
            f'<a href="{html.escape(step["url"], quote=True)}" target="_blank" rel="noreferrer">{html.escape(step["url"])}</a>'
            if step.get("url")
            else "URL not captured"
        )

        cards.append(
            f"""
            <article class="shot-card">
                {image_markup}
                <div class="shot-body">
                    <div class="shot-step">Step {step["step"]}</div>
                    <p class="shot-description">{html.escape(step["description"])}</p>
                    <div class="shot-url">{url_markup}</div>
                </div>
            </article>
            """
        )

    return "\n".join(cards) if cards else '<div class="detail-panel">No screenshots were published for this demo yet.</div>'


def render_beat_cards(manifest: dict) -> str:
    """Render narration beats for the detail page."""
    cards = []
    for step in manifest["steps"]:
        narration = step.get("narration")
        if not narration:
            continue

        pause_seconds = step.get("pause_ms", 0) / 1000.0
        cards.append(
            f"""
            <article class="beat-card">
                <div class="beat-head">
                    <span class="beat-step">Step {step["step"]}</span>
                    <span class="pause-pill">Pause {pause_seconds:.2f}s</span>
                </div>
                <p class="beat-text">{html.escape(narration)}</p>
            </article>
            """
        )

    return "\n".join(cards) if cards else '<div class="detail-panel">Narration beats will appear after narration is generated.</div>'


def render_warning_box(manifest: dict) -> str:
    """Render validation warnings if present."""
    warnings = manifest["validation"]["warnings"]
    if not warnings:
        return ""

    items = "\n".join(f"<li>{html.escape(message)}</li>" for message in warnings)
    issue_label = f"{len(warnings)} issue{'s' if len(warnings) != 1 else ''}"
    return f"""
        <section class="section">
            <div class="warning-box">
                <div class="section-heading">
                    <h2>Validation Notes</h2>
                    <span class="status-pill status-needs-refresh">{issue_label}</span>
                </div>
                <ul class="warning-list">
                    {items}
                </ul>
            </div>
        </section>
    """


def render_index(manifests: list[dict]) -> str:
    """Render the root gallery page."""
    total_steps = sum(manifest["validation"]["counts"]["steps"] for manifest in manifests)
    validated = sum(1 for manifest in manifests if manifest["validation"]["status"] == "validated")
    cards_html = "\n".join(render_card(manifest) for manifest in manifests)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Automation Tutorial Showcase</title>
    <style>
    {shared_styles()}
    </style>
</head>
<body>
    <main class="page-shell">
        <section class="hero-card">
            <span class="eyebrow">Automation Portfolio Refresh</span>
            <h1 class="hero-title">Reusable tutorial demos, not just one-off videos.</h1>
            <p class="hero-description">
                Each card opens its own detail page with the final video, screenshot storyboard,
                exact prompt, rerun commands, and validation checks. The goal is a showcase that
                looks closer to a product surface than a pile of exported clips.
            </p>
            <div class="stats-grid">
                <div class="meta-card">
                    <div class="meta-label">Tutorials</div>
                    <div class="meta-value">{len(manifests)}</div>
                </div>
                <div class="meta-card">
                    <div class="meta-label">Captured Steps</div>
                    <div class="meta-value">{total_steps}</div>
                </div>
                <div class="meta-card">
                    <div class="meta-label">Validated Demos</div>
                    <div class="meta-value">{validated}/{len(manifests)}</div>
                </div>
                <div class="meta-card">
                    <div class="meta-label">Detail Pages</div>
                    <div class="meta-value">{len(manifests)}</div>
                </div>
            </div>
        </section>

        <section class="section">
            <div class="section-heading">
                <h2>Demo Cards</h2>
                <p class="section-subtext">Separate pages, screenshots, and reproducible commands for every workflow.</p>
            </div>
            <div class="card-grid">
                {cards_html}
            </div>
        </section>

        <p class="footer-note">
            Built from one shared pipeline: Playwright for capture, structured step metadata, Gemini-backed narration,
            FFmpeg post-processing, and generated HTML pages.
        </p>
    </main>
</body>
</html>"""


def render_detail_page(manifest: dict) -> str:
    """Render a separate detail page for one demo."""
    validation = manifest["validation"]
    status_class = "status-validated" if validation["status"] == "validated" else "status-needs-refresh"
    warning_count = len(validation["warnings"])
    artifact_items = [
        manifest["video"],
        manifest["transcript"],
        manifest["steps_json"],
        manifest["narration_beats"],
        manifest["manifest"],
        manifest["detail_page"],
    ]
    artifact_markup = "\n".join(f"<li><code>{html.escape(path)}</code></li>" for path in artifact_items)
    command_text = "\n".join(
        [
            manifest["commands"]["record"],
            manifest["commands"]["narrate"],
            manifest["commands"]["process"],
            manifest["commands"]["full_pipeline"],
            manifest["commands"]["page_only"],
        ]
    )
    tool_chips = "\n".join(f'<span class="chip">{html.escape(tool)}</span>' for tool in manifest["toolchain"])
    poster_attr = (
        f' poster="{html.escape(public_href(manifest["poster"], depth=1), quote=True)}"'
        if manifest.get("poster")
        else ""
    )

    warning_tag = f"{warning_count} warning{'s' if warning_count != 1 else ''}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(manifest["title"])} | Automation Tutorial</title>
    <style>
    {shared_styles()}
    </style>
</head>
<body>
    <main class="page-shell">
        <a class="back-link" href="../index.html">&larr; Back to showcase</a>

        <section class="hero-card">
            <div class="card-topline">
                <span class="eyebrow">{html.escape(manifest["category"])}</span>
                <span class="status-pill {status_class}">
                    {html.escape(validation["status_label"])}
                </span>
            </div>
            <h1 class="hero-title">{html.escape(manifest["title"])}</h1>
            <p class="hero-description">{html.escape(manifest["description"])}</p>
            <div class="tag-row" style="margin-top: 18px;">
                <span class="tag">{validation["counts"]["steps"]} steps</span>
                <span class="tag">{html.escape(manifest["site"])}</span>
                <span class="tag">{html.escape(manifest["module"])}.py</span>
                <span class="tag">{warning_tag}</span>
            </div>
        </section>

        <section class="section detail-grid">
            <div class="video-panel">
                <div class="section-heading">
                    <h2>Watch The Demo</h2>
                    <a class="button-ghost" href="{html.escape(public_href(manifest["video"], depth=1), quote=True)}">Open raw asset</a>
                </div>
                <p class="section-subtext">
                    This page pairs the final video with publishable screenshots and the exact rerun recipe.
                </p>
                <div class="video-frame">
                    <video controls preload="metadata"{poster_attr}>
                        <source src="{html.escape(public_href(manifest["video"], depth=1), quote=True)}" type="video/webm">
                        Your browser does not support the video tag.
                    </video>
                </div>
            </div>

            <div class="detail-stack">
                <div class="prompt-box">
                    <div class="section-heading">
                        <h2>Prompt</h2>
                    </div>
                    <code>{html.escape(manifest["prompt"])}</code>
                </div>

                <div class="code-box">
                    <div class="section-heading">
                        <h2>Reproduce It</h2>
                    </div>
                    <pre>{html.escape(command_text)}</pre>
                </div>

                <div class="detail-panel">
                    <div class="section-heading">
                        <h2>Toolchain</h2>
                    </div>
                    <div class="chip-row">
                        {tool_chips}
                    </div>
                </div>

                <div class="detail-panel">
                    <div class="section-heading">
                        <h2>Artifacts</h2>
                    </div>
                    <ul class="artifact-list">
                        {artifact_markup}
                    </ul>
                </div>
            </div>
        </section>

        <section class="section">
            <div class="section-heading">
                <h2>Storyboard Screenshots</h2>
                <p class="section-subtext">Every logged step now ships with a screenshot reference, not only a video file.</p>
            </div>
            <div class="shot-grid">
                {render_shot_cards(manifest)}
            </div>
        </section>

        <section class="section">
            <div class="section-heading">
                <h2>Story-First Narration</h2>
                <p class="section-subtext">Shorter, human-sounding narration beats with explicit pause suggestions.</p>
            </div>
            <div class="beat-grid">
                {render_beat_cards(manifest)}
            </div>
        </section>

        {render_warning_box(manifest)}

        <p class="footer-note">
            Validation checks compare steps JSON, transcript counts, narration beats, screenshot counts, and the final video artifact
            so mismatches are visible during the build instead of surfacing in feedback later.
        </p>
    </main>
</body>
</html>"""


def build_showcase(demos: list[dict]) -> str:
    """Build the root gallery plus one detail page per demo."""
    print("\n============================================================")
    print("  Building Demo Showcase Pages")
    print("============================================================\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PUBLISHED_SCREENSHOT_DIR, exist_ok=True)
    ensure_clean_directory(DETAIL_DIR)

    manifests = []
    for demo in demos:
        manifest = build_demo_manifest(demo)
        manifests.append(manifest)
        for warning in manifest["validation"]["warnings"]:
            print(f"  WARNING [{manifest['name']}]: {warning}")

        detail_path = os.path.join(BASE_DIR, manifest["detail_page"])
        ensure_parent(detail_path)
        with open(detail_path, "w", encoding="utf-8") as file:
            file.write(render_detail_page(manifest))

    with open(ROOT_INDEX_PATH, "w", encoding="utf-8") as file:
        file.write(render_index(manifests))

    print(f"Showcase page generated: {ROOT_INDEX_PATH}")
    return ROOT_INDEX_PATH
