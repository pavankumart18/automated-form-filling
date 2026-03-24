"""
demo_mondula_form.py - Mondula Multi Step Form demo.
Workflow: navigate multi-page form and fill 6+ real inputs across steps.
"""

import os
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(__file__))
from common import create_browser_context, StepLogger, finish_recording

DEMO_NAME = "mondula_form"
DEMO_DESCRIPTION = (
    "Complete a real multi-page form on Mondula's demo using text, date, radio, "
    "checkbox, dropdown, and contact inputs."
)
DEMO_PROMPT = (
    "Go to mondula.com/msf-demo, complete each step, fill at least six fields, "
    "and reach the submit-ready final state."
)


def pause(seconds: float = 0.6):
    time.sleep(seconds)


def is_visible(page, selector: str) -> bool:
    try:
        return page.locator(selector).first.is_visible()
    except Exception:
        return False


def dismiss_cookie_banner(page):
    for label in ["Accept", "Save preferences", "Allow all", "Deny"]:
        buttons = page.locator(f'button:has-text("{label}")')
        for idx in range(buttons.count()):
            candidate = buttons.nth(idx)
            try:
                if candidate.is_visible():
                    candidate.click()
                    pause(0.8)
                    return
            except Exception:
                continue


def click_next_step(page) -> bool:
    next_btn = page.locator(
        'button:has-text("NEXT STEP"), input[value="NEXT STEP"], a:has-text("NEXT STEP")'
    )
    for idx in range(next_btn.count()):
        candidate = next_btn.nth(idx)
        try:
            if candidate.is_visible():
                candidate.scroll_into_view_if_needed()
                candidate.click(force=True)
                pause(1.0)
                return True
        except Exception:
            continue
    return False


def advance_to_step(page, expected_selector: str, max_attempts: int = 3) -> bool:
    for _ in range(max_attempts):
        if is_visible(page, expected_selector):
            return True
        click_next_step(page)
        pause(0.8)
        if is_visible(page, expected_selector):
            return True
    return is_visible(page, expected_selector)


def set_text(page, selector: str, value: str, delay: int = 70, nth: int = 0) -> bool:
    field = page.locator(selector).nth(nth)
    try:
        if field.is_visible():
            field.scroll_into_view_if_needed()
            field.click(force=True)
            try:
                field.press("Control+A")
                field.press("Delete")
            except Exception:
                pass
            field.type(value, delay=delay)
            pause(0.2)
            return True
    except Exception:
        pass

    try:
        page.evaluate(
            """
            ([sel, val, idx]) => {
              const all = document.querySelectorAll(sel);
              if (!all || all.length === 0) return false;
              const el = all[Math.min(idx, all.length - 1)];
              el.value = val;
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
              return true;
            }
            """,
            [selector, value, nth],
        )
        pause(0.2)
        return True
    except Exception:
        return False


def set_text_all(page, selector: str, values: list[str]):
    for idx, value in enumerate(values):
        set_text(page, selector, value, nth=idx)


def check_input(page, selector: str) -> bool:
    target = page.locator(selector).first
    try:
        if target.is_visible():
            target.scroll_into_view_if_needed()
            target.check(force=True)
            pause(0.2)
            return True
    except Exception:
        pass

    try:
        page.evaluate(
            """
            (sel) => {
              const el = document.querySelector(sel);
              if (!el) return false;
              el.checked = true;
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
              return true;
            }
            """,
            selector,
        )
        pause(0.2)
        return True
    except Exception:
        return False


def select_index(page, selector: str, index: int = 1) -> bool:
    field = page.locator(selector).first
    try:
        if field.is_visible():
            field.scroll_into_view_if_needed()
            field.select_option(index=index)
            pause(0.3)
            return True
    except Exception:
        pass

    try:
        page.evaluate(
            """
            ([sel, idx]) => {
              const el = document.querySelector(sel);
              if (!el || !el.options || el.options.length <= idx) return false;
              el.selectedIndex = idx;
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
              return true;
            }
            """,
            [selector, index],
        )
        pause(0.3)
        return True
    except Exception:
        return False


def run():
    print(f"\n{'='*60}")
    print("  RECORDING: Mondula Multi Step Form Tutorial")
    print(f"{'='*60}\n")

    with sync_playwright() as p:
        browser, context, page = create_browser_context(p, DEMO_NAME)
        logger = StepLogger(DEMO_NAME)

        try:
            # Step 1
            page.goto("https://mondula.com/msf-demo/", wait_until="networkidle", timeout=45000)
            dismiss_cookie_banner(page)
            logger.log(page, "Open the Mondula multi-step form demo page")

            # Step 2
            advance_to_step(page, "#msf-text-example-textfield", max_attempts=4)
            logger.log(page, "Move from the intro page to the first form step")

            # Step 3
            set_text(page, "#msf-text-example-textfield", "Pavan Demo")
            set_text(
                page,
                "#msf-textarea-example-textarea",
                "Testing a multi-page form automation workflow.",
            )
            logger.log(page, "Fill first page text and textarea fields")

            # Step 4
            advance_to_step(page, "#msf-date-date-field-with-calender-popup", max_attempts=4)
            logger.log(page, "Go to the next page with additional input fields")

            # Step 5
            set_text_all(page, "#msf-text-simple-text-field", ["Automation Field Value", "Second Value"])
            set_text(page, "#msf-textarea-custom-textarea", "This section demonstrates long-form answers.")
            set_text(page, "#msf-date-date-field-with-calender-popup", "03/13/2026")
            logger.log(page, "Fill text, custom textarea, and date fields on page two")

            # Step 6
            advance_to_step(page, "#fw-12-3-0-0-1", max_attempts=4)
            logger.log(page, "Proceed to radio, checkbox, and dropdown inputs")

            # Step 7
            check_input(page, "#fw-12-3-0-0-2")
            check_input(page, "#fw-12-3-1-0-2")
            check_input(page, "#fw-12-3-1-0-5")
            select_index(page, "#msf-select-please-choose-a-option-from-the-list", 2)
            logger.log(page, "Select a radio option, multiple checkboxes, and a dropdown value")

            # Step 8
            advance_to_step(page, "#msf-select-dish", max_attempts=4)
            logger.log(page, "Open the conditional input section")

            # Step 9
            select_index(page, "#msf-select-dish", 1)  # Pizza
            check_input(page, "#fw-12-4-0-1-2")
            check_input(page, "#fw-12-4-0-2-2")
            check_input(page, "#fw-12-4-0-2-4")
            check_input(page, "#fw-12-4-0-3-2")
            check_input(page, "#fw-12-4-0-4-2")
            logger.log(page, "Fill conditional fields based on the selected dish")

            # Step 10
            advance_to_step(page, "#msf-text-first-name", max_attempts=4)
            logger.log(page, "Move to the final contact-details page")

            # Step 11
            set_text(page, "#msf-text-first-name", "Pavan")
            set_text(page, "#msf-text-last-name", "Kumar")
            set_text(page, "#msf-date-date-of-birth", "03/13/1992")
            set_text(page, "#msf-text-telephone", "9876543210")
            set_text(page, "#msf-mail-email", "pavan@example.com")
            set_text(
                page,
                "#msf-textarea-feel-free-to-write-a-short-message",
                "Please share plugin implementation details for production usage.",
            )
            logger.log(page, "Fill final contact page with six required input fields")

            # Step 12
            summary_btn = page.locator('button:has-text("SHOW SUMMARY"), a:has-text("SHOW SUMMARY")').first
            if summary_btn.is_visible():
                summary_btn.click()
                pause(0.8)

            if not is_visible(page, 'button:has-text("Submit"), input[type="submit"]'):
                # One extra step if summary hides the submit area.
                click_next_step(page)
                pause(0.6)

            logger.show_caption(page, "Form is complete and ready for submit.")
            logger.log(page, "Review summary and reach submit-ready final state", wait_sec=0.8)

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
