"""Generate the project README based on the downloaded events database."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Iterable, List, Sequence
import difflib

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
    "atualizado.\n\n"
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


def dedupe_events(events: Sequence[dict]) -> List[dict]:
    """Remove eventos duplicados baseando-se em data, local e similaridade do nome.

    Dois eventos são considerados iguais se:
    - tiverem o mesmo conjunto de datas, e
    - cidade e uf normalizados forem iguais, e
    - (urls iguais ou similaridade de nome > 0.80)

    Em caso de duplicata, fazemos uma mesclagem simples preferindo campos não vazios
    e nomes mais longos.
    """

    unique: List[dict] = []
    for ev in events:
        ev_days = set(d.strip() for d in ev.get("data", []))
        ev_city = (ev.get("cidade") or "").strip().lower()
        ev_uf = (ev.get("uf") or "").strip().upper()
        ev_url = (ev.get("url") or "").strip()
        ev_name = (ev.get("nome") or "").strip()

        merged = False
        for u in unique:
            u_days = set(d.strip() for d in u.get("data", []))
            u_city = (u.get("cidade") or "").strip().lower()
            u_uf = (u.get("uf") or "").strip().upper()
            u_url = (u.get("url") or "").strip()
            u_name = (u.get("nome") or "").strip()

            if ev_days == u_days and ev_city == u_city and ev_uf == u_uf:
                # same date and location, check url or name similarity
                same_url = bool(ev_url and u_url and ev_url == u_url)
                name_sim = difflib.SequenceMatcher(None, ev_name.lower(), u_name.lower()).ratio()
                if same_url or name_sim >= 0.80:
                    # merge into u: prefer longer name, prefer non-empty url, prefer defined tipo
                    if len(ev_name) > len(u_name):
                        u["nome"] = ev_name
                    if not u_url and ev_url:
                        u["url"] = ev_url
                    # merge cidade/uf if missing
                    if not u.get("cidade") and ev.get("cidade"):
                        u["cidade"] = ev.get("cidade")
                    if not u.get("uf") and ev.get("uf"):
                        u["uf"] = ev.get("uf")
                    # prefer explicit tipo
                    if (u.get("tipo") or "").strip().lower() in ("", "indefinido") and ev.get("tipo"):
                        u["tipo"] = ev.get("tipo")
                    merged = True
                    break

        if not merged:
            unique.append(dict(ev))

    return unique


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

    months_output = []
    for month in sort_months(target_year.get("meses", [])):
        if month.get("arquivado") or not month.get("eventos"):
            continue
        # deduplicate month events before formatting
        events = month.get("eventos", [])
        deduped = dedupe_events(events)
        month_copy = dict(month)
        month_copy["eventos"] = deduped
        months_output.append(build_month_section(month_copy))

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
