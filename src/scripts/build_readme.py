"""Generate the project README based on the downloaded events database."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Iterable, List, Sequence

MONTH_ORDER = [
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
]

MONTH_LABEL = {
    "janeiro": "JANEIRO",
    "fevereiro": "FEVEREIRO",
    "março": "MARCO",
    "abril": "ABRIL",
    "maio": "MAIO",
    "junho": "JUNHO",
    "julho": "JULHO",
    "agosto": "AGOSTO",
    "setembro": "SETEMBRO",
    "outubro": "OUTUBRO",
    "novembro": "NOVEMBRO",
    "dezembro": "DEZEMBRO",
}

EVENT_TYPE_EMOJI = {
    "presencial": "🏢",
    "online": "💻",
    "hibrido": "🔀",
}

README_INTRO = (
    "# Agenda Tech Brasil\n\n"
    "Lista de eventos coletados automaticamente a partir do banco de dados do projeto "
    "Agenda Tech Brasil. O conteúdo abaixo é recriado sempre que o banco de dados é "
    "atualizado.\n"
)


def load_database(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as resource:
        return json.load(resource)


def pick_target_year(database: dict, requested_year: int | None) -> dict:
    years = [year for year in database.get("eventos", []) if not year.get("arquivado")]
    if not years:
        raise ValueError("no active years found in database")

    target_year = requested_year if requested_year is not None else date.today().year
    for year in years:
        if year.get("ano") == target_year:
            return year

    raise ValueError(f"year {target_year} not found in database")


def sort_months(months: Sequence[dict]) -> List[dict]:
    order_index = {month: index for index, month in enumerate(MONTH_ORDER)}
    return sorted(months, key=lambda item: order_index.get(item.get("mes"), 99))


def sort_events(events: Iterable[dict]) -> List[dict]:
    def first_day(entry: dict) -> int:
        days = entry.get("data", [])
        return min(int(day) for day in days) if days else 99

    return sorted(events, key=first_day)


def format_days(days: Sequence[str]) -> str:
    cleaned = [str(int(day)) for day in days if day]
    if not cleaned:
        return "Data a confirmar"
    if len(cleaned) == 1:
        return cleaned[0]
    return ", ".join(cleaned[:-1]) + f" e {cleaned[-1]}"


def format_location(city: str, state: str) -> str:
    city = city.strip()
    state = state.strip()
    if city and state:
        return f" - _{city}/{state}_"
    if city:
        return f" - _{city}_"
    if state:
        return f" - _{state}_"
    return ""


def format_badge(event_type: str) -> str:
    normalized = event_type.strip().lower().replace("í", "i")
    return EVENT_TYPE_EMOJI.get(normalized, "❓")


def build_month_section(month: dict) -> str:
    month_name = month.get("mes", "").strip().lower()
    if not month_name or not month.get("eventos"):
        return ""

    comment_label = MONTH_LABEL.get(month_name, month_name.upper())
    header = f"### {month_name.capitalize()}"
    lines = [header, f"<!-- {comment_label}:START -->"]

    for event in sort_events(month.get("eventos", [])):
        days = format_days(event.get("data", []))
        url = event.get("url", "").strip()
        name = event.get("nome", "Evento sem título").strip()
        location = format_location(event.get("cidade", ""), event.get("uf", ""))
        event_type = event.get("tipo", "indefinido")
        badge = format_badge(event_type)
        bullet = f"- {days}: [{name}]({url}){location} {badge}"
        lines.append(bullet)

    lines.append(f"<!-- {comment_label}:END -->")
    return "\n".join(lines) + "\n"


def build_readme_content(target_year: dict) -> str:
    sections = [README_INTRO]
    year_value = target_year.get("ano")
    sections.append(f"## Eventos em {year_value}\n")
    sections.append(f"<!-- ANO{year_value}:START -->\n")

    months_output = [
        build_month_section(month)
        for month in sort_months(target_year.get("meses", []))
        if not month.get("arquivado") and month.get("eventos")
    ]

    sections.extend(months_output)
    sections.append(f"<!-- ANO{year_value}:END -->\n")
    return "".join(sections)


def write_readme(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-path",
        default=Path(__file__).resolve().parents[1] / "db" / "database.json",
        type=Path,
        help="Path to the downloaded database.json file",
    )
    parser.add_argument(
        "--output",
        default=Path(__file__).resolve().parents[2] / "README.md",
        type=Path,
        help="Target README file to overwrite",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Specific year to export (defaults to the current calendar year)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    database = load_database(args.db_path)
    target_year = pick_target_year(database, args.year)
    content = build_readme_content(target_year)
    write_readme(args.output, content)


if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
