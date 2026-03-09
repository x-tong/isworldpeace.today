# Is World Peace Today — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a static website that daily answers "Is the world at peace today?" with data from Wikipedia, auto-updated via GitHub Actions and deployed on GitHub Pages.

**Architecture:** Python script scrapes Wikipedia's ongoing armed conflicts page, writes `status.json`. A single `index.html` fetches that JSON and renders the answer. GitHub Actions runs the script daily and commits the result.

**Tech Stack:** Python (requests + beautifulsoup4, managed by uv), vanilla HTML/CSS/JS, GitHub Actions, GitHub Pages.

---

### Task 1: Project Setup — pyproject.toml

**Files:**
- Create: `pyproject.toml`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "isworldpeace-today"
version = "0.1.0"
description = "Is the world at peace today?"
requires-python = ">=3.12"
dependencies = [
    "requests>=2.31",
    "beautifulsoup4>=4.12",
]
```

**Step 2: Verify uv can resolve dependencies**

Run: `uv sync`
Expected: Creates `uv.lock` and `.venv/` successfully.

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: init project with uv and dependencies"
```

---

### Task 2: Data Pipeline — update.py (test first)

**Files:**
- Create: `tests/test_update.py`
- Create: `tests/fixtures/conflicts.html`
- Create: `update.py`

**Step 1: Fetch a sample of the Wikipedia page for test fixtures**

Save a trimmed copy of https://en.wikipedia.org/wiki/List_of_ongoing_armed_conflicts as `tests/fixtures/conflicts.html`. Only keep the `<table class="wikitable">` sections (2-3 tables) to keep the fixture small. The page has tables organized by conflict intensity — preserve the table headers so we can identify categories.

**Step 2: Write the failing test**

```python
# tests/test_update.py
import json
from pathlib import Path
from update import parse_conflicts, build_status

FIXTURE = Path(__file__).parent / "fixtures" / "conflicts.html"


def test_parse_conflicts_returns_dict_with_categories():
    html = FIXTURE.read_text()
    result = parse_conflicts(html)
    assert isinstance(result, dict)
    assert "total" in result
    assert result["total"] > 0
    # Should have conflict category breakdown
    assert "conflicts" in result
    assert isinstance(result["conflicts"], dict)


def test_parse_conflicts_counts_match_total():
    html = FIXTURE.read_text()
    result = parse_conflicts(html)
    category_sum = sum(result["conflicts"].values())
    assert category_sum == result["total"]


def test_build_status_structure():
    conflicts_data = {
        "total": 5,
        "conflicts": {"major_wars": 1, "wars": 2, "minor_conflicts": 2},
    }
    status = build_status(conflicts_data)
    assert status["peace"] is False
    assert status["total"] == 5
    assert "date" in status
    assert "day_counter" in status
    assert isinstance(status["day_counter"], int)
    assert status["day_counter"] > 0


def test_build_status_peace_when_zero():
    conflicts_data = {"total": 0, "conflicts": {}}
    status = build_status(conflicts_data)
    assert status["peace"] is True
```

**Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_update.py -v`
Expected: FAIL — `ImportError: cannot import name 'parse_conflicts' from 'update'`

**Step 4: Implement update.py**

```python
# update.py
"""Scrape Wikipedia for ongoing armed conflicts and generate status.json."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/List_of_ongoing_armed_conflicts"

# WWII end date — "Day N of asking"
EPOCH = date(1945, 9, 2)

# Map Wikipedia table section headings to category keys.
# The page organizes conflicts by intensity in separate tables preceded by
# headings like "Major wars (10,000+ deaths in current or past year)".
CATEGORY_MAP: dict[str, str] = {
    "major wars": "major_wars",
    "wars": "wars",
    "minor conflicts": "minor_conflicts",
    "skirmishes": "skirmishes",
}


def fetch_html(url: str = WIKIPEDIA_URL) -> str:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_conflicts(html: str) -> dict:
    """Parse conflict tables and return categorized counts."""
    soup = BeautifulSoup(html, "html.parser")
    conflicts: dict[str, int] = {}
    total = 0

    # Find all wikitables — each is preceded by a heading indicating category
    tables = soup.select("table.wikitable")
    for table in tables:
        # Walk backwards to find the nearest heading
        category_key = _detect_category(table)
        # Count rows (minus header)
        rows = table.find_all("tr")
        count = max(0, len(rows) - 1)
        if category_key:
            conflicts[category_key] = conflicts.get(category_key, 0) + count
        total += count

    return {"total": total, "conflicts": conflicts}


def _detect_category(table) -> str | None:
    """Find the heading before a table and map it to a category key."""
    for sibling in table.previous_siblings:
        if sibling.name and sibling.name.startswith("h"):
            text = sibling.get_text().lower()
            for keyword, key in CATEGORY_MAP.items():
                if keyword in text:
                    return key
            # Unknown heading — use generic key
            return "other"
    return "other"


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
```

**Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_update.py -v`
Expected: All 4 tests PASS.

**Step 6: Run update.py manually to generate initial status.json**

Run: `uv run python update.py`
Expected: `status.json` created with today's data.

**Step 7: Commit**

```bash
git add update.py tests/test_update.py tests/fixtures/conflicts.html status.json
git commit -m "feat: add data pipeline — scrape Wikipedia for armed conflicts"
```

---

### Task 3: Static Page — index.html

**Files:**
- Create: `index.html`

**Step 1: Create index.html**

Single HTML file with embedded CSS and JS. Design spec:

- **Fonts**: Playfair Display + DM Mono from Google Fonts
- **Background**: `#0a0a0a` with CSS grain overlay
- **"NO"**: `#c23616`, `clamp(8rem, 25vw, 20rem)` font size, fade-in animation
- **Layout**: flexbox vertical center, full viewport
- **Responsive**: `clamp()` for all font sizes
- **Animation**: "NO" fades in with subtle scale, inscription delays 1s
- **OG tags**: title, description for social sharing
- **JS**: fetch `status.json`, update DOM elements (answer, day counter, conflict count, date)

Key HTML structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Is the world at peace today?</title>
    <meta property="og:title" content="Is the world at peace today?">
    <meta property="og:description" content="Find out if humanity has achieved world peace.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Mono:wght@400&display=swap" rel="stylesheet">
    <style>/* all CSS here */</style>
</head>
<body>
    <main>
        <h1 class="question">Is the world at peace today?</h1>
        <div id="answer" class="answer">...</div>
        <p id="counter" class="counter"></p>
        <p id="meta" class="meta"></p>
        <hr class="divider">
        <p class="inscription">
            If this page ever shows YES,<br>
            humanity achieved something remarkable.
        </p>
    </main>
    <script>/* fetch + render logic */</script>
</body>
</html>
```

CSS details (embedded in `<style>`):
- `body`: `margin:0; background:#0a0a0a; color:#e0e0e0; font-family:'Playfair Display',serif;` flex center
- `.answer`: `font-size:clamp(8rem,25vw,20rem); font-weight:900; color:#c23616;` with `text-shadow: 0 0 40px rgba(194,54,22,0.3);`
- `.answer.peace`: `color:#27ae60;` with matching green shadow
- `@keyframes fadeIn`: `from{opacity:0;transform:scale(1.02)} to{opacity:1;transform:scale(1)}`
- `.answer`: `animation: fadeIn 1.5s ease-out`
- `.inscription`: `animation: fadeIn 1s ease-out 1s both;` (1s delay)
- Grain overlay via `body::after` with CSS `noise` or SVG filter
- `.counter, .meta`: `font-family:'DM Mono',monospace; color:#666;`
- `.divider`: `border-color:#333; max-width:200px;`

JS logic (embedded in `<script>`):
```javascript
fetch("status.json")
  .then(r => r.json())
  .then(data => {
    const answer = document.getElementById("answer");
    answer.textContent = data.peace ? "YES" : "NO";
    if (data.peace) answer.classList.add("peace");

    document.getElementById("counter").textContent =
      `Day ${data.day_counter.toLocaleString()} of asking.`;

    document.getElementById("meta").textContent =
      `${data.total} active conflicts · ${data.date}`;
  });
```

**Step 2: Test locally**

Run: `python3 -m http.server 8000` and open `http://localhost:8000` in browser.
Expected: Page loads, shows data from `status.json`, "NO" in large red text, grain texture visible.

**Step 3: Commit**

```bash
git add index.html
git commit -m "feat: add static page with editorial brutalism design"
```

---

### Task 4: GitHub Actions — update.yml

**Files:**
- Create: `.github/workflows/update.yml`

**Step 1: Create the workflow file**

```yaml
name: Update peace status

on:
  schedule:
    - cron: "0 0 * * *"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v4

      - name: Run update script
        run: uv run python update.py

      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add status.json
          git diff --cached --quiet || git commit -m "chore: update peace status for $(date -u +%Y-%m-%d)"
          git push
```

Key details:
- `workflow_dispatch` allows manual trigger for testing
- `permissions: contents: write` so the bot can push
- `git diff --cached --quiet ||` ensures no empty commits
- Uses `astral-sh/setup-uv` for uv in CI

**Step 2: Validate YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/update.yml'))"`
(If pyyaml not available, just visually verify indentation is correct.)

**Step 3: Commit**

```bash
git add .github/workflows/update.yml
git commit -m "ci: add daily update workflow"
```

---

### Task 5: GitHub Pages Setup & Final Polish

**Files:**
- Modify: `index.html` (if any issues found during local testing)

**Step 1: Ensure `.nojekyll` exists**

Create empty `.nojekyll` file so GitHub Pages serves files as-is:
```bash
touch .nojekyll
```

**Step 2: Final local test**

Run: `python3 -m http.server 8000`
- Verify page renders correctly
- Verify responsive design (resize browser / use devtools mobile view)
- Verify grain texture
- Verify animations

**Step 3: Commit**

```bash
git add .nojekyll
git commit -m "chore: add .nojekyll for GitHub Pages"
```

**Step 4: Push and enable GitHub Pages**

Push to `main` branch, then enable GitHub Pages in repo settings:
- Settings → Pages → Source: "Deploy from a branch" → Branch: `main`, folder: `/ (root)`

---

### Task 6: End-to-End Verification

**Step 1: Trigger workflow manually**

Go to Actions tab → "Update peace status" → "Run workflow" (or `gh workflow run update.yml`).

**Step 2: Verify status.json was updated**

Check the commit history — should see a new commit from `github-actions[bot]`.

**Step 3: Verify the live site**

Open `https://<username>.github.io/isworldpeace.today/` and verify everything works.

**Step 4: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: address issues found during e2e verification"
```
