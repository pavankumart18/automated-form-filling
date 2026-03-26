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
    "Use Overpass Turbo for real geo-analysis: run hospital, EV charging, school, and pharmacy coverage "
    "queries in Hyderabad, inspect map + data views, and export/share results."
)
DEMO_PROMPT = (
    "Go to overpass-turbo.eu, run multiple Hyderabad POI queries using Overpass QL, switch between "
    "Map and Data views, then export the result."
)
HYD_BBOX = "(17.20,78.20,17.60,78.70)"
STEP_PREVIEW_HOLD_SEC = 0.65
ACTION_SETTLE_SEC = 1.15
QUERY_TYPE_DELAY_MS = 24
QUERY_TYPE_SETTLE_SEC = 1.0
RUN_QUERY_WAIT_SEC = 7.6
RUN_QUERY_SHORT_WAIT_SEC = 6.6
MAP_CLICK_SETTLE_SEC = 1.0


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
    """Set query text by focusing editor panel and typing."""
    try:
        # Click inside left editor pane (stable across CodeMirror versions).
        page.mouse.click(220, 220)
        time.sleep(0.35)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        page.keyboard.type(query, delay=QUERY_TYPE_DELAY_MS)
        time.sleep(QUERY_TYPE_SETTLE_SEC)
        return True
    except Exception:
        return False


def run_current_query(page: Page, wait_after: float = RUN_QUERY_WAIT_SEC) -> bool:
    """Run the query currently in editor."""
    clicked = open_top_action(page, "Run")
    if not clicked:
        clicked = click_any(
            page,
            ['button:has-text("Run")', 'a:has-text("Run")', '[title*="Run"]'],
            wait_after=0.8,
        )
    time.sleep(wait_after)
    return clicked


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
(
  node["amenity"="hospital"]__BBOX__;
  way["amenity"="hospital"]__BBOX__;
  relation["amenity"="hospital"]__BBOX__;
);
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
            logger.log(page, "Use 'zoom to data' to jump map viewport directly onto Hyderabad results", wait_sec=0, show_caption=False)

            announce("Click map markers to inspect feature tags like name, address, and amenity type")
            click_map_marker(page)
            logger.log(page, "Click map markers to inspect feature tags like name, address, and amenity type", wait_sec=0, show_caption=False)

            announce("Open Data tab to inspect raw tabular output and OSM attributes")
            data_opened = open_top_action(page, "Data")
            if data_opened:
                rows = get_data_row_count(page)
                if rows > 0:
                    logger.log(page, f"Open Data tab to inspect tabular results ({rows} rows visible)", wait_sec=0, show_caption=False)
                else:
                    logger.log(page, "Open Data tab to inspect raw tabular output and OSM attributes", wait_sec=0, show_caption=False)
            else:
                logger.log(page, "Data tab can be used to validate each returned feature before export")

            announce("Switch back to Map view to visually compare coverage across neighborhoods")
            open_top_action(page, "Map")
            logger.log(page, "Switch back to Map view to visually compare coverage across neighborhoods", wait_sec=0, show_caption=False)

            ev_query = """
[out:json][timeout:25];
(
  node["amenity"="charging_station"]__BBOX__;
  way["amenity"="charging_station"]__BBOX__;
  relation["amenity"="charging_station"]__BBOX__;
);
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
[out:json][timeout:25];
(
  node["amenity"="school"]__BBOX__;
  way["amenity"="school"]__BBOX__;
  relation["amenity"="school"]__BBOX__;
);
out center;
            """.strip().replace("__BBOX__", HYD_BBOX)
            announce("Run school query to map education infrastructure in the same city boundary")
            if set_query_text(page, schools_query):
                logger.log(page, "Run school query to map education infrastructure in the same city boundary", wait_sec=0, show_caption=False)
                run_current_query(page, wait_after=RUN_QUERY_WAIT_SEC)
                if not zoom_to_data(page):
                    set_hyderabad_view(page)

            pharmacies_query = """
[out:json][timeout:25];
(
  node["amenity"="pharmacy"]__BBOX__;
  way["amenity"="pharmacy"]__BBOX__;
  relation["amenity"="pharmacy"]__BBOX__;
);
out center;
            """.strip().replace("__BBOX__", HYD_BBOX)
            announce("Add pharmacy query as a fourth dataset to build a richer city-services comparison")
            if set_query_text(page, pharmacies_query):
                logger.log(page, "Add pharmacy query as a fourth dataset to build a richer city-services comparison", wait_sec=0, show_caption=False)
                announce("Single editor workflow lets you iterate quickly across multiple urban datasets")
                run_current_query(page, wait_after=RUN_QUERY_SHORT_WAIT_SEC)
                logger.log(page, "Single editor workflow lets you iterate quickly across multiple urban datasets", wait_sec=0, show_caption=False)
                if not zoom_to_data(page):
                    set_hyderabad_view(page)

            announce("Open Export options for downstream GIS and analytics workflows")
            exported = open_top_action(page, "Export")
            if exported:
                logger.log(page, "Open Export options for downstream GIS and analytics workflows", wait_sec=0, show_caption=False)
                announce("Choose GeoJSON to move the result into QGIS, Python, or web map stacks")
                geojson_clicked = click_any(
                    page,
                    [
                        'a:has-text("GeoJSON")',
                        'button:has-text("GeoJSON")',
                        'a:has-text("geojson")',
                    ],
                    wait_after=0.8,
                )
                if geojson_clicked:
                    logger.log(page, "Choose GeoJSON to move the result into QGIS, Python, or web map stacks", wait_sec=0, show_caption=False)
                else:
                    logger.log(page, "Export supports GeoJSON, KML, GPX, and raw OSM for different tools")
            else:
                logger.log(page, "Export panel provides shareable output formats for external analysis")

            page.keyboard.press("Escape")
            time.sleep(0.5)
            logger.log(page, "Tutorial complete: from iterative query editing to exportable, reproducible geo-data")

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
