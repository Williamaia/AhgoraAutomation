import re
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

LOGIN_URL = "https://hcm19.sapsf.com/sf/home?bplte_company=universoon"
STORAGE_PATH = Path(__file__).resolve().parent.parent / "auth" / "storage.json"


def main() -> None:
    STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)

    print()
    print("=== Login manual — SAP SuccessFactors ===")
    print()
    print("1. O navegador vai abrir na página de login.")
    print("2. Digite usuário e senha DIRETAMENTE no navegador.")
    print("   (nada é digitado ou salvo neste terminal)")
    print("3. A sessão será salva automaticamente ao entrar na home.")
    print("   (ou pressione ENTER no terminal quando estiver logado)")
    print()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
        )
        page = context.new_page()
        page.goto(LOGIN_URL, wait_until="domcontentloaded")

        print("Aguardando você concluir o login no navegador...")
        print("(salvando automaticamente ao detectar a home — até 10 min)")
        print()

        try:
            page.wait_for_url(re.compile(r".*/sf/home.*"), timeout=600_000)
            print("Login detectado na home.")
        except PlaywrightTimeoutError:
            print("Tempo esgotado. Pressione ENTER se já estiver logado...")
            try:
                input()
            except EOFError:
                print("Terminal não interativo — salvando sessão atual.")

        context.storage_state(path=str(STORAGE_PATH))
        browser.close()

    print()
    print(f"Sessão salva em: {STORAGE_PATH}")
    print("Credenciais NÃO foram armazenadas — apenas cookies da sessão.")
    print()


if __name__ == "__main__":
    main()
