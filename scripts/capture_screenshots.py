import os
import asyncio
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "docs/screenshots"

async def capture_all(base_url: str = "http://localhost:3000"):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        context_light = await browser.new_context(viewport={"width": 1440, "height": 900})
        page_light = await context_light.new_page()
        await page_light.goto(base_url, wait_until="networkidle")
        await page_light.screenshot(path=os.path.join(SCREENSHOT_DIR, "dashboard-light.png"), full_page=True)
        
        finding_elem = page_light.locator("section:has-text('Finding & Deterministic Proof')")
        if await finding_elem.count() > 0:
            await finding_elem.first.screenshot(path=os.path.join(SCREENSHOT_DIR, "finding-stamp.png"))
            
        diff_elem = page_light.locator("section:has-text('Exhibit D // Diff Reading Room')")
        if await diff_elem.count() > 0:
            await diff_elem.first.screenshot(path=os.path.join(SCREENSHOT_DIR, "diff.png"))
            await diff_elem.first.screenshot(path=os.path.join(SCREENSHOT_DIR, "diff-reading-room.png"))

        plate_elem = page_light.locator("section:has-text('Exhibit B // Draggable Registration Plate')")
        if await plate_elem.count() > 0:
            await plate_elem.first.screenshot(path=os.path.join(SCREENSHOT_DIR, "before-after-plate.png"))

        await page_light.keyboard.press("/")
        voice_focused = await page_light.evaluate("document.activeElement.getAttribute('placeholder')")
        assert "Speak or type" in str(voice_focused)

        await page_light.get_by_role("button", name="Darkroom Mode").click()
        await page_light.wait_for_timeout(300)
        await page_light.screenshot(path=os.path.join(SCREENSHOT_DIR, "dashboard-dark.png"), full_page=True)

        context_reduced = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            reduced_motion="reduce",
        )
        page_reduced = await context_reduced.new_page()
        await page_reduced.goto(f"{base_url}?investigation=BP-EMPTY", wait_until="networkidle")
        
        investigation_input = page_reduced.locator("input[value='BP-0007']")
        if await investigation_input.count() > 0:
            await investigation_input.fill("BP-EMPTY")
            await page_reduced.wait_for_timeout(500)
            
        await page_reduced.screenshot(path=os.path.join(SCREENSHOT_DIR, "empty-state.png"), full_page=True)

        await browser.close()
    print("All screenshots successfully captured in docs/screenshots/")

if __name__ == "__main__":
    asyncio.run(capture_all())
