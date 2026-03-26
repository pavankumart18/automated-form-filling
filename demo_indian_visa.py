"""
demo_indian_visa.py - Indian eVisa form walkthrough (safe dummy data).

This demo intentionally avoids any captcha bypass or final submission.
It fills the first page with fake data and stops before captcha by default.
Optionally, you can pass --captcha=<text> for manual-assisted continuation.
"""

import os
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(__file__))
from common import create_browser_context, StepLogger, finish_recording

DEMO_NAME = "indian_visa"
DEMO_DESCRIPTION = (
    "Walk through the Indian eVisa application start page with dummy data, "
    "showing key required fields and safe stopping before final submission."
)
DEMO_PROMPT = (
    "Open indianvisaonline.gov.in eVisa application, fill fake applicant details, "
    "and stop safely before final submission."
)
STEP_PREVIEW_HOLD_SEC = 0.85
SYNC_LOG_WAIT_SEC = 0.1
STEP_EXTRA_SETTLE_SEC = 0.9
SHORT_STEP_EXTRA_SETTLE_SEC = 1.1
FINAL_PREVIEW_HOLD_SEC = 1.5


def pause(seconds: float = 0.7):
    time.sleep(seconds)


def goto_with_retry(page, url: str, attempts: int = 3):
    last_error = None
    for _ in range(attempts):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            return
        except Exception as error:
            last_error = error
            pause(1.5)
    if last_error:
        raise last_error


def parse_captcha_arg() -> tuple[str | None, bool]:
    prompt_mode = False
    for arg in sys.argv[1:]:
        if arg == "--prompt-captcha":
            prompt_mode = True
        if arg.startswith("--captcha="):
            value = arg.split("=", 1)[1].strip()
            return (value if value else None), prompt_mode
    return None, prompt_mode


def close_modal_overlays(page):
    # Remove any startup modal/backdrop that blocks clicks.
    try:
        page.evaluate(
            """
            () => {
              document.querySelectorAll('#prodInvestmentBanner, .modal-backdrop')
                .forEach((el) => el.remove());
            }
            """
        )
    except Exception:
        pass

    close_buttons = page.locator('button:has-text("CLOSE"), button.close')
    for idx in range(close_buttons.count()):
        button = close_buttons.nth(idx)
        try:
            if button.is_visible():
                button.click(force=True)
                pause(0.5)
                break
        except Exception:
            continue


def close_runtime_dialogs(page):
    """Close runtime dialogs like 'Nationality selected' popups."""
    # jQuery UI dialog buttons
    dialog_buttons = page.locator(
        '.ui-dialog button:has-text("Ok"), '
        '.ui-dialog button:has-text("OK"), '
        '.ui-dialog button:has-text("Close"), '
        'button:has-text("Ok"), '
        'button:has-text("OK"), '
        'button:has-text("Close")'
    )
    for idx in range(dialog_buttons.count()):
        button = dialog_buttons.nth(idx)
        try:
            if button.is_visible():
                button.click(force=True)
                pause(0.5)
                break
        except Exception:
            continue

    # Remove stuck overlays if any remain.
    try:
        page.evaluate(
            """
            () => {
              document.querySelectorAll('.ui-widget-overlay, .modal-backdrop')
                .forEach((el) => el.remove());
            }
            """
        )
    except Exception:
        pass


def safe_select_option(page, selector: str, preferred_labels: list[str]):
    # Try exact labels first, then first non-placeholder option.
    for label in preferred_labels:
        option = page.locator(f'{selector} option:has-text("{label}")')
        if option.count() > 0:
            try:
                page.select_option(selector, label=label)
                pause(0.3)
                close_runtime_dialogs(page)
                return
            except Exception:
                pass

    try:
        page.select_option(selector, index=1)
    except Exception:
        pass
    pause(0.3)
    close_runtime_dialogs(page)


def set_text(page, selector: str, value: str):
    field = page.locator(selector).first
    try:
        field.fill(value)
        pause(0.2)
        return
    except Exception:
        pass

    try:
        page.evaluate(
            """
            ([sel, val]) => {
              const el = document.querySelector(sel);
              if (!el) return false;
              el.value = val;
              el.dispatchEvent(new Event('input', { bubbles: true }));
              el.dispatchEvent(new Event('change', { bubbles: true }));
              return true;
            }
            """,
            [selector, value],
        )
    except Exception:
        pass
    pause(0.2)


def set_checkbox(page, selector: str):
    box = page.locator(selector).first
    try:
        if box.is_visible():
            box.check(force=True)
            pause(0.2)
            return
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
    except Exception:
        pass
    pause(0.2)


def run():
    captcha_code, prompt_captcha = parse_captcha_arg()

    print(f"\n{'='*60}")
    print("  RECORDING: Indian eVisa Application Walkthrough")
    print(f"{'='*60}\n")

    with sync_playwright() as p:
        browser, context, page = create_browser_context(p, DEMO_NAME)
        logger = StepLogger(DEMO_NAME)

        try:
            def announce(description: str, hold_sec: float = STEP_PREVIEW_HOLD_SEC):
                logger.preview(page, description, hold_sec=hold_sec)

            # Step 1
            goto_with_retry(page, "https://indianvisaonline.gov.in/evisa/tvoa.html", attempts=4)
            pause(1.2)
            logger.log(page, "Open the Indian eVisa portal home page")

            # Step 2
            announce("Open the eVisa application form start page")
            close_modal_overlays(page)
            page.get_by_text("Apply here for e-visa", exact=True).click(force=True)
            page.wait_for_load_state("domcontentloaded")
            pause(1.2)
            logger.log(page, "Open the eVisa application form start page", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 3
            announce("Select nationality and passport type for the applicant")
            safe_select_option(page, "#nationality_id", ["UNITED STATES OF AMERICA", "USA", "AMERICAN"])
            safe_select_option(page, "#ppt_type_id", ["ORDINARY PASSPORT", "Ordinary Passport"])
            pause(STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Select nationality and passport type for the applicant", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 4
            announce("Choose the port of arrival for the application")
            safe_select_option(page, "#missioncode_id", ["Delhi", "NEW DELHI"])
            pause(SHORT_STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Choose the port of arrival for the application", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 5
            announce("Fill date of birth and email confirmation")
            set_text(page, "#dob_id", "15/03/1990")
            set_text(page, "#email_id", "john.smith.demo@example.com")
            set_text(page, "#email_re_id", "john.smith.demo@example.com")
            pause(STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Fill date of birth and email confirmation", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 6
            announce("Choose visa service: eTourist Visa (30 Days)")
            set_checkbox(page, 'input[name="evisa_service"][value="31"]')
            pause(SHORT_STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Choose visa service: eTourist Visa (30 Days)", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 7
            announce("Set expected date of arrival and acknowledge instructions")
            # journey date is readonly, set via script and dispatch change.
            try:
                page.evaluate(
                    """
                    () => {
                      const el = document.querySelector('#jouryney_id');
                      if (!el) return;
                      el.value = '15/05/2026';
                      el.dispatchEvent(new Event('input', { bubbles: true }));
                      el.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                    """
                )
            except Exception:
                pass
            set_checkbox(page, "#read_instructions_check")
            pause(SHORT_STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Set expected date of arrival and acknowledge instructions", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 8
            announce("Stop at captcha step for safe, non-submitting demo", hold_sec=FINAL_PREVIEW_HOLD_SEC)
            logger.log(page, "Stop at captcha step for safe, non-submitting demo", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Optional manual-assisted continuation.
            if prompt_captcha and not captcha_code:
                try:
                    captcha_code = input("Enter captcha shown in browser (or press Enter to skip): ").strip() or None
                except Exception:
                    captcha_code = None

            if captcha_code:
                set_text(page, "#captcha", captcha_code)
                continue_button = page.locator('input[value="Continue"], button:has-text("Continue")').first
                if continue_button.is_visible():
                    continue_button.click(force=True)
                    pause(2.0)
                    logger.log(page, "Manual captcha entered and Continue clicked", wait_sec=0.6)
                else:
                    logger.log(page, "Continue button not found after captcha input", wait_sec=0.6)

        except Exception as error:
            print(f"\nERROR during recording: {error}")
            try:
                if not page.is_closed():
                    logger.log(page, f"Error encountered: {str(error)[:80]}", wait_sec=0)
            except Exception:
                pass

        finally:
            logger.save()
            logger.save_transcript()
            finish_recording(browser, context, DEMO_NAME, page)

    return DEMO_NAME, DEMO_DESCRIPTION, DEMO_PROMPT


if __name__ == "__main__":
    run()
