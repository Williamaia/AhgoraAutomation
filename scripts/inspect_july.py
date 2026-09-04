"""Inspeciona detalhadamente o HTML de cada dia de julho."""

import re
from pathlib import Path

from playwright.sync_api import sync_playwright

HOME_URL = "https://hcm19.sapsf.com/sf/home?bplte_company=universoon"
STORAGE_PATH = Path(__file__).resolve().parent.parent / "auth" / "storage.json"
MIRROR_IFRAME = 'iframe[name="mirror-iframe"]'

MONTH_SHORT = {7: "JUL."}


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(
            storage_state=str(STORAGE_PATH),
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
        )
        page = context.new_page()
        page.goto(HOME_URL, wait_until="domcontentloaded")

        with page.expect_popup() as p1:
            page.get_by_role("link", name="Ajuste de Ponto").click()
        with p1.value.expect_popup() as p2:
            p1.value.get_by_role("link", name="Acessar  arrow_right_alt").click()
        mirror = p2.value
        mirror.wait_for_load_state("networkidle", timeout=60_000)
        frame = mirror.frame_locator(MIRROR_IFRAME)
        frame.locator(".v-calendar-weekly").wait_for(state="visible", timeout=60_000)

        frame.locator("button").filter(has_text="keyboard_arrow_down").first.click()
        mirror.wait_for_timeout(1500)
        frame.locator("button:visible").filter(has_text="JUL.").first.click()

        for _ in range(30):
            btn = frame.locator("button").filter(has_text=re.compile(r"/20\d{2}")).first
            if "JULHO" in btn.inner_text(timeout=2000).upper():
                break
            mirror.wait_for_timeout(1000)

        print("Em julho agora.")
        mirror.wait_for_timeout(2000)

        for day_el in frame.locator(".v-calendar-weekly__day").all():
            cls = day_el.get_attribute("class") or ""
            if "v-outside" in cls:
                continue
            text = day_el.inner_text(timeout=2000).strip().replace("\n", " ")
            html = day_el.inner_html(timeout=2000)
            day_num = None
            for tok in text.split():
                if tok.isdigit():
                    day_num = int(tok)
                    break
            if day_num is None:
                continue
            print(f"\n--- Dia {day_num} ---")
            print(f"class: {cls!r}")
            print(f"text: {text!r}")
            print(f"html: {html}")

        browser.close()


if __name__ == "__main__":
    main()
