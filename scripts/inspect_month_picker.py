"""Testa se conseguimos selecionar julho no dropdown do calendario."""

from pathlib import Path

from playwright.sync_api import sync_playwright

HOME_URL = "https://hcm19.sapsf.com/sf/home?bplte_company=universoon"
STORAGE_PATH = Path(__file__).resolve().parent.parent / "auth" / "storage.json"
MIRROR_IFRAME = 'iframe[name="mirror-iframe"]'


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

        month_btn = (
            frame.locator("button")
            .filter(has_text="keyboard_arrow_down")
            .first
        )
        print(f"Antes: {month_btn.inner_text(timeout=5000)!r}")
        month_btn.click()
        mirror.wait_for_timeout(1500)

        jul = frame.locator("button:visible").filter(has_text="JUL.").first
        print(f"JUL. disabled: {jul.is_disabled()}")
        print(f"JUL. class: {jul.get_attribute('class')}")
        jul.click()
        mirror.wait_for_timeout(2000)

        print(f"Depois clique JUL: {month_btn.inner_text(timeout=5000)!r}")

        buttons = frame.locator("button:visible").all()
        for btn in buttons:
            try:
                text = btn.inner_text(timeout=500).strip().replace("\n", " ")
                if text and ("/" in text or "20" in text or "OK" in text.upper() or "CONFIRM" in text.upper()):
                    print(f"  visible btn: {text!r}")
            except Exception:
                pass

        browser.close()


if __name__ == "__main__":
    main()
