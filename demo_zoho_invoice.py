"""
demo_zoho_invoice.py - Zoho Invoice tutorial automation.
Flow: open free generator -> fill invoice -> review totals -> download.
"""

import os
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(__file__))
from common import create_browser_context, StepLogger, finish_recording

DEMO_NAME = "zoho_invoice"
DEMO_DESCRIPTION = (
    "Create a professional GST invoice on Zoho Invoice by filling company details, "
    "client details, line items, and downloading as PDF."
)
DEMO_PROMPT = (
    "Open Zoho free invoice generator, create an invoice for Acme Corp with 3 line items, "
    "review tax totals, and download it."
)
STEP_PREVIEW_HOLD_SEC = 0.9
SYNC_LOG_WAIT_SEC = 0.1
FIELD_TYPE_DELAY_MS = 72
FIELD_SETTLE_SEC = 0.35
STEP_EXTRA_SETTLE_SEC = 1.0
SHORT_STEP_EXTRA_SETTLE_SEC = 1.25
FINAL_PREVIEW_HOLD_SEC = 1.7


def wait_short(seconds: float = 0.6):
    time.sleep(seconds)


def dismiss_blockers(page):
    """Remove nav drawers/popups/chat that can intercept input clicks."""
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass
    wait_short(0.2)

    try:
        page.evaluate(
            """
            () => {
              document.querySelectorAll('.navbar.open').forEach(el => el.classList.remove('open'));
              document.querySelectorAll('.modal-backdrop, .overlay, .menu-overlay, .navbar-overlay')
                .forEach(el => el.remove());
              document.body.classList.remove('menu-open', 'nav-open', 'overflow-hidden');
              const chat = document.querySelector('#zsiq_float, .zsiq_floatmain, .zsiq_cnt');
              if (chat) chat.style.display = 'none';
              const signupModal = document.querySelector('#signupModalTemp');
              if (signupModal) signupModal.style.display = 'none';
            }
            """
        )
    except Exception:
        pass


def type_field(page, selector: str, value: str, delay: int = FIELD_TYPE_DELAY_MS) -> bool:
    """
    Type with human pacing for clearer videos. Falls back to direct value set.
    """
    locator = page.locator(selector).first
    try:
        locator.wait_for(state="visible", timeout=6000)
    except Exception:
        return False

    try:
        locator.scroll_into_view_if_needed()
        dismiss_blockers(page)
        locator.click(timeout=4000)
        try:
            locator.press("Control+A")
            locator.press("Delete")
        except Exception:
            pass
        locator.type(value, delay=delay)
        wait_short(FIELD_SETTLE_SEC)
        return True
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
        wait_short(FIELD_SETTLE_SEC)
        return True
    except Exception:
        return False


def click_visible(page, selector: str) -> bool:
    loc = page.locator(selector).first
    try:
        loc.wait_for(state="visible", timeout=4000)
        dismiss_blockers(page)
        loc.scroll_into_view_if_needed()
        loc.click(timeout=4000)
        return True
    except Exception:
        return False


def run():
    print(f"\n{'='*60}")
    print("  RECORDING: Zoho Invoice Tutorial")
    print(f"{'='*60}\n")

    with sync_playwright() as p:
        browser, context, page = create_browser_context(p, DEMO_NAME)
        logger = StepLogger(DEMO_NAME)

        try:
            def announce(description: str, hold_sec: float = STEP_PREVIEW_HOLD_SEC):
                logger.preview(page, description, hold_sec=hold_sec)

            # Step 1
            page.goto("https://www.zoho.com/invoice/", wait_until="networkidle", timeout=30000)
            logger.log(page, "Open Zoho Invoice - free online invoicing tool for businesses", wait_sec=1.2)

            # Step 2
            announce("Open the free invoice generator page - no login required")
            page.goto(
                "https://www.zoho.com/invoice/free-invoice-generator.html",
                wait_until="networkidle",
                timeout=30000,
            )
            dismiss_blockers(page)
            logger.log(page, "Open the free invoice generator page - no login required", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 3: company details
            announce("Enter business details: company name, contact, and address")
            type_field(page, "#address1", "TechStar Solutions Pvt Ltd")
            type_field(page, "#custName", "Pavan Kumar")
            type_field(page, "#address2", "42 MG Road")
            type_field(page, "#address3", "Hyderabad")
            type_field(page, "#companyState", "Telangana")
            wait_short(STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Enter business details: company name, contact, and address", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 4: client details
            announce("Enter Bill To details for Acme Corp International")
            type_field(page, "#billingAddress1", "Acme Corp International")
            type_field(page, "#billingAddress2", "100 Business Park")
            type_field(page, "#billingAddress3", "Mumbai")
            type_field(page, "#customerState", "Maharashtra")
            wait_short(STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Enter Bill To details for Acme Corp International", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 5: invoice number/date area
            announce("Set invoice number to INV-2026-001")
            type_field(page, "#invNumber", "INV-2026-001")
            wait_short(SHORT_STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Set invoice number to INV-2026-001", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 6: item 1
            announce("Add line item 1 with quantity, rate, and GST")
            type_field(page, "#itemDesc\\.1", "Web Development Services")
            type_field(page, "#itemQty\\.1", "40")
            type_field(page, "#itemRate\\.1", "2500")
            type_field(page, "#itemTax1\\.1", "9")
            wait_short(STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Add line item 1 with quantity, rate, and GST", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 7: item 2
            announce("Add line item 2: UI/UX Design services")
            type_field(page, "#itemDesc\\.2", "UI/UX Design")
            type_field(page, "#itemQty\\.2", "20")
            type_field(page, "#itemRate\\.2", "3000")
            type_field(page, "#itemTax1\\.2", "9")
            wait_short(STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Add line item 2: UI/UX Design services", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 8: item 3
            announce("Add line item 3: annual server hosting")
            type_field(page, "#itemDesc\\.3", "Server Hosting (Annual)")
            type_field(page, "#itemQty\\.3", "1")
            type_field(page, "#itemRate\\.3", "18000")
            type_field(page, "#itemTax1\\.3", "9")
            wait_short(STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Add line item 3: annual server hosting", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 9: notes and terms
            announce("Add payment notes and terms for the client")
            notes = page.locator("#customerNotes").first
            if notes.is_visible():
                notes.scroll_into_view_if_needed()
            type_field(page, "#customerNotes", "Payment due within 30 days.")
            type_field(page, "#terms", "Bank: HDFC | IFSC: HDFC0001234")
            wait_short(STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Add payment notes and terms for the client", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 10: totals section (keep frame on totals area)
            announce("Review subtotal, GST breakdown, and grand total")
            totals_anchor = page.get_by_text("Sub Total").first
            if totals_anchor.is_visible():
                totals_anchor.scroll_into_view_if_needed()
            wait_short(SHORT_STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Review subtotal, GST breakdown, and grand total", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 11: download action
            announce("Use Download/Print to export the invoice as PDF")
            clicked_download = (
                click_visible(page, 'button:has-text("Download/Print")')
                or click_visible(page, 'button:has-text("Download")')
                or click_visible(page, ".action-btn.btn-main")
                or click_visible(page, ".btn-main")
            )
            wait_short(SHORT_STEP_EXTRA_SETTLE_SEC)
            if clicked_download:
                logger.log(page, "Use Download/Print to export the invoice as PDF", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)
            else:
                logger.log(page, "Download/Print is available on the right panel to export PDF", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

            # Step 12
            logger.preview(page, "Tutorial complete - create professional GST invoices in minutes", hold_sec=FINAL_PREVIEW_HOLD_SEC)
            logger.log(page, "Tutorial complete - create professional GST invoices in minutes", wait_sec=SYNC_LOG_WAIT_SEC, show_caption=False)

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
