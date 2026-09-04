"""Inspeciona campos do formulario antes de Enviar."""

from pathlib import Path

from playwright.sync_api import sync_playwright

HOME_URL = "https://hcm19.sapsf.com/sf/home?bplte_company=universoon"
STORAGE_PATH = Path(__file__).resolve().parent.parent / "auth" / "storage.json"
MIRROR_IFRAME = 'iframe[name="mirror-iframe"]'


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, slow_mo=200)
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
            p1.value.get_by_role("link", name="Acessar  arrow_right_alt").click()
        mirror = p2.value
        mirror.wait_for_load_state("networkidle", timeout=60_000)
        frame = mirror.frame_locator(MIRROR_IFRAME)

        frame.locator(".v-calendar-weekly__day").filter(has_text="8").first.click(force=True)
        frame.get_by_role("button", name="Incluir solicitação").click()
        frame.get_by_text("Solicitar abono keyboard_arrow_right").click()

        print("=== Teste hora via access_time ===")
        frame.get_by_text("access_time").first.click()
        frame.get_by_text("9").nth(2).click()
        frame.get_by_text("00", exact=True).click()

        hora_inicio = frame.get_by_role("textbox", name="Hora inicial")
        print(f"Hora inicial value: {hora_inicio.input_value()}")

        print("=== Teste hora final ===")
        frame.get_by_role("textbox", name="Hora final").click()
        frame.get_by_text("18").first.click()
        frame.get_by_text("00").first.click()
        hora_fim = frame.get_by_role("textbox", name="Hora final")
        print(f"Hora final value: {hora_fim.input_value()}")

        frame.locator(".v-select__selections").click()
        frame.locator("a").filter(has_text="Teletrabalho").first.click()
        print(f"Motivo: {frame.locator('.v-select__selections').inner_text()!r}")
        print(f"Mensagem antes: {frame.get_by_role('textbox', name='Mensagem').input_value()!r}")

        frame.get_by_role("textbox", name="Mensagem").fill("Teletrabalho/HomeOffice")
        print(f"Mensagem depois: {frame.get_by_role('textbox', name='Mensagem').input_value()!r}")

        enviar = frame.get_by_role("button", name="Enviar")
        print(f"Enviar disabled: {enviar.is_disabled()}")
        print(f"Enviar visible: {enviar.is_visible()}")

        enviar.scroll_into_view_if_needed()
        enviar.click(force=True)
        mirror.wait_for_timeout(3000)

        print(f"Enviar ainda visivel: {enviar.is_visible()}")
        print(f"Form text snippet:")
        text = frame.locator("body").inner_text(timeout=5000)
        for line in text.splitlines():
            s = line.strip()
            if s and any(k in s.lower() for k in ["hora", "abono", "erro", "obrig", "enviar", "tele"]):
                print(f"  {s!r}")

        browser.close()


if __name__ == "__main__":
    main()
