"""
demo_tinkercad.py - TinkerCAD tutorial browsing demo (no login).
Flow: open Tinkercad -> learn basics -> review Airbus moon lessons -> browse
community gallery -> open the Greek Spartan Helmet design.
"""

import os
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(__file__))
from common import create_browser_context, StepLogger, slow_scroll, finish_recording

DEMO_NAME = "tinkercad"
DEMO_DESCRIPTION = (
    "Explore Tinkercad's no-login learning resources, review Airbus moon lessons, "
    "and open a standout community gallery project for inspiration."
)
DEMO_PROMPT = (
    "Open Tinkercad, search 3D design basics, review Airbus moon lessons, "
    "then browse the gallery and open the Greek Spartan Helmet design."
)
STEP_PREVIEW_HOLD_SEC = 0.85
PAGE_SETTLE_SEC = 1.8
SECTION_SETTLE_SEC = 1.35
SHORT_STEP_EXTRA_SETTLE_SEC = 1.45
SYNC_LOG_WAIT_SEC = 0.1
TYPE_DELAY_MS = 82
FINAL_PREVIEW_HOLD_SEC = 1.7


def click_visible(page, selector: str, timeout: int = 4000) -> bool:
    loc = page.locator(selector).first
    try:
        loc.wait_for(state="visible", timeout=timeout)
        loc.scroll_into_view_if_needed()
        loc.click()
        return True
    except Exception:
        return False


def type_visible(page, selector: str, text: str, delay: int = TYPE_DELAY_MS) -> bool:
    loc = page.locator(selector).first
    try:
        loc.wait_for(state="visible", timeout=5000)
        loc.scroll_into_view_if_needed()
        loc.click()
        try:
            loc.press("Control+A")
            loc.press("Delete")
        except Exception:
            pass
        loc.type(text, delay=delay)
        return True
    except Exception:
        return False


def run():
    print(f"\n{'='*60}")
    print("  RECORDING: TinkerCAD Learning Tutorial")
    print(f"{'='*60}\n")

    with sync_playwright() as p:
        browser, context, page = create_browser_context(p, DEMO_NAME)
        logger = StepLogger(DEMO_NAME)

        try:
            def announce(description: str, hold_sec: float = STEP_PREVIEW_HOLD_SEC):
                logger.preview(page, description, hold_sec=hold_sec)

            # Step 1
            page.goto("https://www.tinkercad.com/", wait_until="networkidle", timeout=30000)
            time.sleep(PAGE_SETTLE_SEC)
            logger.log(page, "Open TinkerCAD - Autodesk's free platform for 3D learning and design")

            # Step 2
            announce("Open the Learning Center where beginner tutorials are available without login")
            opened_learn = click_visible(page, 'a:has-text("Learn"), nav a[href*="/learn"]', timeout=5000)
            if opened_learn:
                page.wait_for_load_state("networkidle")
            else:
                page.goto("https://www.tinkercad.com/learn/designs", wait_until="networkidle", timeout=30000)
            time.sleep(PAGE_SETTLE_SEC)
            logger.log(page, "Open the Learning Center where beginner tutorials are available without login", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 3
            announce("Search for beginner 3D design tutorials using the search bar")
            searched = type_visible(
                page,
                'input[placeholder*="Search tutorials"], input[type="search"]',
                "3D design basics",
            )
            if searched:
                time.sleep(1.0)
                page.keyboard.press("Enter")
                time.sleep(SECTION_SETTLE_SEC)
                logger.log(page, "Search for beginner 3D design tutorials using the search bar", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)
            else:
                logger.log(page, "Browse the tutorials listed under Learn 3D Design", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 4
            announce("Stick with the 3D Design tutorials and let the results settle")
            clicked_designs = click_visible(
                page,
                'a[href*="/learn/search/designs"], button:has-text("3D Designs"), a:has-text("3D Designs")',
                timeout=5000,
            )
            if clicked_designs:
                page.wait_for_load_state("networkidle")
                time.sleep(SECTION_SETTLE_SEC)
            else:
                time.sleep(SHORT_STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Stay on the 3D Design track while the search results load", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 5
            announce("Scroll through the lesson cards and do a quick quality check")
            slow_scroll(page, 260, 3)
            time.sleep(0.8)
            logger.log(page, "Scroll through the lesson cards and scan for clear beginner-friendly tutorials", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 6
            announce("Open an Airbus moon lesson from the search results")
            opened_airbus = click_visible(
                page,
                'a[href*="airbus-habitat-on-the-moon"], a[href*="airbus-traveling-to-the-moon"], a[href*="airbus-living-on-the-moon"], a[href*="airbus-driving-on-the-moon"]',
                timeout=5000,
            )
            if opened_airbus:
                page.wait_for_load_state("networkidle")
                time.sleep(PAGE_SETTLE_SEC)
                logger.log(page, "Open an Airbus moon lesson to view the guided project details", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)
            else:
                logger.log(page, "Open any visible moon-focused Airbus lesson from the search results", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 7
            announce("Scroll through the moon lesson visuals and project overview")
            slow_scroll(page, 520, 5)
            time.sleep(1.0)
            logger.log(page, "Scroll through the Airbus moon lesson to review the visuals and instructions", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 8
            announce("Open the Community Gallery to explore design inspiration")
            opened_gallery = click_visible(page, 'a:has-text("Gallery"), nav a[href*="/things"]', timeout=5000)
            if opened_gallery:
                page.wait_for_load_state("networkidle")
            else:
                page.goto("https://www.tinkercad.com/things", wait_until="networkidle", timeout=30000)
            time.sleep(PAGE_SETTLE_SEC)
            logger.log(page, "Open the Community Gallery to explore standout Tinkercad designs", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 9
            announce("Browse the gallery and spot the standout community projects")
            time.sleep(1.0)
            logger.log(page, "Browse the gallery and keep the top community designs in view", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 10
            announce("Open the Greek Spartan Helmet design from the gallery")
            opened_design = click_visible(
                page,
                'a[href*="my-take-on-a-greek-spartan-helmet-march-2026"]',
                timeout=5000,
            )
            if opened_design:
                page.wait_for_load_state("networkidle")
                time.sleep(SECTION_SETTLE_SEC)
                logger.log(page, "Open the Greek Spartan Helmet - March 2026 design from the gallery", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)
            else:
                page.goto(
                    "https://www.tinkercad.com/things/ddtuLraw1Zf-my-take-on-a-greek-spartan-helmet-march-2026",
                    wait_until="networkidle",
                    timeout=30000,
                )
                time.sleep(SECTION_SETTLE_SEC)
                logger.log(page, "Open the Greek Spartan Helmet - March 2026 design from the gallery", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 11
            announce("View the 3D model and inspect the design details")
            time.sleep(PAGE_SETTLE_SEC)
            logger.log(page, "View the 3D model and inspect how the Spartan Helmet design is built", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Finish
            logger.preview(page, "Tutorial complete - learn it, browse it, build it", hold_sec=FINAL_PREVIEW_HOLD_SEC)
            logger.log(page, "Tutorial complete - learn it, browse it, build it", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

        except Exception as error:
            print(f"\nERROR during recording: {error}")
            logger.log(page, f"Error encountered: {str(error)[:80]}", wait_sec=0)

        finally:
            logger.save()
            logger.save_transcript()
            finish_recording(browser, context, DEMO_NAME, page)

    return DEMO_NAME, DEMO_DESCRIPTION, DEMO_PROMPT


if __name__ == "__main__":
    run()
