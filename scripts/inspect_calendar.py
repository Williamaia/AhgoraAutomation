"""Lista dias do calendario com/sem estrela."""

from pathlib import Path

from playwright.sync_api import sync_playwright

HOME_URL = "https://hcm19.sapsf.com/sf/home?bplte_company=universoon"
STORAGE_PATH = Path(__file__).resolve().parent.parent / "auth" / "storage.json"
MIRROR_IFRAME = 'iframe[name="mirror-iframe"]'


def open_mirror(page):
    with page.expect_popup() as popup_info:
        page.get_by_role("link", name="Ajuste de Ponto").click()
    ajuste = popup_info.value
    with ajuste.expect_popup() as mirror_info:
        ajuste.get_by_role("link", name="Acessar  arrow_right_alt").click()
    mirror = mirror_info.value
    mirror.wait_for_load_state("networkidle", timeout=60_000)
    return mirror.frame_locator(MIRROR_IFRAME)


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

        frame = open_mirror(page)
        frame.locator(".v-calendar-weekly").wait_for(state="visible", timeout=60_000)

        days = frame.locator(".v-calendar-weekly__day").all()
        available = []

        for day_el in days:
            text = day_el.inner_text(timeout=2000).strip().replace("\n", " ")
            cls = day_el.get_attribute("class") or ""
            if not text:
                continue

            has_star = "star" in text.lower()
            day_num = text.replace("star", "").strip()
            if not day_num.isdigit():
                continue

            info = {
                "day": int(day_num),
                "has_star": has_star,
                "present": "v-present" in cls,
                "future": "v-future" in cls,
                "text": text,
            }
            print(info)
            if not has_star:
                available.append(info)

        print("\nDisponiveis (sem estrela):", [d["day"] for d in available])
        browser.close()


if __name__ == "__main__":
    main()
