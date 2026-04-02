"""
demo_screener.py - Screener.in stock research tutorial.
Workflow: open Screener -> search Reliance -> inspect financial sections ->
click Screens -> open a growth/value screen -> open Ganesh Infra.
"""

import os
import re
import sys
import time
from urllib.parse import urljoin

from playwright.sync_api import Locator, sync_playwright

sys.path.insert(0, os.path.dirname(__file__))
from common import (
    StepLogger,
    create_browser_context,
    finish_recording,
    point_and_highlight_locator,
    point_at_locator,
    slow_scroll,
)

DEMO_NAME = "screener"
DEMO_DESCRIPTION = (
    "How to choose stocks on Screener.in using a repeatable checklist: type "
    "Reliance Industries into the visible search box, inspect the key financial "
    "sections, use Screens to find the High Growth, High RoE, Low PE filter, and "
    "verify a shortlist pick like Ganesh Infra."
)
DEMO_PROMPT = (
    "Go to screener.in and show how to choose stocks step by step: use the home-page "
    "search box to type Reliance Industries, click the visible match, review the key "
    "metrics, quarterly results, profit and loss, and balance sheet, then click Screens, "
    "click Show all screens, clearly point at the High Growth, High RoE, Low PE card, "
    "open it, compare the results, and drill into Ganesh Infra."
)

COMPANY_URLS = [
    "https://www.screener.in/company/RELIANCE/",
    "https://www.screener.in/company/500325/",
    "https://www.screener.in/company/RELIANCE/consolidated/",
]
PUBLIC_SCREENS_LIST_URLS = [
    "https://www.screener.in/explore/",
    "https://www.screener.in/screens/",
]
TARGET_SCREEN_URLS = [
    "https://www.screener.in/screens/328709/high-growth-high-roe-low-pe/",
    "https://www.screener.in/screens/18/high-growth-high-roe-low-pe/",
    "https://www.screener.in/screens/299408/high-growth/",
]

STEP_PREVIEW_HOLD_SEC = 0.28
PAGE_SETTLE_SEC = 0.95
SECTION_SETTLE_SEC = 1.0
SHORT_STEP_EXTRA_SETTLE_SEC = 0.45
RESULT_OPEN_SETTLE_SEC = 1.05
SYNC_LOG_WAIT_SEC = 0.12

RELIANCE_PATTERN = re.compile(r"Reliance Industries", re.IGNORECASE)
SCREENS_PATTERN = re.compile(r"^\s*Screens\s*$", re.IGNORECASE)
HIGH_GROWTH_SCREEN_PATTERN = re.compile(r"High\s*Growth.*High\s*RoE.*Low\s*PE", re.IGNORECASE)
HIGH_ROE_LOW_PE_PATTERN = re.compile(r"High\s*ROE\s*low\s*PE", re.IGNORECASE)
GANESH_INFRA_PATTERN = re.compile(r"Ganesh\s*Infra", re.IGNORECASE)


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


def wait_brief(seconds: float):
    """Sleep only when a positive delay is requested."""
    if seconds > 0:
        time.sleep(seconds)


def first_visible(*candidates: Locator, timeout_ms: int = 1600) -> Locator | None:
    """Return the first locator that becomes visibly usable."""
    for locator in candidates:
        try:
            candidate_count = min(locator.count(), 6)
        except Exception:
            candidate_count = 1

        if candidate_count <= 0:
            continue

        per_target_timeout = max(int(timeout_ms / max(candidate_count, 1)), 250)
        for index in range(candidate_count):
            try:
                target = locator.nth(index)
                if target.is_visible():
                    return target
                target.wait_for(state="visible", timeout=per_target_timeout)
                return target
            except Exception:
                continue
    return None


def focus_target(page, locator: Locator | None, settle_sec: float = 0.58) -> bool:
    """Put the visible pointer on a target so the recording clearly references it."""
    if locator is None:
        return False
    return point_at_locator(page, locator, settle_sec=settle_sec)


def emphasize_target(page, locator: Locator | None, settle_sec: float = 0.95) -> bool:
    """Use a brighter pointer plus a highlight box for especially important clicks."""
    if locator is None:
        return False
    return point_and_highlight_locator(page, locator, settle_sec=settle_sec)


def goto_first_working_url(page, urls: list[str]) -> str | None:
    """Open the first URL that does not render a 404 page."""
    for url in urls:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            wait_brief(0.55)
            if not is_404_page(page):
                return url
        except Exception:
            continue
    return None


def dismiss_site_noise(page):
    """Handle simple modal or banner interruptions without changing the visible layout."""
    try:
        page.keyboard.press("Escape")
        wait_brief(0.25)
    except Exception:
        pass


def scroll_page_top(page):
    """Bring the global navigation back into view."""
    try:
        page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' })")
        wait_brief(0.9)
    except Exception:
        page.keyboard.press("Home")
        wait_brief(0.8)


def screener_search_input(page) -> Locator | None:
    """Locate the main Screener search field on the home page."""
    return first_visible(
        page.locator('input[placeholder*="Search for a company" i]'),
        page.locator('input[placeholder*="Search" i]'),
        page.locator('input[type="search"]'),
        page.locator('input[name="q"]'),
        page.locator('input[id*="search" i]'),
        page.locator('input:not([type="hidden"])'),
        timeout_ms=4200,
    )


def target_screen_locator(page) -> Locator | None:
    """Locate the exact stock screen card/link we want to open."""
    return first_visible(
        page.get_by_role("link", name=HIGH_GROWTH_SCREEN_PATTERN),
        page.locator('a[href*="/screen/"]:has-text("High Growth High RoE Low PE")'),
        page.get_by_text("High ROE low PE", exact=False),
        timeout_ms=2200,
    )


def reliance_search_result(page) -> Locator | None:
    """Locate the Reliance Industries result shown after typing into the search box."""
    return first_visible(
        page.locator('a[href*="/company/RELIANCE/"]'),
        page.locator('a[href*="/company/500325/"]'),
        page.get_by_role("link", name=RELIANCE_PATTERN),
        page.get_by_text(RELIANCE_PATTERN),
        timeout_ms=5200,
    )


def show_all_screens_link(page) -> Locator | None:
    """Locate the link that expands the full public screen list."""
    return first_visible(
        page.get_by_role("link", name=re.compile(r"Show all screens", re.IGNORECASE)),
        page.locator('a:has-text("Show all screens")'),
        timeout_ms=2200,
    )


def search_and_open_reliance(page, logger, announce) -> bool:
    """Type Reliance into the visible search box, show the match, then open it."""
    search_input = screener_search_input(page)
    if not search_input:
        return False

    announce("Type Reliance Industries into the search box and wait for the visible match")
    emphasize_target(page, search_input, settle_sec=0.9)
    search_input.click()
    wait_brief(0.2)
    try:
        page.keyboard.press("Control+A")
        wait_brief(0.1)
        page.keyboard.press("Backspace")
    except Exception:
        pass
    page.keyboard.type("Reliance Industries", delay=115)
    wait_brief(0.9)

    result_link = reliance_search_result(page)
    if result_link:
        emphasize_target(page, result_link, settle_sec=1.0)
    else:
        focus_target(page, search_input, settle_sec=0.8)

    logger.log(
        page,
        "Type Reliance Industries into the search box and wait for the visible match",
        wait_sec=SYNC_LOG_WAIT_SEC,
        show_caption=False,
    )

    announce("Click Reliance Industries from the visible search results")
    result_link = reliance_search_result(page)
    result_href = ""
    if result_link:
        try:
            result_href = (result_link.get_attribute("href") or "").strip()
        except Exception:
            result_href = ""
        emphasize_target(page, result_link, settle_sec=0.92)
        try:
            result_link.click()
            page.wait_for_url(re.compile(r".*/company/(RELIANCE|500325)(/.*)?$"), timeout=12000)
        except Exception:
            if result_href:
                page.goto(urljoin("https://www.screener.in", result_href), wait_until="domcontentloaded", timeout=20000)
            else:
                page.keyboard.press("Enter")
    else:
        page.keyboard.press("Enter")

    try:
        page.wait_for_url(re.compile(r".*/company/.+"), timeout=15000)
    except Exception:
        opened = goto_first_working_url(page, COMPANY_URLS)
        if not opened:
            return False

    wait_brief(PAGE_SETTLE_SEC)
    company_header = first_visible(
        page.get_by_role("heading", name=RELIANCE_PATTERN),
        page.locator("h1"),
        timeout_ms=3000,
    )
    emphasize_target(page, company_header, settle_sec=0.92)
    logger.log(
        page,
        "Click Reliance Industries from the visible search results",
        wait_sec=SYNC_LOG_WAIT_SEC,
        show_caption=False,
    )
    return True


def log_metric_snapshot(page, logger, announce):
    """Hold on the key metric block near the company header."""
    announce("View key metrics - market cap, PE ratio, ROCE, and valuation snapshot")
    wait_brief(SHORT_STEP_EXTRA_SETTLE_SEC)
    metric_focus = first_visible(
        page.locator('li:has-text("Market Cap")'),
        page.locator('li:has-text("Stock P/E")'),
        page.locator('li:has-text("ROCE")'),
        page.get_by_text("Market Cap", exact=False),
        timeout_ms=2200,
    )
    focus_target(page, metric_focus, settle_sec=0.62)
    logger.log(
        page,
        "View key metrics - market cap, PE ratio, ROCE, and valuation snapshot",
        wait_sec=SYNC_LOG_WAIT_SEC,
        show_caption=False,
    )


def open_section(page, logger, announce, description: str, tab: Locator | None, focus_locator: Locator | None, scroll_pixels: int):
    """Open a section tab, or scroll to it, then pause on a clearly visible target."""
    announce(description)
    if tab:
        focus_target(page, tab, settle_sec=0.55)
        tab.click()
        wait_brief(SECTION_SETTLE_SEC)
    else:
        if focus_locator:
            try:
                focus_locator.scroll_into_view_if_needed(timeout=5000)
                wait_brief(0.75)
            except Exception:
                slow_scroll(page, scroll_pixels, 5)
                wait_brief(0.65)
        else:
            slow_scroll(page, scroll_pixels, 5)
            wait_brief(0.65)

    focus_target(page, focus_locator, settle_sec=0.62)
    logger.log(page, description, wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)


def open_public_screens(page, logger, announce) -> bool:
    """Use the visible top navigation first, then fall back to the direct Screens pages."""
    announce("Click Screens in the top menu to explore ready-made stock filters")
    scroll_page_top(page)

    screens_link = first_visible(
        page.get_by_role("link", name=SCREENS_PATTERN),
        page.locator('a:has-text("Screens")'),
        timeout_ms=2200,
    )

    opened_from_ui = False
    if screens_link:
        emphasize_target(page, screens_link, settle_sec=0.88)
        try:
            screens_link.click()
            try:
                page.wait_for_url(re.compile(r".*/(explore|screens)/.*"), timeout=20000)
            except Exception:
                page.wait_for_load_state("domcontentloaded", timeout=12000)
            wait_brief(PAGE_SETTLE_SEC)
            opened_from_ui = not is_404_page(page)
        except Exception:
            opened_from_ui = False

    if not opened_from_ui:
        opened = goto_first_working_url(page, PUBLIC_SCREENS_LIST_URLS)
        if not opened:
            return False
        wait_brief(PAGE_SETTLE_SEC)

    screen_library_focus = first_visible(
        page.get_by_role("heading", name=re.compile(r"Stock screens", re.IGNORECASE)),
        page.get_by_role("link", name=re.compile(r"Show all screens", re.IGNORECASE)),
        page.get_by_text("Popular stock screens", exact=False),
        timeout_ms=2500,
    )
    focus_target(page, screen_library_focus, settle_sec=0.62)
    logger.log(
        page,
        "Click Screens in the top menu to explore ready-made stock filters",
        wait_sec=SYNC_LOG_WAIT_SEC,
        show_caption=False,
    )
    return True


def open_all_screens_list(page, logger, announce) -> bool:
    """Move from the curated explore page into the full public screen list."""
    announce("Click Show all screens to open the full screen library")
    all_screens_link = show_all_screens_link(page)
    if not all_screens_link:
        return False

    emphasize_target(page, all_screens_link, settle_sec=0.95)
    all_screens_link.click()
    try:
        page.wait_for_url(re.compile(r".*/screens/?$"), timeout=20000)
    except Exception:
        page.wait_for_load_state("domcontentloaded", timeout=12000)
    wait_brief(PAGE_SETTLE_SEC)

    list_heading = first_visible(
        page.get_by_role("heading", name=re.compile(r"Popular Stock Screens", re.IGNORECASE)),
        page.locator("h1"),
        timeout_ms=2500,
    )
    emphasize_target(page, list_heading, settle_sec=0.9)
    logger.log(
        page,
        "Click Show all screens to open the full screen library",
        wait_sec=SYNC_LOG_WAIT_SEC,
        show_caption=False,
    )
    return True


def highlight_target_screen(page, logger, announce) -> bool:
    """Show the exact screen card before clicking it so the task is easy to follow."""
    announce("Find the exact High Growth, High RoE, Low PE card in the full screen list")
    target_link = target_screen_locator(page)
    if not target_link:
        return False

    emphasize_target(page, target_link, settle_sec=1.05)
    logger.log(
        page,
        "Find the exact High Growth, High RoE, Low PE card in the full screen list",
        wait_sec=SYNC_LOG_WAIT_SEC,
        show_caption=False,
    )
    return True


def open_target_screen(page, logger, announce) -> bool:
    """Open the exact prebuilt screen named in the narration, or fall back to its stable URL."""
    announce("Click the highlighted High Growth, High RoE, Low PE card")
    target_link = target_screen_locator(page)

    if target_link:
        emphasize_target(page, target_link, settle_sec=0.9)
        target_link.click()
        try:
            page.wait_for_url(re.compile(r".*/screens/.+"), timeout=20000)
        except Exception:
            page.wait_for_load_state("domcontentloaded", timeout=12000)
        wait_brief(SECTION_SETTLE_SEC)
    else:
        opened = goto_first_working_url(page, TARGET_SCREEN_URLS)
        if not opened:
            return False
        wait_brief(SECTION_SETTLE_SEC)

    screen_title = first_visible(
        page.get_by_role("heading", name=HIGH_GROWTH_SCREEN_PATTERN),
        page.get_by_text(HIGH_ROE_LOW_PE_PATTERN),
        page.locator("h1"),
        timeout_ms=2400,
    )
    focus_target(page, screen_title, settle_sec=0.62)
    logger.log(
        page,
        "Click the highlighted High Growth, High RoE, Low PE card",
        wait_sec=SYNC_LOG_WAIT_SEC,
        show_caption=False,
    )
    return True


def browse_screen_results(page, logger, announce):
    """Pause on the visible results table and the Ganesh Infra row when it exists."""
    announce("Scan the filtered results table and spot promising names like Ganesh Infra")
    results_table = first_visible(page.locator("table"), timeout_ms=2200)
    if results_table:
        try:
            results_table.scroll_into_view_if_needed(timeout=5000)
            wait_brief(0.7)
        except Exception:
            slow_scroll(page, 220, 3)
            wait_brief(0.45)
    else:
        slow_scroll(page, 240, 3)
        wait_brief(0.45)

    row_focus = first_visible(
        page.get_by_role("link", name=GANESH_INFRA_PATTERN),
        page.locator('table a[href*="/company/"]').first,
        page.locator("table"),
        timeout_ms=2400,
    )
    emphasize_target(page, row_focus, settle_sec=0.95)
    logger.log(
        page,
        "Scan the filtered results table and spot promising names like Ganesh Infra",
        wait_sec=SYNC_LOG_WAIT_SEC,
        show_caption=False,
    )


def open_company_from_screen(page, logger, announce):
    """Open Ganesh Infra from the screen if it is visible, otherwise use the first company row."""
    announce("Click Ganesh Infra from the results and land on the company page")
    company_link = first_visible(
        page.get_by_role("link", name=GANESH_INFRA_PATTERN),
        page.locator('table a[href*="/company/"]').first,
        timeout_ms=2600,
    )
    if not company_link:
        logger.log(
            page,
            "Open a shortlisted company from the screen for deeper analysis",
            wait_sec=SYNC_LOG_WAIT_SEC,
            show_caption=False,
        )
        return

    company_name = (company_link.text_content() or "").strip() or "Ganesh Infra"
    company_href = (company_link.get_attribute("href") or "").strip()
    emphasize_target(page, company_link, settle_sec=0.95)

    try:
        page.evaluate("(element) => { if (element) { element.removeAttribute('target'); } }", company_link)
    except Exception:
        pass

    navigated = False
    try:
        company_link.click()
        page.wait_for_url(re.compile(r".*/company/.+"), timeout=6000)
        navigated = True
    except Exception:
        navigated = False

    if not navigated and company_href:
        page.goto(urljoin("https://www.screener.in", company_href), wait_until="domcontentloaded", timeout=20000)

    wait_brief(RESULT_OPEN_SETTLE_SEC)

    company_focus = first_visible(
        page.get_by_role("heading", name=GANESH_INFRA_PATTERN),
        page.locator("h1"),
        timeout_ms=3000,
    )
    emphasize_target(page, company_focus, settle_sec=0.9)
    logger.log(
        page,
        f"Click {company_name} from the results and land on the company page",
        wait_sec=SYNC_LOG_WAIT_SEC,
        show_caption=False,
    )


def run():
    print(f"\n{'=' * 60}")
    print("  RECORDING: Screener.in Stock Research Tutorial")
    print(f"{'=' * 60}\n")

    with sync_playwright() as playwright:
        browser, context, page = create_browser_context(playwright, DEMO_NAME)
        logger = StepLogger(DEMO_NAME)

        try:
            def announce(description: str):
                logger.preview(page, description, hold_sec=STEP_PREVIEW_HOLD_SEC)

            page.goto("https://www.screener.in/", wait_until="domcontentloaded", timeout=30000)
            wait_brief(PAGE_SETTLE_SEC)
            dismiss_site_noise(page)

            home_focus = screener_search_input(page) or first_visible(
                page.get_by_role("link", name=SCREENS_PATTERN),
                page.locator("h1"),
                timeout_ms=2200,
            )
            focus_target(page, home_focus, settle_sec=0.62)
            logger.log(
                page,
                "Open Screener.in and bring the stock search page into view",
                wait_sec=SYNC_LOG_WAIT_SEC,
                show_caption=False,
            )

            if not search_and_open_reliance(page, logger, announce):
                raise RuntimeError("Could not select and open Reliance Industries from search.")

            log_metric_snapshot(page, logger, announce)

            open_section(
                page,
                logger,
                announce,
                "Review quarterly financial trends to understand recent performance",
                first_visible(
                    page.get_by_role("link", name=re.compile(r"Quarters|Quarterly", re.IGNORECASE)),
                    page.locator('a:has-text("Quarters")'),
                    timeout_ms=1500,
                ),
                first_visible(
                    page.get_by_text("Quarterly Results", exact=False),
                    page.locator("text=Quarterly Results"),
                    timeout_ms=1800,
                ),
                scroll_pixels=520,
            )

            open_section(
                page,
                logger,
                announce,
                "Inspect Profit and Loss details - revenue, expenses, and margins",
                first_visible(
                    page.get_by_role("link", name=re.compile(r"Profit\s*&\s*Loss|P&L", re.IGNORECASE)),
                    page.locator('a:has-text("Profit & Loss")'),
                    timeout_ms=1500,
                ),
                first_visible(
                    page.get_by_text("Profit & Loss", exact=False),
                    page.locator("text=Profit & Loss"),
                    timeout_ms=1800,
                ),
                scroll_pixels=500,
            )

            open_section(
                page,
                logger,
                announce,
                "Check balance sheet strength - assets, liabilities, and equity",
                first_visible(
                    page.get_by_role("link", name=re.compile(r"Balance\s*Sheet|Balance", re.IGNORECASE)),
                    page.locator('a:has-text("Balance Sheet")'),
                    timeout_ms=1500,
                ),
                first_visible(
                    page.get_by_text("Balance Sheet", exact=False),
                    page.locator("text=Balance Sheet"),
                    timeout_ms=1800,
                ),
                scroll_pixels=460,
            )

            if not open_public_screens(page, logger, announce):
                raise RuntimeError("Screens page was not reachable.")

            if not open_all_screens_list(page, logger, announce):
                raise RuntimeError("Show all screens link was not reachable.")

            if not highlight_target_screen(page, logger, announce):
                raise RuntimeError("Could not find the exact High Growth, High RoE, Low PE card.")

            if not open_target_screen(page, logger, announce):
                raise RuntimeError("Target stock screen was not reachable.")

            browse_screen_results(page, logger, announce)
            open_company_from_screen(page, logger, announce)

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
