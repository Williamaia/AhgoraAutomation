"""Registra abono para todos os dias uteis sem estrela em um mes."""

from __future__ import annotations

import argparse
import calendar
import re
import sys
from datetime import date
from pathlib import Path

from playwright.sync_api import FrameLocator, sync_playwright

from bater_ponto import (
    HOME_URL,
    STORAGE_PATH,
    fill_abono,
    mirror_frame,
    open_ajuste_ponto,
)

MONTH_SHORT = {
    1: "JAN.",
    2: "FEV.",
    3: "MAR.",
    4: "ABR.",
    5: "MAI.",
    6: "JUN.",
    7: "JUL.",
    8: "AGO.",
    9: "SET.",
    10: "OUT.",
    11: "NOV.",
    12: "DEZ.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Registra abono para dias uteis sem estrela em um mes."
    )
    parser.add_argument("--mes", required=True, help="Mes alvo no formato YYYY-MM.")
    parser.add_argument("--hora-inicio", default="09:00")
    parser.add_argument("--hora-fim", default="18:00")
    parser.add_argument("--motivo", default="Teletrabalho")
    parser.add_argument("--mensagem", default="Teletrabalho/HomeOffice")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--min-dia",
        type=int,
        default=1,
        help="Ignora dias anteriores a este numero no mes.",
    )
    parser.add_argument(
        "--max-dia",
        type=int,
        default=31,
        help="Ignora dias posteriores a este numero no mes.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas lista os dias que seriam processados.",
    )
    return parser.parse_args()


def parse_month(value: str) -> tuple[int, int]:
    year_str, month_str = value.split("-", maxsplit=1)
    year = int(year_str)
    month = int(month_str)
    if month < 1 or month > 12:
        raise ValueError("Mes invalido.")
    return year, month


def is_weekday(year: int, month: int, day: int) -> bool:
    return date(year, month, day).weekday() < 5


MONTH_LONG = {
    1: "janeiro",
    2: "fevereiro",
    3: "marco",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}


def _strip_accents(value: str) -> str:
    import unicodedata
    return "".join(
        c
        for c in unicodedata.normalize("NFD", value)
        if unicodedata.category(c) != "Mn"
    )


def current_month_year(frame: FrameLocator) -> tuple[int, int]:
    button = frame.locator("button").filter(has_text=re.compile(r"/20\d{2}")).first
    raw = button.inner_text(timeout=5_000).replace("\n", " ").strip()
    label = _strip_accents(raw).lower()
    match = re.search(r"([a-z]+)\s*/\s*(20\d{2})", label)
    if not match:
        raise RuntimeError(f"Nao consegui interpretar o mes atual: {raw!r}")
    month_name, year_str = match.group(1), match.group(2)
    for num, name in MONTH_LONG.items():
        if name.startswith(month_name[:3]):
            return int(year_str), num
    raise RuntimeError(f"Mes desconhecido no botao: {raw!r}")


def _click_arrow(frame: FrameLocator, direction: str) -> None:
    btn = frame.locator("button:visible").filter(has_text=direction).first
    btn.click()


def _open_month_picker(frame: FrameLocator) -> None:
    frame.locator("button").filter(has_text="keyboard_arrow_down").first.click()


def _adjust_year(frame: FrameLocator, page, target_year: int) -> None:
    for _ in range(20):
        year_btn = frame.locator("button:visible").filter(
            has_text=re.compile(r"^20\d{2}$")
        ).first
        current_year = int(year_btn.inner_text(timeout=5_000).strip())
        if current_year == target_year:
            return
        arrow = "chevron_left" if current_year > target_year else "chevron_right"
        _click_arrow(frame, arrow)
        page.wait_for_timeout(200)
    raise RuntimeError(f"Nao consegui ajustar o ano para {target_year}.")


def _wait_for_month(frame: FrameLocator, page, year: int, month: int, timeout_ms: int = 60_000) -> None:
    """Aguarda o botao de mes refletir o mes/ano alvo."""
    step_ms = 500
    elapsed = 0
    while elapsed < timeout_ms:
        try:
            cur_year, cur_month = current_month_year(frame)
            if (cur_year, cur_month) == (year, month):
                return
        except Exception:
            pass
        page.wait_for_timeout(step_ms)
        elapsed += step_ms
    cur_year, cur_month = current_month_year(frame)
    raise RuntimeError(
        f"Falhou ao navegar para {month:02d}/{year}. Atual: {cur_month:02d}/{cur_year}."
    )


def go_to_month(frame: FrameLocator, page, year: int, month: int) -> None:
    frame.locator(".v-calendar-weekly").wait_for(state="visible", timeout=60_000)

    def _wait_calendar_settled() -> None:
        """Aguarda o calendario terminar de renderizar (icones carregados)."""
        frame.locator(".v-calendar-weekly").wait_for(state="visible", timeout=60_000)
        page.wait_for_timeout(3_000)

    for attempt in range(3):
        cur_year, cur_month = current_month_year(frame)
        if (cur_year, cur_month) == (year, month):
            _wait_calendar_settled()
            return

        _open_month_picker(frame)
        page.wait_for_timeout(800)
        _adjust_year(frame, page, year)
        frame.locator("button:visible").filter(has_text=MONTH_SHORT[month]).first.click()
        try:
            _wait_for_month(frame, page, year, month, timeout_ms=60_000)
            _wait_calendar_settled()
            return
        except RuntimeError:
            if attempt == 2:
                raise
            page.wait_for_timeout(1500)


def day_marker(day_el) -> str | None:
    """Retorna o nome do icone dentro de .icon-attach, ou None se estiver livre."""
    icon_locator = day_el.locator(".icon-attach i")
    if icon_locator.count() == 0:
        return None
    return icon_locator.first.inner_text(timeout=2000).strip().lower() or None


def extract_day_number(text: str) -> int | None:
    for token in text.split():
        if token.isdigit():
            return int(token)
    match = re.search(r"\b(\d{1,2})\b", text)
    if match:
        return int(match.group(1))
    return None


def get_month_days(frame: FrameLocator) -> list[dict[str, object]]:
    days: list[dict[str, object]] = []

    for day_el in frame.locator(".v-calendar-weekly__day").all():
        text = day_el.inner_text(timeout=2000).strip().replace("\n", " ")
        cls = day_el.get_attribute("class") or ""
        if "v-outside" in cls or not text:
            continue

        day_num = extract_day_number(text)
        if day_num is None:
            continue

        marker = day_marker(day_el)
        days.append(
            {
                "day": day_num,
                "marker": marker,
                "already_marked": marker is not None,
            }
        )

    return days


def select_specific_day(frame: FrameLocator, day: int) -> None:
    candidates = frame.locator(".v-calendar-weekly__day").all()
    for el in candidates:
        cls = el.get_attribute("class") or ""
        if "v-outside" in cls:
            continue
        text = el.inner_text(timeout=2000).strip().replace("\n", " ")
        if extract_day_number(text) == day:
            el.scroll_into_view_if_needed()
            el.click(force=True, timeout=60_000)
            frame.get_by_role("button", name="Incluir solicitação").wait_for(
                state="visible", timeout=30_000
            )
            return
    raise RuntimeError(f"Dia {day} nao encontrado no calendario atual.")


def target_weekdays(
    year: int,
    month: int,
    frame: FrameLocator,
    *,
    min_day: int,
    max_day: int,
) -> list[int]:
    month_days = get_month_days(frame)
    last_day = calendar.monthrange(year, month)[1]

    marked = sorted(
        (int(d["day"]), d["marker"])
        for d in month_days
        if d["already_marked"]
    )
    livres = sorted(int(d["day"]) for d in month_days if not d["already_marked"])
    unseen = sorted(
        day
        for day in range(1, last_day + 1)
        if day not in {int(d["day"]) for d in month_days}
    )

    targets = [
        day
        for day in livres
        if min_day <= day <= min(max_day, last_day)
        and is_weekday(year, month, day)
    ]

    print(f"Dias ja marcados (com icone): {marked}")
    if unseen:
        print(f"Dias fora do calendario carregado: {unseen}")
    print(f"Dias livres (sem icone): {livres}")
    print(f"Dias uteis a processar: {targets}")
    return targets


def run(args: argparse.Namespace) -> None:
    if not STORAGE_PATH.exists():
        print(f"Sessao nao encontrada: {STORAGE_PATH}")
        print("Execute primeiro: python scripts/login.py")
        sys.exit(1)

    year, month = parse_month(args.mes)

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

        go_to_month(frame, mirror_page, year, month)
        targets = target_weekdays(
            year,
            month,
            frame,
            min_day=args.min_dia,
            max_day=args.max_dia,
        )

        if args.dry_run:
            browser.close()
            return

        processed: list[int] = []
        failed: list[tuple[int, str]] = []

        for day in targets:
            try:
                frame.locator(".v-calendar-weekly").wait_for(
                    state="visible", timeout=60_000
                )
                select_specific_day(frame, day)
                fill_abono(
                    frame,
                    hora_inicio=args.hora_inicio,
                    hora_fim=args.hora_fim,
                    motivo=args.motivo,
                    mensagem=args.mensagem,
                )
                processed.append(day)
                print(
                    f"OK {day:02d}/{month:02d}/{year} "
                    f"{args.hora_inicio}-{args.hora_fim}"
                )
                mirror_page.wait_for_timeout(1_000)
            except Exception as exc:
                failed.append((day, str(exc)))
                print(f"ERRO {day:02d}/{month:02d}/{year}: {exc}")

        print()
        print(f"Concluidos: {processed}")
        if failed:
            print(f"Falhas: {failed}")
            sys.exit(1)

        context.close()
        browser.close()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
