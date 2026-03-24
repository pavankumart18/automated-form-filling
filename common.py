"""
common.py - Shared utilities for the video tutorial generator.
Handles: click indicators, keystroke overlays, step logging, browser setup.
"""

import json
import os
import shutil
import time
from datetime import datetime

from playwright.sync_api import Page

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "videos")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

for directory in [VIDEO_DIR, SCREENSHOT_DIR, OUTPUT_DIR]:
    os.makedirs(directory, exist_ok=True)


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


CLICK_INDICATOR_JS = """
(() => {
  const init = () => {
    if (window.__tutorialClickOverlayReady) return;
    window.__tutorialClickOverlayReady = true;

    const style = document.createElement('style');
    style.textContent = `
      @keyframes clickRipple {
        0% {
          transform: translate(-50%, -50%) scale(0.28);
          opacity: 0.95;
        }
        70% {
          transform: translate(-50%, -50%) scale(1.9);
          opacity: 0.38;
        }
        100% {
          transform: translate(-50%, -50%) scale(2.75);
          opacity: 0;
        }
      }
      @keyframes clickPulse {
        0%, 100% {
          transform: translate(-50%, -50%) scale(1);
          opacity: 0.92;
        }
        50% {
          transform: translate(-50%, -50%) scale(1.16);
          opacity: 1;
        }
      }
      .click-indicator {
        position: fixed;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(255, 64, 64, 0.42) 0%, rgba(255, 64, 64, 0.22) 52%, rgba(255, 64, 64, 0) 72%);
        border: 4px solid rgba(255, 64, 64, 0.8);
        box-shadow: 0 0 0 10px rgba(255, 64, 64, 0.16), 0 12px 28px rgba(120, 0, 0, 0.24);
        pointer-events: none;
        z-index: 999999;
        transform: translate(-50%, -50%) scale(0.28);
        animation: clickRipple 0.95s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      }
      .click-indicator::after {
        content: '';
        position: absolute;
        inset: 14px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.82);
        opacity: 0.7;
      }
      .click-dot {
        position: fixed;
        width: 18px;
        height: 18px;
        border-radius: 50%;
        background: rgba(255, 64, 64, 0.96);
        border: 4px solid rgba(255, 255, 255, 0.72);
        box-shadow: 0 0 0 8px rgba(255, 64, 64, 0.18), 0 8px 18px rgba(120, 0, 0, 0.26);
        pointer-events: none;
        z-index: 999999;
        transition: opacity 0.3s ease-out;
        transform: translate(-50%, -50%);
        animation: clickPulse 1.3s ease-in-out infinite;
      }
    `;
    document.head.appendChild(style);

    const root = document.body || document.documentElement;
    if (!root) return;

    const cursorDot = document.createElement('div');
    cursorDot.className = 'click-dot';
    cursorDot.style.display = 'none';
    root.appendChild(cursorDot);

    document.addEventListener('mousemove', (e) => {
      cursorDot.style.display = 'block';
      cursorDot.style.left = e.clientX + 'px';
      cursorDot.style.top = e.clientY + 'px';
    });

    document.addEventListener('click', (e) => {
      const ripple = document.createElement('div');
      ripple.className = 'click-indicator';
      ripple.style.left = e.clientX + 'px';
      ripple.style.top = e.clientY + 'px';
      root.appendChild(ripple);
      setTimeout(() => ripple.remove(), 1100);
    });
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
"""

KEYSTROKE_OVERLAY_JS = """
(() => {
  const init = () => {
    if (window.__tutorialKeystrokeOverlayReady) return;
    window.__tutorialKeystrokeOverlayReady = true;

    const root = document.body || document.documentElement;
    if (!root) return;

    const bar = document.createElement('div');
    bar.id = 'keystroke-bar';
    bar.style.cssText = `
      position: fixed;
      bottom: 0;
      left: 0;
      width: 100%;
      background: rgba(0, 0, 0, 0.85);
      color: #00ff88;
      font-family: 'Courier New', monospace;
      font-size: 20px;
      padding: 10px 20px;
      z-index: 999999;
      pointer-events: none;
      display: none;
      letter-spacing: 2px;
      box-shadow: 0 -2px 10px rgba(0,0,0,0.3);
    `;
    root.appendChild(bar);

    let clearTimeoutId = null;

    document.addEventListener('keydown', (e) => {
      bar.style.display = 'block';

      let keyDisplay = '';
      if (e.key === ' ') keyDisplay = '[SPACE]';
      else if (e.key === 'Enter') keyDisplay = '[ENTER]';
      else if (e.key === 'Backspace') {
        bar.textContent = bar.textContent.slice(0, -1);
        return;
      } else if (e.key === 'Tab') keyDisplay = '[TAB]';
      else if (e.key === 'Escape') keyDisplay = '[ESC]';
      else if (e.key.length === 1) keyDisplay = e.key;
      else keyDisplay = `[${e.key}]`;

      bar.textContent += keyDisplay;

      clearTimeout(clearTimeoutId);
      clearTimeoutId = setTimeout(() => {
        bar.style.display = 'none';
        bar.textContent = '';
      }, 2500);
    });
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
"""

CAPTION_OVERLAY_JS = """
(() => {
  const attachCaption = () => {
    if (typeof window._showCaption === 'function') return;

    const root = document.body || document.documentElement;
    if (!root) return;

    const existing = document.getElementById('step-caption');
    const caption = existing || document.createElement('div');
    caption.id = 'step-caption';
    caption.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      background: linear-gradient(135deg, rgba(30, 60, 120, 0.92), rgba(20, 40, 80, 0.92));
      color: #ffffff;
      font-family: 'Segoe UI', Arial, sans-serif;
      font-size: 18px;
      font-weight: 600;
      padding: 12px 24px;
      z-index: 999998;
      pointer-events: none;
      display: none;
      text-align: center;
      box-shadow: 0 2px 10px rgba(0,0,0,0.3);
      letter-spacing: 0.5px;
    `;
    if (!existing) root.appendChild(caption);

    window._showCaption = (text) => {
      caption.textContent = text;
      caption.style.display = 'block';
    };

    window._hideCaption = () => {
      caption.style.display = 'none';
    };
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', attachCaption, { once: true });
  } else {
    attachCaption();
  }
})();
"""

CAPTION_SAFE_EVAL_JS = """
(text) => {
  try {
    if (typeof window._showCaption !== 'function') {
      const root = document.body || document.documentElement;
      if (root) {
        let caption = document.getElementById('step-caption');
        if (!caption) {
          caption = document.createElement('div');
          caption.id = 'step-caption';
          caption.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background: linear-gradient(135deg, rgba(30, 60, 120, 0.92), rgba(20, 40, 80, 0.92));
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 18px;
            font-weight: 600;
            padding: 12px 24px;
            z-index: 999998;
            pointer-events: none;
            display: none;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            letter-spacing: 0.5px;
          `;
          root.appendChild(caption);
        }
        window._showCaption = (msg) => {
          caption.textContent = msg;
          caption.style.display = 'block';
        };
      }
    }
    if (typeof window._showCaption === 'function') {
      window._showCaption(text);
    }
  } catch (e) {
  }
}
"""


class StepLogger:
    """Logs each step with description, URL, timestamp, and screenshot."""

    def __init__(self, demo_name: str):
        self.demo_name = demo_name
        self.steps = []
        self.screenshot_dir = os.path.join(SCREENSHOT_DIR, demo_name)
        ensure_clean_directory(self.screenshot_dir)

    def show_caption(self, page: Page, text: str):
        """Safely show top caption without crashing the tutorial if overlay isn't ready."""
        try:
            page.evaluate(CAPTION_SAFE_EVAL_JS, text)
        except Exception as error:
            print(f"  WARNING: Could not render caption overlay: {error}")

    def log(self, page: Page, description: str, wait_sec: float = 1.0):
        """Log a step: take screenshot, record metadata, show caption."""
        time.sleep(wait_sec)

        step_num = len(self.steps) + 1
        step_label = f"Step {step_num}: {description}"
        screenshot_path = os.path.join(self.screenshot_dir, f"step_{step_num:02d}.png")

        self.show_caption(page, step_label)
        time.sleep(0.65)

        page.screenshot(path=screenshot_path)

        self.steps.append(
            {
                "step": step_num,
                "caption": step_label,
                "description": description,
                "url": page.url,
                "timestamp": datetime.now().isoformat(),
                "screenshot": screenshot_path,
            }
        )
        print(f"  Step {step_num}: {description}")

    def save(self):
        """Save steps to JSON file."""
        output_path = os.path.join(SCREENSHOT_DIR, f"{self.demo_name}_steps.json")
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(self.steps, file, indent=2)
        print(f"\nSteps saved to: {output_path}")
        return output_path

    def get_transcript(self) -> str:
        """Generate a readable transcript from steps."""
        lines = [f"## Tutorial: {self.demo_name}\n"]
        for step in self.steps:
            lines.append(f"**Step {step['step']}:** {step['description']}")
            lines.append(f"  - URL: {step['url']}\n")
        return "\n".join(lines)

    def save_transcript(self):
        """Save readable transcript as markdown."""
        output_path = os.path.join(OUTPUT_DIR, f"{self.demo_name}_transcript.md")
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(self.get_transcript())
        print(f"Transcript saved to: {output_path}")
        return output_path


def create_browser_context(playwright, demo_name: str, headless: bool = False) -> tuple:
    """
    Launch browser with stealth settings, video recording, and overlays.
    Returns: (browser, context, page)
    """
    video_dir = os.path.join(VIDEO_DIR, demo_name)
    ensure_clean_directory(video_dir)

    browser = playwright.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ],
    )

    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 720},
        locale="en-IN",
        timezone_id="Asia/Kolkata",
        ignore_https_errors=True,
        record_video_dir=video_dir,
        record_video_size={"width": 1280, "height": 720},
    )

    page = context.new_page()

    page.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    """
    )
    page.add_init_script(CLICK_INDICATOR_JS)
    page.add_init_script(KEYSTROKE_OVERLAY_JS)
    page.add_init_script(CAPTION_OVERLAY_JS)

    return browser, context, page


def safe_click(page: Page, selector: str, timeout: int = 10000):
    """Click with wait and error handling."""
    try:
        page.wait_for_selector(selector, timeout=timeout, state="visible")
        page.click(selector)
    except Exception as error:
        print(f"  WARNING: Could not click '{selector}': {error}")


def safe_fill(page: Page, selector: str, text: str, timeout: int = 10000):
    """Fill input with wait, clear first, then type slowly for visual effect."""
    try:
        page.wait_for_selector(selector, timeout=timeout, state="visible")
        page.click(selector)
        page.fill(selector, "")
        page.type(selector, text, delay=80)
    except Exception as error:
        print(f"  WARNING: Could not fill '{selector}': {error}")


def slow_scroll(page: Page, pixels: int = 300, steps: int = 3):
    """Smooth scroll for visual effect in video."""
    step_size = pixels // steps
    for _ in range(steps):
        page.mouse.wheel(0, step_size)
        time.sleep(0.3)


def finish_recording(browser, context, demo_name: str, page: Page | None = None) -> str:
    """Close context to finalize video and keep only the chosen raw recording."""
    preferred_video = ""
    context.close()

    if page is not None:
        try:
            video = page.video
            if video:
                preferred_video = video.path()
        except Exception as error:
            print(f"  WARNING: Could not resolve page video directly: {error}")

    browser.close()

    video_dir = os.path.join(VIDEO_DIR, demo_name)
    videos = [
        os.path.join(video_dir, file_name)
        for file_name in os.listdir(video_dir)
        if file_name.endswith(".webm")
    ]

    if not videos:
        print("\nWARNING: No video file found!")
        return ""

    chosen_video = preferred_video if preferred_video and os.path.exists(preferred_video) else ""
    if not chosen_video:
        # Fallback: prefer the largest recording, then break ties by recency.
        chosen_video = max(videos, key=lambda path: (os.path.getsize(path), os.path.getmtime(path)))

    canonical_video = os.path.join(video_dir, f"{demo_name}.webm")
    if os.path.abspath(chosen_video) != os.path.abspath(canonical_video):
        shutil.copyfile(chosen_video, canonical_video)
        chosen_video = canonical_video

    for video_path in videos:
        if os.path.abspath(video_path) != os.path.abspath(chosen_video):
            try:
                os.remove(video_path)
            except OSError:
                pass

    print(f"\nRaw video saved: {chosen_video}")
    return chosen_video
