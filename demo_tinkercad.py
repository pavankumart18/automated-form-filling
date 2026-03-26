"""
demo_tinkercad.py - TinkerCAD tutorial browsing demo (no login).
Flow: open TinkerCAD -> learning center -> search/filter tutorials -> gallery.
"""

import os
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(__file__))
from common import create_browser_context, StepLogger, slow_scroll, finish_recording

DEMO_NAME = "tinkercad"
DEMO_DESCRIPTION = (
    "Explore TinkerCAD's no-login learning resources by browsing tutorials, "
    "switching categories, and checking gallery designs."
)
DEMO_PROMPT = (
    "Open TinkerCAD learning center, search beginner tutorials, switch categories, "
    "and browse gallery designs for inspiration."
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
            announce("Return to 3D Design tutorials for CAD-focused practice")
            clicked_circuits = click_visible(page, 'button:has-text("Circuits"), a:has-text("Circuits"), text=Circuits')
            if clicked_circuits:
                time.sleep(SECTION_SETTLE_SEC)
                click_visible(page, 'button:has-text("3D Design"), a:has-text("3D Design"), text=3D Design')
                time.sleep(SHORT_STEP_EXTRA_SETTLE_SEC)
            else:
                time.sleep(SHORT_STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Return to 3D Design tutorials for CAD-focused practice", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 5
            announce("Open a tutorial card to view guided learning content")
            opened_card = click_visible(
                page,
                'main a[href*="/learn/"], section a[href*="/learn/"], a:has-text("Learn 3D Design")',
                timeout=5000,
            )
            if opened_card:
                page.wait_for_load_state("networkidle")
                time.sleep(PAGE_SETTLE_SEC)
                logger.log(page, "Open a tutorial card to view guided learning content", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)
            else:
                logger.log(page, "Select any visible tutorial card to open guided instructions", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 6
            announce("Scroll through the tutorial page to view lesson details and visuals")
            slow_scroll(page, 540, 5)
            time.sleep(1.0)
            logger.log(page, "Scroll through the tutorial page to view lesson details and visuals", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 7
            announce("Open the TinkerCAD gallery to explore community designs")
            page.goto("https://www.tinkercad.com/things", wait_until="networkidle", timeout=30000)
            time.sleep(PAGE_SETTLE_SEC)
            logger.log(page, "Open the TinkerCAD gallery to explore community designs", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 8
            announce("Browse featured gallery designs for project inspiration")
            search_gallery = type_visible(
                page,
                'input[placeholder*="Search"], input[type="search"]',
                "phone stand",
            )
            if search_gallery:
                time.sleep(1.0)
                page.keyboard.press("Enter")
                time.sleep(SECTION_SETTLE_SEC)
                logger.log(page, "Search gallery designs for 'phone stand' inspiration", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)
            else:
                slow_scroll(page, 320, 3)
                time.sleep(0.8)
                logger.log(page, "Browse featured gallery designs for project inspiration", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 9
            announce("Open a gallery design page to review details and references")
            opened_design = click_visible(
                page,
                'a[href*="/things/"], .gallery-item a, main a[href*="/things/"]',
                timeout=5000,
            )
            if opened_design:
                page.wait_for_load_state("networkidle")
                time.sleep(SECTION_SETTLE_SEC)
                logger.log(page, "Open a gallery design page to review details and references", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)
            else:
                slow_scroll(page, 360, 4)
                time.sleep(0.8)
                logger.log(page, "Scroll through gallery results to inspect multiple design ideas", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Finish
            logger.preview(page, "Tutorial complete - start learning TinkerCAD with no-login resources", hold_sec=FINAL_PREVIEW_HOLD_SEC)
            logger.log(page, "Tutorial complete - start learning TinkerCAD with no-login resources", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

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
