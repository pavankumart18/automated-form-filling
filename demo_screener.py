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


def open_company_page(page, logger):
    """Try search first, then direct company URLs."""
    search_box = page.locator(
        'input[type="search"], input[name="q"], input[placeholder*="Search"], #search'
    ).first

    try:
        if search_box.is_visible():
            search_box.click()
            search_box.fill("")
            search_box.type("Reliance Industries", delay=70)
            time.sleep(1.2)
            logger.log(page, "Search for Reliance Industries in the search bar")

            result = page.locator(
                '.dropdown-content a[href*="/company/"], '
                '.results a[href*="/company/"], '
                'a[href*="/company/RELIANCE"]'
            ).first
            if result.is_visible(timeout=3000):
                result.click()
                page.wait_for_load_state("networkidle")
                time.sleep(1.5)
                if not is_404_page(page):
                    logger.log(page, "Open Reliance Industries from search results")
                    return True
    except Exception:
        pass

    opened = goto_first_working_url(page, COMPANY_URLS)
    if opened:
        logger.log(page, "Navigate directly to Reliance Industries company page")
        return True
    return False


def open_public_screen(page, logger):
    """Open a public screen without using outdated /screens/new URLs."""
    page.goto(PUBLIC_SCREENS_LIST_URL, wait_until="networkidle", timeout=30000)
    time.sleep(1.5)
    if is_404_page(page):
        return False

    logger.log(page, "Open the Public Screens page to explore ready-made stock filters")

    candidates = page.locator('a[href*="/screens/"][href*="/"]').all()
    for link in candidates:
        try:
            href = link.get_attribute("href") or ""
            if href.rstrip("/") in ["/screens", "/screens/"]:
                continue
            if "/screens/" not in href:
                continue
            link.first.click()
            page.wait_for_load_state("networkidle")
            time.sleep(1.2)
            if not is_404_page(page):
                logger.log(page, "Open a public screen to view companies matching prebuilt criteria")
                return True
            page.go_back(wait_until="networkidle")
            time.sleep(1)
        except Exception:
            try:
                page.goto(PUBLIC_SCREENS_LIST_URL, wait_until="networkidle", timeout=30000)
            except Exception:
                pass
            continue

    working = goto_first_working_url(page, SCREEN_FALLBACK_URLS)
    if working:
        logger.log(page, "Open a known public screen with quality/value filters")
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
            # Step 1: Open Screener
            page.goto("https://www.screener.in/", wait_until="networkidle", timeout=30000)
            logger.log(page, "Open Screener.in - India's popular stock research platform")

            # Step 2: Open company
            company_opened = open_company_page(page, logger)
            if not company_opened:
                raise RuntimeError("Could not open a working Reliance company page.")

            # Step 3-6: Financial sections
            logger.log(page, "View key metrics - market cap, PE ratio, ROCE, and valuation snapshot")

            # Bring quarterly section into view if available, otherwise scroll naturally
            quarterly_tab = page.locator('a:has-text("Quarters"), a:has-text("Quarterly")').first
            if quarterly_tab.is_visible():
                quarterly_tab.click()
                time.sleep(1.5)
            else:
                slow_scroll(page, 400, 4)
            logger.log(page, "Review quarterly financial trends to understand recent performance")

            pnl_tab = page.locator('a:has-text("Profit & Loss"), a:has-text("P&L")').first
            if pnl_tab.is_visible():
                pnl_tab.click()
                time.sleep(1.5)
            else:
                slow_scroll(page, 400, 4)
            logger.log(page, "Inspect Profit and Loss details - revenue, expenses, and margins")

            balance_tab = page.locator('a:has-text("Balance Sheet"), a:has-text("Balance")').first
            if balance_tab.is_visible():
                balance_tab.click()
                time.sleep(1.5)
            else:
                slow_scroll(page, 300, 3)
            logger.log(page, "Check balance sheet strength - assets, liabilities, and equity")

            # Step 7-8: Public screens
            screen_opened = open_public_screen(page, logger)
            if not screen_opened:
                raise RuntimeError("Public screen pages were not reachable.")

            # Step 9: Browse results
            slow_scroll(page, 350, 3)
            logger.log(page, "Browse filtered companies and compare PE, ROE, and market cap")

            # Step 10: Open a company from table if present
            company_link = page.locator('table a[href*="/company/"]').first
            if company_link.is_visible():
                company_name = (company_link.text_content() or "").strip()
                company_link.click()
                page.wait_for_load_state("networkidle")
                time.sleep(1.5)
                logger.log(page, f"Open {company_name or 'a company'} from the screen for deeper analysis")
            else:
                logger.log(page, "Open any company from the screen results for deeper analysis")

            # Finish
            logger.show_caption(page, "Tutorial complete! You can now research and compare stocks on Screener.in")
            time.sleep(2)
            logger.log(page, "Tutorial complete - you can now research and compare stocks on Screener.in", wait_sec=0)

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
