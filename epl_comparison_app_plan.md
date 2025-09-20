# 📋 Streamlit EPL Comparison App — Build Plan

This document outlines the steps to build a Streamlit app that compares EPL team performance between the **2025/26 season (current)** and the **2024/25 season (previous)** using fixture mapping.

---

## 1. Project Setup
- Repo already created ✅
- Ensure branch protection rules on `main`
- Add `.gitignore` for Python/Poetry projects
- Add `CLAUDE.md` (see section 10 for contents)

### Environment
- Use **Poetry** for dependency management:
  ```bash
  poetry init
  poetry add streamlit pandas requests pytest ruff black flake8
  ```
- Activate environment:
  ```bash
  poetry shell
  ```

---

## 2. Data Sourcing
- **Source**: Use [Football-Data.org](https://www.football-data.org/) free API for EPL.
- **Required data**:
  - EPL fixtures + results for **2025/26** and **2024/25**
  - Championship final standings from **2024/25** (to map promoted teams)
- **Implementation**:
  - Create `src/data_fetcher.py`
    - `get_fixtures(season: int) -> pd.DataFrame`
    - `get_results(season: int) -> pd.DataFrame`
  - Cache raw data as CSV in `/data/` to avoid API limits.

---

## 3. Fixture Mapping Logic
- Create `src/fixture_mapper.py`
- Responsibilities:
  - Match each fixture in 2025/26 to the equivalent in 2024/25
    - Match by `home_team`, `away_team`
  - Handle promoted/relegated teams:
    - Rank promoted Championship teams
    - Map them to relegated EPL teams (1st → 18th, 2nd → 19th, 3rd → 20th)
- Output: dataframe with aligned fixtures.

---

## 4. Comparison Engine
- Create `src/comparison.py`
- Responsibilities:
  - For each team:
    - Aggregate **points** and **goal difference** for 2025/26 fixtures
    - Aggregate the same for mapped 2024/25 fixtures
  - Output table with schema:

  | Team | Points 25/26 | GD 25/26 | Points 24/25 (mapped) | GD 24/25 (mapped) |

---

## 5. Streamlit UI
- Main entrypoint: `app.py`
- Layout:
  - **Sidebar**:
    - Team dropdown
  - **Main panel**:
    - Table of all teams (filtered if team selected)
    - Conditional formatting (improvements in green, declines in red)
  - **Optional**: bar chart of Δ Points and Δ GD

---

## 6. Testing
- Use `pytest`
- Store test data in `/tests/data/`
- Tests:
  - Data fetching schema
  - Fixture mapping correctness (including promoted/relegated handling)
  - Comparison logic with sample data

Run:
```bash
pytest
```

---

## 7. GitHub Workflow
- Add `.github/workflows/ci.yml`:

  ```yaml
  name: CI

  on:
    push:
      branches: [main]
    pull_request:
      branches: [main]

  jobs:
    build:
      runs-on: ubuntu-latest

      steps:
        - uses: actions/checkout@v3

        - name: Set up Python
          uses: actions/setup-python@v4
          with:
            python-version: '3.11'

        - name: Install Poetry
          run: pip install poetry

        - name: Install dependencies
          run: poetry install

        - name: Lint
          run: poetry run ruff check . && poetry run black --check .

        - name: Run tests
          run: poetry run pytest

        - name: Streamlit health check
          run: poetry run streamlit run app.py --headless & sleep 15
  ```

- Require ✅ checks on PRs before merging.

---

## 8. Deployment
- Use **Streamlit Cloud**
- Ensure `requirements.txt` is generated for compatibility:
  ```bash
  poetry export -f requirements.txt --output requirements.txt --without-hashes
  ```
- Store API keys in Streamlit Cloud secrets manager.
- Configure auto-deploy on merge to `main`.

---

## 9. Documentation
- `README.md` should include:
  - Project description
  - Setup instructions with Poetry
  - How to run locally:
    ```bash
    poetry run streamlit run app.py
    ```
  - Testing instructions
  - Deployment link (Streamlit Cloud URL)

---

## 10. CLAUDE.md
Create `CLAUDE.md` in the repo root to guide AI contributions. Suggested contents:

```markdown
# CLAUDE Project Guidelines

## Coding Standards
- Use Python 3.11
- Manage dependencies with Poetry
- Follow PEP8 + run `ruff` and `black`
- Keep modules small and focused:
  - `data_fetcher.py` → external data
  - `fixture_mapper.py` → mapping logic
  - `comparison.py` → aggregation/comparison
  - `app.py` → Streamlit UI

## Git Workflow
- Use feature branches: `feature/<name>`
- PRs require:
  - ✅ CI checks (lint, tests, health check)
  - At least one reviewer approval

## Testing
- Write unit tests with `pytest`
- Use mock data in `/tests/data`
- Aim for coverage on critical functions

## Documentation
- Update README with new features
- Add docstrings to all public functions
- Keep CHANGELOG.md for version history

## Deployment
- Streamlit Cloud auto-deploys on merge to `main`
- All secrets managed via Streamlit Cloud secrets manager
```

---

✅ Following this plan ensures a maintainable, testable, and deployable Streamlit app with best practices embedded via GitHub and the `CLAUDE.md`.
