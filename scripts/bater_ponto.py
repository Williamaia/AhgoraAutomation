"""Automacao de solicitacao de abono (Teletrabalho) no AhGora via SAP SuccessFactors."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path

from playwright.sync_api import FrameLocator, Page, sync_playwright

HOME_URL = "https://hcm19.sapsf.com/sf/home?bplte_company=universoon"
STORAGE_PATH = Path(__file__).resolve().parent.parent / "auth" / "storage.json"
MIRROR_IFRAME = 'iframe[name="mirror-iframe"]'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Registra abono de Teletrabalho no AhGora (SAP SuccessFactors)."
    )
    parser.add_argument(
        "--data",
        type=str,
        default=date.today().isoformat(),
        help="Data da solicitacao (YYYY-MM-DD). Padrao: hoje.",
    )
    parser.add_argument(
        "--hora-inicio",
        default="09:00",
        help="Hora inicial (HH:MM). Padrao: 09:00.",
    )
    parser.add_argument(
        "--hora-fim",
        default="18:00",
        help="Hora final (HH:MM). Padrao: 18:00.",
    )
    parser.add_argument(
        "--motivo",
        default="Teletrabalho",
        help="Motivo do abono. Padrao: Teletrabalho.",
    )
    parser.add_argument(
        "--mensagem",
        default="Teletrabalho/HomeOffice",
        help="Mensagem enviada na solicitacao.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Executa sem abrir janela do navegador.",
    )
    return parser.parse_args()


def mirror_frame(page: Page) -> FrameLocator:
    return page.frame_locator(MIRROR_IFRAME)


def open_ajuste_ponto(page: Page) -> Page:
    with page.expect_popup() as popup_info:
        page.get_by_role("link", name="Ajuste de Ponto").click()
    ajuste_page = popup_info.value

    with ajuste_page.expect_popup() as mirror_info:
        ajuste_page.get_by_role("link", name="Acessar  arrow_right_alt").click()

    return mirror_info.value


def get_available_days(frame: FrameLocator) -> list[int]:
    frame.locator(".v-calendar-weekly").wait_for(state="visible", timeout=60_000)
    available: list[int] = []

    for day_el in frame.locator(".v-calendar-weekly__day").all():
        text = day_el.inner_text(timeout=2000).strip().replace("\n", " ")
        if not text or "star" in text.lower():
            continue
        day_num = text.replace("star", "").strip()
        if day_num.isdigit():
            available.append(int(day_num))

    return sorted(set(available))


def resolve_day(available: list[int], preferred: date) -> int:
    if preferred.day in available:
        return preferred.day

    same_month_after = [day for day in available if day >= preferred.day]
    if same_month_after:
        return same_month_after[0]

    if available:
        return available[0]

    raise RuntimeError("Nenhum dia disponivel no calendario (todos ja possuem estrela).")


def select_day(frame: FrameLocator, target: date) -> int:
    available = get_available_days(frame)
    chosen_day = resolve_day(available, target)

    if chosen_day != target.day:
        print(
            f"Dia {target.day:02d} indisponivel (estrela ou fora do mes). "
            f"Usando dia {chosen_day:02d}."
        )

    day_cell = frame.locator(".v-calendar-weekly__day").filter(
        has_text=re.compile(rf"^{chosen_day}$")
    )
    if day_cell.count() == 0:
        day_cell = frame.locator("div").filter(has_text=re.compile(rf"^{chosen_day}$"))

    day_cell.first.scroll_into_view_if_needed()
    day_cell.first.click(force=True, timeout=60_000)

    frame.get_by_role("button", name="Incluir solicitação").wait_for(
        state="visible", timeout=30_000
    )

    return chosen_day


def set_start_time(frame: FrameLocator, time_value: str) -> None:
    hour, minute = time_value.split(":")
    hour_label = str(int(hour))

    frame.get_by_text("access_time").first.click()
    frame.get_by_text(hour_label).nth(2).click()
    frame.get_by_text(minute, exact=True).click()


def set_end_time(frame: FrameLocator, time_value: str) -> None:
    hour, minute = time_value.split(":")
    hour_label = str(int(hour))

    frame.get_by_role("textbox", name="Hora final").click()
    frame.get_by_text(hour_label).first.click()
    frame.get_by_text(minute, exact=True).first.click()


def fill_abono(
    frame: FrameLocator,
    *,
    hora_inicio: str,
    hora_fim: str,
    motivo: str,
    mensagem: str,
) -> None:
    frame.get_by_role("button", name="Incluir solicitação").click()
    frame.get_by_text("Solicitar abono keyboard_arrow_right").click()

    set_start_time(frame, hora_inicio)
    set_end_time(frame, hora_fim)

    frame.locator(".v-select__selections").click()
    frame.locator("a").filter(has_text=motivo).first.click()

    mensagem_field = frame.get_by_role("textbox", name="Mensagem")
    mensagem_field.fill(mensagem)

    enviar = frame.get_by_role("button", name="Enviar")
    enviar.scroll_into_view_if_needed()
    enviar.click(force=True, timeout=60_000)
    enviar.wait_for(state="hidden", timeout=60_000)


def run(args: argparse.Namespace) -> None:
    if not STORAGE_PATH.exists():
        print(f"Sessao nao encontrada: {STORAGE_PATH}")
        print("Execute primeiro: python scripts/login.py")
        sys.exit(1)

    target_date = datetime.strptime(args.data, "%Y-%m-%d").date()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=args.headless)
        context = browser.new_context(
            storage_state=str(STORAGE_PATH),
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
        )
        page = context.new_page()
        page.goto(HOME_URL, wait_until="domcontentloaded")

        mirror_page = open_ajuste_ponto(page)
        mirror_page.wait_for_load_state("networkidle", timeout=60_000)
        frame = mirror_frame(mirror_page)

        chosen_day = select_day(frame, target_date)
        fill_abono(
            frame,
            hora_inicio=args.hora_inicio,
            hora_fim=args.hora_fim,
            motivo=args.motivo,
            mensagem=args.mensagem,
        )

        print(
            f"Solicitacao enviada: {chosen_day:02d}/{target_date.month:02d}/{target_date.year} "
            f"{args.hora_inicio}-{args.hora_fim} ({args.motivo})"
        )

        context.close()
        browser.close()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
