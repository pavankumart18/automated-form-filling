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


def type_field(page, selector: str, value: str, delay: int = 65) -> bool:
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
        wait_short(0.25)
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
        wait_short(0.2)
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
            # Step 1
            page.goto("https://www.zoho.com/invoice/", wait_until="networkidle", timeout=30000)
            logger.log(page, "Open Zoho Invoice - free online invoicing tool for businesses", wait_sec=1.2)

            # Step 2
            page.goto(
                "https://www.zoho.com/invoice/free-invoice-generator.html",
                wait_until="networkidle",
                timeout=30000,
            )
            dismiss_blockers(page)
            logger.log(page, "Open the free invoice generator page - no login required", wait_sec=1.2)

            # Step 3: company details
            type_field(page, "#address1", "TechStar Solutions Pvt Ltd")
            type_field(page, "#custName", "Pavan Kumar")
            type_field(page, "#address2", "42 MG Road")
            type_field(page, "#address3", "Hyderabad")
            type_field(page, "#companyState", "Telangana")
            wait_short(0.8)
            logger.log(page, "Enter business details: company name, contact, and address", wait_sec=1.0)

            # Step 4: client details
            type_field(page, "#billingAddress1", "Acme Corp International")
            type_field(page, "#billingAddress2", "100 Business Park")
            type_field(page, "#billingAddress3", "Mumbai")
            type_field(page, "#customerState", "Maharashtra")
            wait_short(0.8)
            logger.log(page, "Enter Bill To details for Acme Corp International", wait_sec=1.0)

            # Step 5: invoice number/date area
            type_field(page, "#invNumber", "INV-2026-001")
            wait_short(0.5)
            logger.log(page, "Set invoice number to INV-2026-001", wait_sec=1.0)

            # Step 6: item 1
            type_field(page, "#itemDesc\\.1", "Web Development Services")
            type_field(page, "#itemQty\\.1", "40")
            type_field(page, "#itemRate\\.1", "2500")
            type_field(page, "#itemTax1\\.1", "9")
            wait_short(0.6)
            logger.log(page, "Add line item 1 with quantity, rate, and GST", wait_sec=1.0)

            # Step 7: item 2
            type_field(page, "#itemDesc\\.2", "UI/UX Design")
            type_field(page, "#itemQty\\.2", "20")
            type_field(page, "#itemRate\\.2", "3000")
            type_field(page, "#itemTax1\\.2", "9")
            wait_short(0.6)
            logger.log(page, "Add line item 2: UI/UX Design services", wait_sec=1.0)

            # Step 8: item 3
            type_field(page, "#itemDesc\\.3", "Server Hosting (Annual)")
            type_field(page, "#itemQty\\.3", "1")
            type_field(page, "#itemRate\\.3", "18000")
            type_field(page, "#itemTax1\\.3", "9")
            wait_short(0.8)
            logger.log(page, "Add line item 3: annual server hosting", wait_sec=1.0)

            # Step 9: notes and terms
            notes = page.locator("#customerNotes").first
            if notes.is_visible():
                notes.scroll_into_view_if_needed()
            type_field(page, "#customerNotes", "Payment due within 30 days.")
            type_field(page, "#terms", "Bank: HDFC | IFSC: HDFC0001234")
            wait_short(0.8)
            logger.log(page, "Add payment notes and terms for the client", wait_sec=1.0)

            # Step 10: totals section (keep frame on totals area)
            totals_anchor = page.get_by_text("Sub Total").first
            if totals_anchor.is_visible():
                totals_anchor.scroll_into_view_if_needed()
            wait_short(0.8)
            logger.log(page, "Review subtotal, GST breakdown, and grand total", wait_sec=1.0)

            # Step 11: download action
            clicked_download = (
                click_visible(page, 'button:has-text("Download/Print")')
                or click_visible(page, 'button:has-text("Download")')
                or click_visible(page, ".action-btn.btn-main")
                or click_visible(page, ".btn-main")
            )
            wait_short(0.8)
            if clicked_download:
                logger.log(page, "Use Download/Print to export the invoice as PDF", wait_sec=1.0)
            else:
                logger.log(page, "Download/Print is available on the right panel to export PDF", wait_sec=1.0)

            # Step 12
            logger.show_caption(page, "Tutorial complete! You can now create GST invoices in Zoho Invoice")
            wait_short(1.6)
            logger.log(page, "Tutorial complete - create professional GST invoices in minutes", wait_sec=0.6)

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
