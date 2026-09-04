import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(storage_state="auth/storage.json")
    page = context.new_page()
    page.goto("https://hcm19.sapsf.com/sf/home?bplte_company=universoon")
    with page.expect_popup() as page1_info:
        page.get_by_role("link", name="Ajuste de Ponto").click()
    page1 = page1_info.value
    with page1.expect_popup() as page2_info:
        page1.get_by_role("link", name="Acessar  arrow_right_alt").click()
    page2 = page2_info.value
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.get_by_role("button", name="Agosto/").click()
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.get_by_role("button", name="jul.").click()
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.locator("div").filter(has_text=re.compile(r"^7$")).first.click()
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.get_by_role("button", name="Incluir solicitação").click()
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.get_by_text("Solicitar abono keyboard_arrow_right").click()
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.get_by_text("access_time").first.click()
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.get_by_text("9").nth(2).click()
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.get_by_text("00", exact=True).click()
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.get_by_role("textbox", name="Hora final").click()
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.get_by_text("18").first.click()
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.get_by_text("00").first.click()
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.locator(".v-select__selections").click()
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.locator("a").filter(has_text="Teletrabalho").click()
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.locator("a").filter(has_text="Teletrabalho").click()
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.get_by_role("textbox", name="Mensagem").fill("Teletrabalho/HomeOffice")
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.get_by_role("textbox", name="Mensagem").press("ControlOrMeta+a")
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.get_by_role("textbox", name="Mensagem").press("ControlOrMeta+c")
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.get_by_role("textbox", name="Mensagem").click()
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.get_by_role("textbox", name="Mensagem").fill("Teletrabalho/HomeOffice")
    page2.locator("iframe[name=\"mirror-iframe\"]").content_frame.get_by_role("button", name="Enviar").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
