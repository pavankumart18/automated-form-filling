"""
demo_screener.py - Screener.in Stock Research Tutorial
Workflow: Search company -> View financials -> Open public stock screens -> Compare stocks
"""

import os
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(__file__))
from common import create_browser_context, StepLogger, slow_scroll, finish_recording

DEMO_NAME = "screener"
DEMO_DESCRIPTION = (
    "How to research stocks on Screener.in - search a company, analyze financials, "
    "and use public stock screens to compare companies."
)
DEMO_PROMPT = (
    "Go to screener.in, search for Reliance Industries, view quarterly results, "
    "then open a public stock screen with PE/ROE filters."
)

COMPANY_URLS = [
    "https://www.screener.in/company/RELIANCE/",
    "https://www.screener.in/company/500325/",
    "https://www.screener.in/company/RELIANCE/consolidated/",
]
PUBLIC_SCREENS_LIST_URL = "https://www.screener.in/screens/"
SCREEN_FALLBACK_URLS = [
    "https://www.screener.in/screens/18/high-growth-high-roe-low-pe/",
    "https://www.screener.in/screens/184/value-stocks/",
    "https://www.screener.in/screens/1/the-bull-cartel/",
]
STEP_PREVIEW_HOLD_SEC = 0.85
PAGE_SETTLE_SEC = 1.6
SECTION_SETTLE_SEC = 1.85
SHORT_STEP_EXTRA_SETTLE_SEC = 1.2
RESULT_OPEN_SETTLE_SEC = 1.9
SYNC_LOG_WAIT_SEC = 0.1


def is_404_page(page) -> bool:
    """Detect Screener 404 pages based on title/body patterns."""
    try:
        title = page.title().lower()
        if "404" in title or "page not found" in title:
            return True
    except Exception:
        pass

    patterns = [
        "Error 404: Page Not Found",
        "Resolver404",
        "No Screen matches the given query",
        "We couldn't find the page you are looking for.",
    ]
    for text in patterns:
        try:
            if page.get_by_text(text, exact=False).first.is_visible(timeout=1200):
                return True
        except Exception:
            continue
    return False


def goto_first_working_url(page, urls):
    """Open the first URL that does not render a 404 page."""
    for url in urls:
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(1)
            if not is_404_page(page):
                return url
        except Exception:
            continue
    return None


def open_company_page(page, logger, announce):
    """Open a stable Reliance page so the demo is reproducible and easy to sync."""
    announce("Navigate directly to Reliance Industries company page")
    opened = goto_first_working_url(page, COMPANY_URLS)
    if opened:
        time.sleep(PAGE_SETTLE_SEC)
        logger.log(page, "Navigate directly to Reliance Industries company page", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)
        return True
    return False


def open_public_screen(page, logger, announce):
    """Open a stable public screen path for a repeatable portfolio demo."""
    announce("Open the Public Screens page to explore ready-made stock filters")
    page.goto(PUBLIC_SCREENS_LIST_URL, wait_until="networkidle", timeout=30000)
    time.sleep(PAGE_SETTLE_SEC)
    if is_404_page(page):
        return False

    logger.log(page, "Open the Public Screens page to explore ready-made stock filters", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

    announce("Open a public screen to view companies matching prebuilt criteria")
    working = goto_first_working_url(page, SCREEN_FALLBACK_URLS)
    if working:
        time.sleep(SECTION_SETTLE_SEC)
        logger.log(page, "Open a public screen to view companies matching prebuilt criteria", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)
        return True
    return False


def run():
    print(f"\n{'='*60}")
    print("  RECORDING: Screener.in Stock Research Tutorial")
    print(f"{'='*60}\n")

    with sync_playwright() as p:
        browser, context, page = create_browser_context(p, DEMO_NAME)
        logger = StepLogger(DEMO_NAME)

        try:
            def announce(description: str):
                logger.preview(page, description, hold_sec=STEP_PREVIEW_HOLD_SEC)

            # Step 1: Open Screener
            page.goto("https://www.screener.in/", wait_until="networkidle", timeout=30000)
            time.sleep(PAGE_SETTLE_SEC)
            logger.log(page, "Open Screener.in - India's popular stock research platform")

            # Step 2: Open company
            company_opened = open_company_page(page, logger, announce)
            if not company_opened:
                raise RuntimeError("Could not open a working Reliance company page.")

            # Step 3-6: Financial sections
            announce("View key metrics - market cap, PE ratio, ROCE, and valuation snapshot")
            time.sleep(SHORT_STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "View key metrics - market cap, PE ratio, ROCE, and valuation snapshot", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Bring quarterly section into view if available, otherwise scroll naturally
            announce("Review quarterly financial trends to understand recent performance")
            quarterly_tab = page.locator('a:has-text("Quarters"), a:has-text("Quarterly")').first
            if quarterly_tab.is_visible():
                quarterly_tab.click()
                time.sleep(SECTION_SETTLE_SEC)
            else:
                slow_scroll(page, 520, 5)
                time.sleep(0.8)
            logger.log(page, "Review quarterly financial trends to understand recent performance", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            announce("Inspect Profit and Loss details - revenue, expenses, and margins")
            pnl_tab = page.locator('a:has-text("Profit & Loss"), a:has-text("P&L")').first
            if pnl_tab.is_visible():
                pnl_tab.click()
                time.sleep(SECTION_SETTLE_SEC)
            else:
                slow_scroll(page, 500, 5)
                time.sleep(0.8)
            logger.log(page, "Inspect Profit and Loss details - revenue, expenses, and margins", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            announce("Check balance sheet strength - assets, liabilities, and equity")
            balance_tab = page.locator('a:has-text("Balance Sheet"), a:has-text("Balance")').first
            if balance_tab.is_visible():
                balance_tab.click()
                time.sleep(SECTION_SETTLE_SEC)
            else:
                slow_scroll(page, 420, 4)
                time.sleep(0.8)
            logger.log(page, "Check balance sheet strength - assets, liabilities, and equity", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 7-8: Public screens
            screen_opened = open_public_screen(page, logger, announce)
            if not screen_opened:
                raise RuntimeError("Public screen pages were not reachable.")

            # Step 9: Browse results
            announce("Browse filtered companies and compare PE, ROE, and market cap")
            slow_scroll(page, 480, 5)
            time.sleep(1.0)
            logger.log(page, "Browse filtered companies and compare PE, ROE, and market cap", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 10: Open a company from table if present
            announce("Open Bank of India from the screen for deeper analysis")
            company_link = page.locator('table a[href*="/company/"]').first
            if company_link.is_visible():
                company_name = (company_link.text_content() or "").strip()
                company_link.click()
                page.wait_for_load_state("networkidle")
                time.sleep(RESULT_OPEN_SETTLE_SEC)
                if company_name:
                    logger.log(page, f"Open {company_name} from the screen for deeper analysis", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)
                else:
                    logger.log(page, "Open a company from the screen for deeper analysis", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)
            else:
                logger.log(page, "Open a company from the screen for deeper analysis", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Finish
            logger.preview(page, "Tutorial complete - you can now research and compare stocks on Screener.in", hold_sec=1.8)
            logger.log(page, "Tutorial complete - you can now research and compare stocks on Screener.in", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

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
