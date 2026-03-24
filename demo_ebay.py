"""
demo_ebay.py - eBay advanced search demo.
"""

import os
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(__file__))
from common import StepLogger, create_browser_context, finish_recording

DEMO_NAME = "ebay_advanced"
DEMO_DESCRIPTION = (
    "Fill eBay Advanced Search with keywords, exclusions, price limits, and "
    "condition filters to run a real marketplace query."
)
DEMO_PROMPT = (
    "Go to eBay advanced search, fill multiple fields, set filters, and run the search."
)


def pause(seconds: float = 0.8):
    time.sleep(seconds)


def inject_visual_helpers(page):
    try:
        page.evaluate(
            """
            () => {
                if (window.__ebayVisualHelpersReady) return;
                window.__ebayVisualHelpersReady = true;

                const banner = document.createElement('div');
                banner.id = 'ai-agent-banner';
                banner.style.position = 'fixed';
                banner.style.top = '24px';
                banner.style.left = '50%';
                banner.style.transform = 'translateX(-50%)';
                banner.style.backgroundColor = 'rgba(16, 185, 129, 0.95)';
                banner.style.color = 'white';
                banner.style.padding = '14px 28px';
                banner.style.borderRadius = '12px';
                banner.style.fontFamily = 'Segoe UI, Roboto, Helvetica, sans-serif';
                banner.style.fontSize = '18px';
                banner.style.fontWeight = 'bold';
                banner.style.zIndex = '999999';
                banner.style.boxShadow = '0 10px 25px rgba(0,0,0,0.2)';
                banner.style.transition = 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
                banner.style.opacity = '0';
                banner.style.pointerEvents = 'none';
                document.body.appendChild(banner);

                const cursor = document.createElement('div');
                cursor.id = 'ai-cursor';
                cursor.style.position = 'fixed';
                cursor.style.width = '24px';
                cursor.style.height = '24px';
                cursor.style.borderRadius = '50%';
                cursor.style.backgroundColor = 'rgba(59, 130, 246, 0.3)';
                cursor.style.border = '3px solid #3B82F6';
                cursor.style.zIndex = '999998';
                cursor.style.pointerEvents = 'none';
                cursor.style.transition = 'top 0.15s ease-out, left 0.15s ease-out';
                cursor.style.transform = 'translate(-50%, -50%)';
                cursor.style.display = 'none';
                document.body.appendChild(cursor);

                document.addEventListener('mousemove', (e) => {
                    cursor.style.left = e.clientX + 'px';
                    cursor.style.top = e.clientY + 'px';
                    cursor.style.display = 'block';
                });

                document.addEventListener('click', (e) => {
                    const click = document.createElement('div');
                    click.style.position = 'fixed';
                    click.style.left = e.clientX + 'px';
                    click.style.top = e.clientY + 'px';
                    click.style.width = '20px';
                    click.style.height = '20px';
                    click.style.borderRadius = '50%';
                    click.style.backgroundColor = 'rgba(59, 130, 246, 0.8)';
                    click.style.transform = 'translate(-50%, -50%) scale(1)';
                    click.style.transition = 'transform 0.5s ease-out, opacity 0.5s ease-out';
                    click.style.zIndex = '999997';
                    click.style.pointerEvents = 'none';
                    document.body.appendChild(click);

                    requestAnimationFrame(() => {
                        click.style.transform = 'translate(-50%, -50%) scale(3.5)';
                        click.style.opacity = '0';
                    });

                    setTimeout(() => click.remove(), 500);
                });
            }
            """
        )
    except Exception:
        pass


def show_banner(page, text):
    try:
        page.evaluate(
            """
            (msg) => {
                const el = document.getElementById('ai-agent-banner');
                if (!el) return;

                el.innerText = msg;
                el.style.opacity = '1';
                el.style.transform = 'translateX(-50%) scale(1.05)';

                setTimeout(() => {
                    el.style.transform = 'translateX(-50%) scale(1)';
                }, 150);

                setTimeout(() => {
                    el.style.opacity = '0';
                    el.style.transform = 'translateX(-50%) translateY(-10px)';
                }, 2500);
            }
            """,
            text,
        )
    except Exception:
        pass


def robust_fill(page, selectors, value):
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if locator.count() > 0 and locator.is_visible():
                locator.scroll_into_view_if_needed()
                locator.click(force=True)
                locator.fill(value)
                pause(0.4)
                return True
        except Exception:
            continue
    return False


def robust_check(page, selector_text):
    selectors = [
        f"label:has-text('{selector_text}')",
        f"span:has-text('{selector_text}')",
        f"div:has-text('{selector_text}')",
    ]
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if locator.count() > 0 and locator.is_visible():
                locator.scroll_into_view_if_needed()
                locator.click(force=True)
                pause(0.4)
                return True
        except Exception:
            continue
    return False


def click_search(page):
    selectors = [
        'button:has-text("Search")',
        'input[type="submit"][value*="Search" i]',
        '[aria-label*="Search" i]',
    ]
    for selector in selectors:
        locator = page.locator(selector)
        try:
            for idx in range(locator.count()):
                candidate = locator.nth(idx)
                if candidate.is_visible():
                    candidate.scroll_into_view_if_needed()
                    candidate.click(force=True)
                    pause(0.8)
                    return True
        except Exception:
            continue

    try:
        page.keyboard.press("Enter")
        pause(0.8)
        return True
    except Exception:
        return False


def run():
    print(f"\n{'='*60}")
    print("  RECORDING: eBay Advanced Search Automation")
    print(f"{'='*60}\n")

    with sync_playwright() as p:
        browser, context, page = create_browser_context(p, DEMO_NAME)
        logger = StepLogger(DEMO_NAME)
        page.on("load", lambda *_: inject_visual_helpers(page))

        try:
            page.goto("https://www.ebay.com/sch/ebayadvsearch", wait_until="domcontentloaded", timeout=60000)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            inject_visual_helpers(page)
            logger.log(page, "Open eBay Advanced Search")

            show_banner(page, "Step 2: Entering primary keywords")
            robust_fill(
                page,
                ["#_nkw", "input[data-testid='_nkw']", "[name='_nkw']"],
                "Sony WH-1000XM5",
            )
            logger.log(page, "Enter main search keywords")

            show_banner(page, "Step 3: Matching exact words in exact order")
            dropdown = page.locator("select[name='_in_kw']").first
            if dropdown.count() > 0:
                dropdown.scroll_into_view_if_needed()
                dropdown.select_option(label="Exact words, exact order")
                pause(0.6)
            logger.log(page, "Change the keyword match dropdown to exact order")

            show_banner(page, "Step 4: Excluding damaged listings")
            robust_fill(
                page,
                ["#_ex_kw", "input[data-testid='_ex_kw']", "[name='_ex_kw']"],
                "broken parts only",
            )
            logger.log(page, "Enter words to exclude from results")

            show_banner(page, "Step 5: Expanding search into descriptions")
            robust_check(page, "Title and description")
            logger.log(page, "Include title and description in the search scope")

            show_banner(page, "Step 6: Applying the price window")
            robust_fill(page, ["input[name='_udlo']", "#adv_search_from"], "150")
            robust_fill(page, ["input[name='_udhi']", "#adv_search_to"], "400")
            logger.log(page, "Set minimum and maximum price filters")

            show_banner(page, "Step 7: Keeping only new-condition items")
            robust_check(page, "New")
            logger.log(page, "Filter for new-condition items")

            show_banner(page, "Step 8: Running the advanced search")
            click_search(page)
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            pause(2.5)
            inject_visual_helpers(page)
            logger.show_caption(page, "Filtered results are now visible.")
            logger.log(page, "Run the search and open the filtered results page", wait_sec=0.5)

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
