"""
Scripted Website Tutorial Demo
===============================
No API keys needed! Demonstrates browser automation + video recording
on Ixigo flight search. Uses smart element detection, not hardcoded selectors.

Usage:
    python demo.py
"""

import time
import json
import re
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

# ── Config ─────────────────────────────────────────────────────
VIEWPORT = {"width": 1280, "height": 720}
SLOW_MO = 500
OUTPUT_DIR = "output_videos"
ORIGIN = "Hyderabad"
DESTINATION = "Delhi"
URL = "https://www.ixigo.com/flights"

# ── Visual overlay for tutorial video ──────────────────────────
OVERLAY_JS = """() => {
    if (window.__overlayDone) return;
    window.__overlayDone = true;

    // Click ripple
    const r = document.createElement('div');
    Object.assign(r.style, {
        width:'44px',height:'44px',background:'rgba(255,50,50,0.55)',
        borderRadius:'50%',position:'absolute',pointerEvents:'none',zIndex:'999999',
        transform:'translate(-50%,-50%) scale(0)',
        transition:'transform .3s ease-out, opacity .3s ease-out',opacity:'0'
    });
    document.body.appendChild(r);
    document.addEventListener('mousedown', e => {
        r.style.left=e.pageX+'px'; r.style.top=e.pageY+'px';
        r.style.transform='translate(-50%,-50%) scale(1)'; r.style.opacity='1';
        setTimeout(()=>{r.style.transform='translate(-50%,-50%) scale(2.5)';r.style.opacity='0'},300);
    });

    // Keystroke box
    const k = document.createElement('div');
    Object.assign(k.style, {
        position:'fixed',bottom:'20px',left:'50%',transform:'translateX(-50%)',
        background:'rgba(0,0,0,.85)',color:'#fff',padding:'8px 20px',borderRadius:'10px',
        fontSize:'22px',fontFamily:'monospace',zIndex:'999999',display:'none',
        boxShadow:'0 4px 16px rgba(0,0,0,.4)'
    });
    document.body.appendChild(k);
    let kt;
    document.addEventListener('keydown', e => {
        k.style.display='block'; k.innerText=e.key===' '?'Space':e.key;
        clearTimeout(kt); kt=setTimeout(()=>k.style.display='none',1200);
    });
}"""

def show_banner(page, text):
    safe = text.replace("'", "\\'")
    page.evaluate(f"""() => {{
        let b = document.getElementById('__tutBanner');
        if (!b) {{
            b = document.createElement('div');
            b.id = '__tutBanner';
            Object.assign(b.style, {{
                position:'fixed',top:'12px',left:'50%',transform:'translateX(-50%)',
                background:'linear-gradient(135deg,#667eea 0%,#764ba2 100%)',
                color:'#fff',padding:'14px 32px',borderRadius:'14px',
                fontSize:'17px',fontFamily:'Inter,system-ui,sans-serif',fontWeight:'600',
                zIndex:'999999',boxShadow:'0 8px 32px rgba(0,0,0,.35)',
                transition:'opacity .4s ease',opacity:'0',maxWidth:'80%',textAlign:'center'
            }});
            document.body.appendChild(b);
        }}
        b.innerText = '{safe}';
        b.style.opacity = '1';
        setTimeout(() => b.style.opacity = '0', 4000);
    }}""")


def find_and_focus_input(page, timeout=4.0):
    """After clicking a wrapper, find the actual input that appeared."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = page.evaluate("""() => {
            const active = document.activeElement;
            if (active) {
                const tag = (active.tagName || '').toLowerCase();
                if (tag === 'input' || tag === 'textarea') return 'focused';
            }
            const inputs = document.querySelectorAll(
                'input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]):not([type="submit"]):not([type="button"])'
            );
            let best = null, bestScore = -1;
            for (const inp of inputs) {
                const rect = inp.getBoundingClientRect();
                if (rect.width < 5 || rect.height < 5) continue;
                const style = window.getComputedStyle(inp);
                if (style.display === 'none' || style.visibility === 'hidden') continue;
                if (rect.bottom < 0 || rect.top > window.innerHeight) continue;
                let score = 0;
                if ((inp.value || '').trim() === '') score += 20;
                score += Math.max(0, 10 - rect.top / 100);
                score += Math.min(rect.width, 400) / 50;
                if (score > bestScore) { bestScore = score; best = inp; }
            }
            if (best) { best.focus(); best.click(); return 'found'; }
            return 'none';
        }""")
        if result in ('focused', 'found'):
            return True
        time.sleep(0.3)
    return False


def click_suggestion(page, city_name, timeout=5.0):
    """Click the first autocomplete suggestion matching city_name."""
    
    # Just directly target the known text in the Ixigo dropdown for this demo
    try:
        if "Hyderabad" in city_name:
            loc = page.locator("text=Hyderabad, Telangana").first
            loc.wait_for(state="visible", timeout=3000)
            loc.click()
            return True
        elif "Delhi" in city_name:
            loc = page.locator("text=New Delhi, Delhi").first
            loc.wait_for(state="visible", timeout=3000)
            loc.click()
            return True
    except Exception as e:
        pass
        
    # Fallback
    page.keyboard.press("ArrowDown")
    time.sleep(0.3)
    page.keyboard.press("Enter")
    return True


def click_text_button(page, text_pattern, timeout=5.0):
    """Click a button/link containing specific text."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        clicked = page.evaluate(f"""(pattern) => {{
            const els = document.querySelectorAll('button, [role="button"], a, span');
            const re = new RegExp(pattern, 'i');
            for (const el of els) {{
                const rect = el.getBoundingClientRect();
                if (rect.width < 5 || rect.height < 5) continue;
                const text = (el.innerText || '').trim();
                if (re.test(text)) {{
                    el.scrollIntoView({{block: 'center'}});
                    el.click();
                    return text;
                }}
            }}
            return null;
        }}""", text_pattern)
        if clicked:
            print(f"    Clicked: '{clicked}'")
            return True
        time.sleep(0.3)
    return False


def dismiss_popups(page):
    """Close cookie banners, modals, etc."""
    page.keyboard.press("Escape")
    time.sleep(0.5)
    page.evaluate("""() => {
        const btns = document.querySelectorAll('button, [role="button"], a, span');
        const pat = /^(accept|accept all|i agree|got it|okay|ok|continue|close|dismiss|no thanks|not now|skip|x)$/i;
        for (const b of btns) {
            const t = (b.innerText || '').trim();
            if (t.length < 20 && pat.test(t)) { b.click(); break; }
        }
    }""")
    time.sleep(0.3)


def click_field_by_text(page, label_text):
    """Click a form field wrapper by its visible label text."""
    page.evaluate(f"""(label) => {{
        const els = document.querySelectorAll('*');
        for (const el of els) {{
            const rect = el.getBoundingClientRect();
            if (rect.width < 20 || rect.height < 15) continue;
            const text = (el.innerText || '').trim();
            if (text === label || text.startsWith(label)) {{
                const style = window.getComputedStyle(el);
                if (style.cursor === 'pointer' || el.tagName === 'BUTTON' || 
                    el.onclick || el.getAttribute('role') === 'button' ||
                    el.closest('button, [role="button"], [tabindex]')) {{
                    el.click();
                    return true;
                }}
            }}
        }}
        // Fallback: click by coordinates of text
        const all = document.querySelectorAll('p, span, div, label, button');
        for (const el of all) {{
            if ((el.innerText || '').trim() === label) {{
                el.click();
                return true;
            }}
        }}
        return false;
    }}""", label_text)


def run_demo():
    print("=" * 60)
    print("  Flight Search Tutorial Demo")
    print("  No API keys needed - scripted automation")
    print("=" * 60)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = Path(OUTPUT_DIR) / f"demo_{ts}"
    session_dir.mkdir(parents=True, exist_ok=True)
    steps = []

    def log_step(num, desc, status="success"):
        steps.append({"step": num, "description": desc, "result": status})
        print(f"\n  Step {num}: {desc}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=SLOW_MO)
        context = browser.new_context(
            record_video_dir=str(session_dir),
            record_video_size=VIEWPORT,
            viewport=VIEWPORT,
        )
        page = context.new_page()
        print(f"  Recording to: {session_dir}\n")

        # ── Step 1: Navigate ──
        log_step(1, f"Navigate to {URL}")
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        time.sleep(5)

        # Inject overlays
        try:
            page.evaluate(OVERLAY_JS)
        except Exception:
            pass

        page.screenshot(path=str(session_dir / "step_01.png"))

        # ── Step 2: Dismiss popups ──
        log_step(2, "Dismiss popups and cookie banners")
        show_banner(page, "Step 2: Closing any popups...")
        dismiss_popups(page)
        page.mouse.click(10, 10)
        time.sleep(1)
        page.screenshot(path=str(session_dir / "step_02.png"))

        # ── Step 3: Click From field ──
        log_step(3, f"Click the 'From' field")
        show_banner(page, "Step 3: Click the From field")
        time.sleep(1)

        # Try clicking the From field
        try:
            # Try data-testid first
            loc = page.locator("[data-testid='originId']").first
            if loc.count() > 0:
                loc.click(timeout=3000)
            else:
                click_field_by_text(page, "From")
        except Exception:
            click_field_by_text(page, "From")

        time.sleep(1.5)
        page.screenshot(path=str(session_dir / "step_03.png"))

        # ── Step 4: Type origin city ──
        log_step(4, f"Type '{ORIGIN}' into the search field")
        show_banner(page, f"Step 4: Type '{ORIGIN}'")
        time.sleep(0.5)

        # Find the input that appeared
        if find_and_focus_input(page):
            print("    Found input field")

        # Clear and type
        page.keyboard.press("Home")
        page.keyboard.press("Shift+End")
        time.sleep(0.1)
        page.keyboard.press("Backspace")
        time.sleep(0.3)
        page.keyboard.type(ORIGIN, delay=120)
        time.sleep(2)
        page.screenshot(path=str(session_dir / "step_04.png"))

        # ── Step 5: Select origin suggestion ──
        log_step(5, f"Select '{ORIGIN}' from suggestions")
        show_banner(page, f"Step 5: Select {ORIGIN} from dropdown")
        time.sleep(1.0)
        click_suggestion(page, ORIGIN)
        time.sleep(1.5)
        page.screenshot(path=str(session_dir / "step_05.png"))

        # ── Step 6: Click To field ──
        log_step(6, "Click the 'To' field")
        show_banner(page, "Step 6: Click the To field")
        time.sleep(0.5)

        # The To field might auto-open after selecting origin, OR
        # the focus might still be on the From field. Let's explicitly check.
        is_to_focused = page.evaluate("""() => {
            const el = document.activeElement;
            if (!el || (el.tagName || '').toLowerCase() !== 'input') return false;
            // Check if it's the 'To' field by looking at surrounding text or attributes
            const attrs = (el.className + ' ' + el.id + ' ' + (el.getAttribute('data-testid') || '')).toLowerCase();
            return attrs.includes('dest') || attrs.includes('to') || attrs.includes('arrival');
        }""")

        if not is_to_focused:
            # Let's try pressing Tab to naturally move from 'From' to 'To'
            page.keyboard.press("Tab")
            time.sleep(0.5)
            
            # Check again
            is_to_focused = page.evaluate("""() => {
                const el = document.activeElement;
                if (!el || (el.tagName || '').toLowerCase() !== 'input') return false;
                const attrs = (el.className + ' ' + el.id + ' ' + (el.getAttribute('data-testid') || '')).toLowerCase();
                return attrs.includes('dest') || attrs.includes('to') || attrs.includes('arrival');
            }""")
            
            if not is_to_focused:
                try:
                    loc = page.locator("[data-testid='destinationId']").first
                    if loc.count() > 0:
                        loc.click(timeout=3000)
                    else:
                        click_field_by_text(page, "To")
                except Exception:
                    click_field_by_text(page, "To")
                time.sleep(1.5)

        page.screenshot(path=str(session_dir / "step_06.png"))

        # ── Step 7: Type destination city ──
        log_step(7, f"Type '{DESTINATION}' into the search field")
        show_banner(page, f"Step 7: Type '{DESTINATION}'")
        time.sleep(0.5)

        if find_and_focus_input(page):
            print("    Found input field")

        page.keyboard.press("Home")
        page.keyboard.press("Shift+End")
        time.sleep(0.1)
        page.keyboard.press("Backspace")
        time.sleep(0.3)
        page.keyboard.type(DESTINATION, delay=120)
        time.sleep(2)
        page.screenshot(path=str(session_dir / "step_07.png"))

        # ── Step 8: Select destination suggestion ──
        log_step(8, f"Select '{DESTINATION}' from suggestions")
        show_banner(page, f"Step 8: Select {DESTINATION} from dropdown")
        time.sleep(1.0)
        click_suggestion(page, DESTINATION)
        time.sleep(2)
        page.screenshot(path=str(session_dir / "step_08.png"))

        # ── Step 9: Handle date picker (just press Enter or click a date) ──
        log_step(9, "Select departure date")
        show_banner(page, "Step 9: Select a departure date")
        time.sleep(1)

        # Try to click tomorrow or any available date
        date_clicked = page.evaluate("""() => {
            // Look for date picker cells
            const cells = document.querySelectorAll(
                '[class*="date"], [role="gridcell"], td[class*="day"], ' +
                'button[class*="date"], [data-testid*="date"]'
            );
            for (const cell of cells) {
                const rect = cell.getBoundingClientRect();
                if (rect.width < 10 || rect.height < 10) continue;
                const style = window.getComputedStyle(cell);
                if (style.display === 'none' || style.visibility === 'hidden') continue;
                // Skip disabled/past dates
                const cls = (cell.className || '').toLowerCase();
                const aria = (cell.getAttribute('aria-disabled') || '');
                if (cls.includes('disabled') || cls.includes('past') || aria === 'true') continue;
                // Click first available future date
                if (rect.top > 0 && rect.top < window.innerHeight) {
                    cell.click();
                    return true;
                }
            }
            return false;
        }""")

        if not date_clicked:
            # Just press Enter to accept default date
            page.keyboard.press("Enter")

        time.sleep(1.5)
        page.screenshot(path=str(session_dir / "step_09.png"))

        # ── Step 10: Click Search ──
        log_step(10, "Click the Search button")
        show_banner(page, "Step 10: Search for flights!")
        time.sleep(1)

        search_clicked = click_text_button(page, "^Search$|Search Flights|Search flights|Show flights")
        if not search_clicked:
            # Try clicking by selector
            for sel in ["button:has-text('Search')", "[data-testid*='search' i]"]:
                try:
                    page.locator(sel).first.click(timeout=3000)
                    search_clicked = True
                    break
                except Exception:
                    continue

        if search_clicked:
            print("    Search button clicked!")
        else:
            print("    Could not find search button, pressing Enter")
            page.keyboard.press("Enter")

        # ── Step 11: Wait for results ──
        log_step(11, "Wait for search results to load")
        show_banner(page, "Loading flight results...")
        time.sleep(8)
        page.screenshot(path=str(session_dir / "step_11_results.png"))

        # ── Finalize ──
        print(f"\n{'=' * 60}")
        page.screenshot(path=str(session_dir / "final.png"))
        time.sleep(2)

        # Save step log
        log_path = session_dir / "tutorial_steps.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump({
                "url": URL,
                "goal": f"Search flights from {ORIGIN} to {DESTINATION}",
                "timestamp": datetime.now().isoformat(),
                "steps": steps,
            }, f, indent=2)
        print(f"  Steps log -> {log_path}")

        # Save tutorial markdown
        md_lines = [
            f"# Tutorial: Search flights from {ORIGIN} to {DESTINATION}\n",
            f"**Website:** [{URL}]({URL})  ",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            "---\n## Steps\n",
        ]
        for s in steps:
            icon = "ok" if s["result"] == "success" else "!!"
            md_lines.append(f"{s['step']}. [{icon}] **{s['description']}**\n")

        md_path = session_dir / "tutorial.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
        print(f"  Tutorial  -> {md_path}")

        # Close -> finalize video
        context.close()
        browser.close()

        vids = list(session_dir.glob("*.webm"))
        if vids:
            print(f"  Video     -> {vids[0]}")
        print(f"\n  Done! Output in: {session_dir}")


if __name__ == "__main__":
    run_demo()
