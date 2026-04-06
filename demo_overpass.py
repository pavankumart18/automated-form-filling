"""
demo_overpass.py - Overpass Turbo Geographic Data Query Tutorial
Richer workflow: multi-dataset Overpass QL runs, map exploration, data-table review,
and export/share actions.
"""

import os
import sys
import time

from playwright.sync_api import Page, sync_playwright

sys.path.insert(0, os.path.dirname(__file__))
from common import StepLogger, create_browser_context, finish_recording

DEMO_NAME = "overpass_turbo"
DEMO_DESCRIPTION = (
    "Use Overpass Turbo for real geo-analysis: run hospital, EV charging, school, and park coverage "
    "queries in Hyderabad, then compare the layers on the map."
)
DEMO_PROMPT = (
    "Go to overpass-turbo.eu, run multiple Hyderabad POI queries using Overpass QL, switch between "
    "Map and Data views, then stop after comparing schools, parks, and EV coverage."
)
HYD_BBOX = "(17.20,78.20,17.60,78.70)"
HYD_CORE_BBOX = "(17.28,78.32,17.50,78.62)"
HYD_SCHOOL_BBOX = "(17.33,78.38,17.47,78.56)"
HYD_PARK_BBOX = "(17.35,78.41,17.45,78.54)"
STEP_PREVIEW_HOLD_SEC = 0.95
ACTION_SETTLE_SEC = 1.45
QUERY_TYPE_DELAY_MS = 42
QUERY_TYPE_SETTLE_SEC = 0.7
RUN_QUERY_WAIT_SEC = 9.25
RUN_QUERY_SHORT_WAIT_SEC = 8.45
QUOTA_RETRY_WAIT_SEC = 18.0
MAP_CLICK_SETTLE_SEC = 1.25
SHORT_STEP_EXTRA_SETTLE_SEC = 2.15
EXPORT_STEP_EXTRA_SETTLE_SEC = 1.55
OVERPASS_ERROR_PATTERNS = [
    "api error",
    "runtime error",
    "parse error",
    "query timed out",
    "too many requests",
    "bad gateway",
    "gateway time-out",
    "server returned",
    "dispatcher",
]
OVERPASS_QUOTA_PATTERNS = [
    "quota",
    "too many requests",
    "rate limit",
    "multiple requests",
    "ip address",
]


def first_visible(page: Page, selectors: list[str]):
    """Return first visible locator from a selector list."""
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if locator.is_visible():
                return locator
        except Exception:
            continue
    return None


def click_any(page: Page, selectors: list[str], wait_after: float = ACTION_SETTLE_SEC) -> bool:
    """Click the first visible matching element."""
    target = first_visible(page, selectors)
    if not target:
        return False
    try:
        target.click()
        time.sleep(wait_after)
        return True
    except Exception:
        return False


def close_active_modal(page: Page):
    """Close active modal dialogs that can block interactions."""
    active_modal = page.locator(
        "#ffs-dialog.is-active, .modal.is-active, .dialog.is-active, .ui-dialog"
    ).first
    try:
        if active_modal.is_visible():
            page.keyboard.press("Escape")
            time.sleep(0.9)
    except Exception:
        pass


def open_top_action(page: Page, action_name: str) -> bool:
    """Open top toolbar tabs/actions like Data, Map, Export, Query."""
    return click_any(
        page,
        [
            f'button:has-text("{action_name}")',
            f'a:has-text("{action_name}")',
            f'[title*="{action_name}"]',
        ],
        wait_after=1.0,
    )


def query_has_api_error(page: Page) -> bool:
    """Detect common Overpass runtime and API failure messages."""
    try:
        error_locators = [
            "text=/api error/i",
            "text=/runtime error/i",
            "text=/parse error/i",
            "text=/too many requests/i",
            "text=/gateway time-out/i",
            "text=/bad gateway/i",
            ".alert-danger",
            ".notification.is-danger",
            ".error",
        ]
        for selector in error_locators:
            locator = page.locator(selector).first
            try:
                if locator.is_visible(timeout=250):
                    return True
            except Exception:
                continue

        body_text = page.locator("body").inner_text(timeout=1200).lower()
        return any(pattern in body_text for pattern in OVERPASS_ERROR_PATTERNS)
    except Exception:
        return False


def query_has_quota_error(page: Page) -> bool:
    """Detect quota / rate-limit failures that need a longer cooldown before retry."""
    try:
        body_text = page.locator("body").inner_text(timeout=1200).lower()
        return any(pattern in body_text for pattern in OVERPASS_QUOTA_PATTERNS)
    except Exception:
        return False


def dismiss_query_error(page: Page):
    """Clear visible error popups so a retry can proceed."""
    close_active_modal(page)
    click_any(
        page,
        [
            "button:has-text('Close')",
            "button:has-text('OK')",
            ".modal button",
            ".notification button.delete",
        ],
        wait_after=0.4,
    )
    try:
        page.keyboard.press("Escape")
        time.sleep(0.3)
    except Exception:
        pass


def set_hyderabad_view(page: Page):
    """Center map around Hyderabad."""
    page.evaluate(
        """
        const trySetView = (m) => {
            if (!m) return false;
            if (typeof m.setView === "function") {
                m.setView([17.3850, 78.4867], 12);
                return true;
            }
            if (typeof m.fitBounds === "function") {
                m.fitBounds([[17.28, 78.32], [17.50, 78.62]]);
                return true;
            }
            return false;
        };

        // Overpass Turbo map object can appear in different globals by version.
        const centered =
            trySetView(window.map) ||
            trySetView(window.ide && window.ide.map) ||
            trySetView(window.app && window.app.map);

        // Force state hash as fallback so map opens at Hyderabad.
        if (!centered) {
            window.location.hash = "map=12/17.3850/78.4867";
        }
        """
    )
    time.sleep(2.0)


def zoom_to_data(page: Page) -> bool:
    """Click Overpass map control that fits viewport to current query results."""
    clicked = click_any(
        page,
        [
            "a.leaflet-control-buttons-fitdata",
            "[title='zoom to data']",
            "[title*='zoom to data']",
        ],
        wait_after=1.2,
    )
    if clicked:
        return True

    # Fallback: known icon stack position in the map control bar.
    map_area = first_visible(page, ["#map", ".leaflet-container"])
    if not map_area:
        return False
    bounds = map_area.bounding_box()
    if not bounds:
        return False
    try:
        page.mouse.click(bounds["x"] + 24, bounds["y"] + 160)
        time.sleep(1.2)
        return True
    except Exception:
        return False


def click_map_marker(page: Page):
    """Click a map point/marker area to show details popup."""
    map_area = first_visible(page, ["#map", ".leaflet-container"])
    if not map_area:
        return

    bounds = map_area.bounding_box()
    if not bounds:
        return

    # First click near map center, then nearby offset to increase chance of popup.
    page.mouse.click(bounds["x"] + bounds["width"] * 0.52, bounds["y"] + bounds["height"] * 0.43)
    time.sleep(MAP_CLICK_SETTLE_SEC)
    page.mouse.click(bounds["x"] + bounds["width"] * 0.58, bounds["y"] + bounds["height"] * 0.48)
    time.sleep(MAP_CLICK_SETTLE_SEC + 0.2)


def get_data_row_count(page: Page) -> int:
    """Estimate row count in Data tab for narration."""
    try:
        count = page.locator("table tbody tr").count()
        if count <= 0:
            count = page.locator("table tr").count()
        return count
    except Exception:
        return 0


def set_query_text(page: Page, query: str) -> bool:
    """Prefer visible typing in the editor, then fall back to injection if needed."""
    def editor_has_query() -> bool:
        try:
            return bool(
                page.evaluate(
                    """
                    (queryText) => {
                      const normalized = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                      const expected = normalized(queryText).slice(0, 40);

                      try {
                        if (window.ide && window.ide.codeMirror && typeof window.ide.codeMirror.getValue === 'function') {
                          return normalized(window.ide.codeMirror.getValue()).includes(expected);
                        }
                      } catch (e) {}

                      try {
                        const cmHost = document.querySelector('.CodeMirror');
                        if (cmHost && cmHost.CodeMirror && typeof cmHost.CodeMirror.getValue === 'function') {
                          return normalized(cmHost.CodeMirror.getValue()).includes(expected);
                        }
                      } catch (e) {}

                      try {
                        const aceHost = document.querySelector('.ace_editor');
                        if (aceHost && window.ace && typeof window.ace.edit === 'function') {
                          return normalized(window.ace.edit(aceHost).getValue()).includes(expected);
                        }
                      } catch (e) {}

                      const textareas = Array.from(document.querySelectorAll('textarea'));
                      const candidate = textareas.find((node) => node.offsetParent !== null) || textareas[0];
                      return candidate ? normalized(candidate.value).includes(expected) : false;
                    }
                    """,
                    query,
                )
            )
        except Exception:
            return False

    try:
        editor_target = first_visible(page, [".CodeMirror", ".ace_editor", "textarea"])
        if editor_target:
            box = editor_target.bounding_box()
            if box:
                page.mouse.click(
                    box["x"] + min(box["width"] * 0.35, 240),
                    box["y"] + min(box["height"] * 0.2, 80),
                )
                time.sleep(0.25)
                page.keyboard.press("Control+A")
                time.sleep(0.15)
                page.keyboard.press("Backspace")
                time.sleep(0.25)
                page.keyboard.type(query, delay=QUERY_TYPE_DELAY_MS)
                time.sleep(QUERY_TYPE_SETTLE_SEC)
                if editor_has_query():
                    return True
    except Exception:
        pass

    try:
        injected = page.evaluate(
            """
            (queryText) => {
              try {
                if (window.ide && window.ide.codeMirror && typeof window.ide.codeMirror.setValue === 'function') {
                  window.ide.codeMirror.setValue(queryText);
                  if (typeof window.ide.codeMirror.refresh === 'function') window.ide.codeMirror.refresh();
                  return true;
                }
              } catch (e) {}

              try {
                const cmHost = document.querySelector('.CodeMirror');
                if (cmHost && cmHost.CodeMirror && typeof cmHost.CodeMirror.setValue === 'function') {
                  cmHost.CodeMirror.setValue(queryText);
                  if (typeof cmHost.CodeMirror.refresh === 'function') cmHost.CodeMirror.refresh();
                  return true;
                }
              } catch (e) {}

              try {
                const aceHost = document.querySelector('.ace_editor');
                if (aceHost && window.ace && typeof window.ace.edit === 'function') {
                  const editor = window.ace.edit(aceHost);
                  editor.setValue(queryText, -1);
                  editor.clearSelection();
                  return true;
                }
              } catch (e) {}

              try {
                const textareas = Array.from(document.querySelectorAll('textarea'));
                const candidate = textareas.find((node) => node.offsetParent !== null) || textareas[0];
                if (candidate) {
                  candidate.focus();
                  candidate.value = queryText;
                  candidate.dispatchEvent(new Event('input', { bubbles: true }));
                  candidate.dispatchEvent(new Event('change', { bubbles: true }));
                  return true;
                }
              } catch (e) {}

              return false;
            }
            """,
            query,
        )
        if injected:
            time.sleep(QUERY_TYPE_SETTLE_SEC)
            return True
    except Exception:
        pass

    try:
        page.mouse.click(220, 220)
        time.sleep(0.35)
        page.keyboard.press("Control+A")
        time.sleep(0.15)
        page.keyboard.press("Backspace")
        time.sleep(0.25)
        page.keyboard.type(query, delay=QUERY_TYPE_DELAY_MS)
        time.sleep(QUERY_TYPE_SETTLE_SEC)
        return editor_has_query()
    except Exception:
        return False


def run_current_query(page: Page, wait_after: float = RUN_QUERY_WAIT_SEC, retries: int = 1) -> bool:
    """Run the query currently in editor and retry once if Overpass shows an API error."""
    clicked = False
    for attempt in range(retries + 1):
        clicked = open_top_action(page, "Run")
        if not clicked:
            clicked = click_any(
                page,
                ['button:has-text("Run")', 'a:has-text("Run")', '[title*="Run"]'],
                wait_after=0.8,
            )
        if not clicked:
            return False

        time.sleep(wait_after if attempt == 0 else max(wait_after - 2.0, 4.5))
        if not query_has_api_error(page):
            return True

        quota_hit = query_has_quota_error(page)
        dismiss_query_error(page)
        time.sleep(QUOTA_RETRY_WAIT_SEC if quota_hit else 1.0)

    return not query_has_api_error(page)


def run():
    print(f"\n{'='*60}")
    print("  RECORDING: Overpass Turbo Geographic Data Tutorial")
    print(f"{'='*60}\n")

    with sync_playwright() as p:
        browser, context, page = create_browser_context(p, DEMO_NAME)
        logger = StepLogger(DEMO_NAME)

        try:
            page.goto("https://overpass-turbo.eu/#map=12/17.3850/78.4867", wait_until="networkidle", timeout=45000)
            time.sleep(3)
            close_active_modal(page)
            logger.log(page, "Open Overpass Turbo and load the map + query editor workspace")

            logger.log(page, "Split view: query editor on left, map + controls on right")

            def announce(description: str):
                logger.preview(page, description, hold_sec=STEP_PREVIEW_HOLD_SEC)

            hospital_query = """
[out:json][timeout:25];
nwr["amenity"="hospital"]__BBOX__;
out center;
            """.strip().replace("__BBOX__", HYD_BBOX)
            announce("Write a Hyderabad hospitals query in Overpass QL using a fixed city bounding box")
            if set_query_text(page, hospital_query):
                logger.log(page, "Write a Hyderabad hospitals query in Overpass QL using a fixed city bounding box", wait_sec=0, show_caption=False)
                announce("Run query to load all mapped hospitals as explorable markers")
                run_current_query(page, wait_after=RUN_QUERY_WAIT_SEC)
                logger.log(page, "Run query to load all mapped hospitals as explorable markers", wait_sec=0, show_caption=False)
            else:
                logger.log(page, "If editor focus fails, click left pane, paste query, and press Run")

            announce("Use 'zoom to data' to jump map viewport directly onto Hyderabad results")
            if not zoom_to_data(page):
                set_hyderabad_view(page)
            time.sleep(SHORT_STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Use 'zoom to data' to jump map viewport directly onto Hyderabad results", wait_sec=0, show_caption=False)

            announce("Click map markers to inspect feature tags like name, address, and amenity type")
            click_map_marker(page)
            time.sleep(SHORT_STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Click map markers to inspect feature tags like name, address, and amenity type", wait_sec=0, show_caption=False)

            announce("Open Data tab to inspect raw tabular output and OSM attributes")
            data_opened = open_top_action(page, "Data")
            if data_opened:
                time.sleep(SHORT_STEP_EXTRA_SETTLE_SEC)
                rows = get_data_row_count(page)
                if rows > 0:
                    logger.log(page, f"Open Data tab to inspect tabular results ({rows} rows visible)", wait_sec=0, show_caption=False)
                else:
                    logger.log(page, "Open Data tab to inspect raw tabular output and OSM attributes", wait_sec=0, show_caption=False)
            else:
                logger.log(page, "Data tab can be used to validate each returned feature before export")

            announce("Switch back to Map view to visually compare coverage across neighborhoods")
            open_top_action(page, "Map")
            time.sleep(SHORT_STEP_EXTRA_SETTLE_SEC)
            logger.log(page, "Switch back to Map view to visually compare coverage across neighborhoods", wait_sec=0, show_caption=False)

            ev_query = """
[out:json][timeout:25];
nwr["amenity"="charging_station"]__BBOX__;
out center;
            """.strip().replace("__BBOX__", HYD_BBOX)
            announce("Replace with EV charging station query to analyze clean-mobility readiness")
            if set_query_text(page, ev_query):
                logger.log(page, "Replace with EV charging station query to analyze clean-mobility readiness", wait_sec=0, show_caption=False)
                announce("EV charging points rendered; now compare spread versus healthcare locations")
                run_current_query(page, wait_after=RUN_QUERY_WAIT_SEC)
                logger.log(page, "EV charging points rendered; now compare spread versus healthcare locations", wait_sec=0, show_caption=False)
                if not zoom_to_data(page):
                    set_hyderabad_view(page)

            schools_query = """
[out:json][timeout:20];
(
  nwr["amenity"="school"]__BBOX__;
);
out center 80;
            """.strip().replace("__BBOX__", HYD_SCHOOL_BBOX)
            schools_fallback_query = """
[out:json][timeout:18];
node["amenity"="school"]__BBOX__;
out 60;
            """.strip().replace("__BBOX__", HYD_SCHOOL_BBOX)
            announce("Run school query to map education infrastructure in the same city boundary")
            if set_query_text(page, schools_query):
                logger.log(page, "Run school query to map education infrastructure in the same city boundary", wait_sec=0, show_caption=False)
                school_ok = run_current_query(page, wait_after=RUN_QUERY_WAIT_SEC)
                if not school_ok and set_query_text(page, schools_fallback_query):
                    announce("School query hit turbulence, so we switch to a lighter school map and run again")
                    run_current_query(page, wait_after=RUN_QUERY_SHORT_WAIT_SEC)
                if not zoom_to_data(page):
                    set_hyderabad_view(page)

            parks_query = """
[out:json][timeout:18];
node["leisure"="park"]__BBOX__;
out 40;
            """.strip().replace("__BBOX__", HYD_PARK_BBOX)
            parks_fallback_query = """
[out:json][timeout:15];
node["leisure"="garden"]__BBOX__;
out 30;
            """.strip().replace("__BBOX__", HYD_PARK_BBOX)
            announce("Run park query to map green space and recreation across the same urban core")
            if set_query_text(page, parks_query):
                logger.log(page, "Run park query to map green space and recreation across the same urban core", wait_sec=0, show_caption=False)
                announce("Park layer rendered; now compare green space against schools and mobility")
                park_ok = run_current_query(page, wait_after=RUN_QUERY_SHORT_WAIT_SEC)
                if not park_ok and set_query_text(page, parks_fallback_query):
                    announce("Park query hit the rate limit, so we switch to a lighter green-space layer and try again")
                    run_current_query(page, wait_after=RUN_QUERY_SHORT_WAIT_SEC)
                logger.log(page, "Park layer rendered; now compare green space against schools and mobility", wait_sec=0, show_caption=False)
                if not zoom_to_data(page):
                    set_hyderabad_view(page)

            page.keyboard.press("Escape")
            time.sleep(0.5)
            logger.log(page, "Tutorial complete: compare hospitals, EV charging, schools, and parks in one reproducible map workflow")

        except Exception as error:
            print(f"\nERROR during recording: {error}")
            try:
                logger.log(page, f"Error encountered: {str(error)[:100]}", wait_sec=0)
            except Exception:
                pass

        finally:
            logger.save()
            logger.save_transcript()
            finish_recording(browser, context, DEMO_NAME, page)

    return DEMO_NAME, DEMO_DESCRIPTION, DEMO_PROMPT


if __name__ == "__main__":
    run()
