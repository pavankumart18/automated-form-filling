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


def click_visible(page, selector: str, timeout: int = 4000) -> bool:
    loc = page.locator(selector).first
    try:
        loc.wait_for(state="visible", timeout=timeout)
        loc.scroll_into_view_if_needed()
        loc.click()
        return True
    except Exception:
        return False


def type_visible(page, selector: str, text: str, delay: int = 70) -> bool:
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
            # Step 1
            page.goto("https://www.tinkercad.com/", wait_until="networkidle", timeout=30000)
            time.sleep(1.5)
            logger.log(page, "Open TinkerCAD - Autodesk's free platform for 3D learning and design")

            # Step 2
            page.goto("https://www.tinkercad.com/learn/designs", wait_until="networkidle", timeout=30000)
            time.sleep(1.5)
            logger.log(page, "Open the Learning Center where beginner tutorials are available without login")

            # Step 3
            searched = type_visible(
                page,
                'input[placeholder*="Search tutorials"], input[type="search"]',
                "3D design basics",
            )
            if searched:
                time.sleep(0.8)
                page.keyboard.press("Enter")
                time.sleep(1.2)
                logger.log(page, "Search for beginner 3D design tutorials using the search bar")
            else:
                logger.log(page, "Browse the tutorials listed under Learn 3D Design")

            # Step 4
            clicked_circuits = click_visible(page, 'button:has-text("Circuits"), a:has-text("Circuits"), text=Circuits')
            if clicked_circuits:
                time.sleep(1.0)
                logger.log(page, "Switch to the Circuits category to see electronics-focused lessons")
                click_visible(page, 'button:has-text("3D Design"), a:has-text("3D Design"), text=3D Design')
                time.sleep(0.8)
            logger.log(page, "Return to 3D Design tutorials for CAD-focused practice")

            # Step 5
            opened_card = click_visible(
                page,
                'main a[href*="/learn/"], section a[href*="/learn/"], a:has-text("Learn 3D Design")',
                timeout=5000,
            )
            if opened_card:
                page.wait_for_load_state("networkidle")
                time.sleep(1.5)
                logger.log(page, "Open a tutorial card to view guided learning content")
            else:
                logger.log(page, "Select any visible tutorial card to open guided instructions")

            # Step 6
            slow_scroll(page, 450, 4)
            time.sleep(0.8)
            logger.log(page, "Scroll through the tutorial page to view lesson details and visuals")

            # Step 7
            page.goto("https://www.tinkercad.com/things", wait_until="networkidle", timeout=30000)
            time.sleep(1.5)
            logger.log(page, "Open the TinkerCAD gallery to explore community designs")

            # Step 8
            search_gallery = type_visible(
                page,
                'input[placeholder*="Search"], input[type="search"]',
                "phone stand",
            )
            if search_gallery:
                time.sleep(0.8)
                page.keyboard.press("Enter")
                time.sleep(1.2)
                logger.log(page, "Search gallery designs for 'phone stand' inspiration")
            else:
                logger.log(page, "Browse featured gallery designs for project inspiration")

            # Step 9
            opened_design = click_visible(
                page,
                'a[href*="/things/"], .gallery-item a, main a[href*="/things/"]',
                timeout=5000,
            )
            if opened_design:
                page.wait_for_load_state("networkidle")
                time.sleep(1.2)
                logger.log(page, "Open a gallery design page to review details and references")
            else:
                slow_scroll(page, 300, 3)
                logger.log(page, "Scroll through gallery results to inspect multiple design ideas")

            # Finish
            logger.show_caption(page, "Tutorial complete! Explore and learn TinkerCAD for free")
            time.sleep(1.6)
            logger.log(page, "Tutorial complete - start learning TinkerCAD with no-login resources", wait_sec=0.5)

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
