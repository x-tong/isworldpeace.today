"""Scrape Wikipedia for ongoing armed conflicts and generate status.json."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/List_of_ongoing_armed_conflicts"

# WWII end date — "Day N of asking"
EPOCH = date(1945, 9, 2)

# Map Wikipedia table section headings to category keys.
CATEGORY_MAP: dict[str, str] = {
    "major wars": "major_wars",
    "minor wars": "minor_wars",
    "conflicts": "conflicts",
    "skirmishes": "skirmishes",
}


def fetch_html(url: str = WIKIPEDIA_URL) -> str:
    resp = requests.get(
        url,
        headers={"User-Agent": "isworldpeace.today/0.1 (educational project)"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text


def parse_conflicts(html: str) -> dict:
    """Parse conflict tables and return categorized counts."""
    soup = BeautifulSoup(html, "lxml")
    conflicts: dict[str, int] = {}
    total = 0

    tables = soup.select("table.wikitable")
    for table in tables:
        category_key = _detect_category(table)
        if category_key is None:
            continue  # skip non-conflict tables (e.g. death statistics)
        rows = table.find_all("tr")
        count = max(0, len(rows) - 1)  # exclude header row
        conflicts[category_key] = conflicts.get(category_key, 0) + count
        total += count

    return {"total": total, "conflicts": conflicts}


def _detect_category(table: Tag) -> str | None:
    """Find the heading before a table and map it to a category key."""
    for sibling in table.previous_siblings:
        if not isinstance(sibling, Tag):
            continue
        # Wikipedia wraps headings in div.mw-heading
        heading_tag = None
        if sibling.name and sibling.name.startswith("h"):
            heading_tag = sibling
        elif sibling.name == "div" and "mw-heading" in sibling.get("class", []):
            heading_tag = sibling.find(["h2", "h3", "h4"])

        if heading_tag:
            text = heading_tag.get_text().lower()
            for keyword, key in CATEGORY_MAP.items():
                if keyword in text:
                    return key
            # Heading found but not a conflict category — skip this table.
            return None
    return None


def build_status(conflicts_data: dict) -> dict:
    """Build the status.json structure."""
    today = date.today()
    return {
        "date": str(today),
        "peace": conflicts_data["total"] == 0,
        "conflicts": conflicts_data["conflicts"],
        "total": conflicts_data["total"],
        "day_counter": (today - EPOCH).days,
    }


def main() -> None:
    html = fetch_html()
    conflicts_data = parse_conflicts(html)
    status = build_status(conflicts_data)

    out = Path("status.json")
    out.write_text(json.dumps(status, indent=2) + "\n")
    print(f"Updated: peace={status['peace']}, total={status['total']}")


if __name__ == "__main__":
    main()
