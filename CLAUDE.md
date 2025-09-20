# CLAUDE Project Guidelines

## Coding Standards
- Use Python 3.11+
- Manage dependencies with Poetry
- Follow PEP8 + run `ruff` and `black`
- Keep modules small and focused:
  - `data_fetcher.py` → external data
  - `fixture_mapper.py` → mapping logic
  - `comparison.py` → aggregation/comparison
  - `app.py` → Streamlit UI

## Commands
- **Lint**: `poetry run ruff check . && poetry run black --check .`
- **Format**: `poetry run black .`
- **Test**: `poetry run pytest`
- **Run App**: `poetry run streamlit run app.py`

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

## API Usage
- Football-Data.org API for EPL data
- Cache responses as CSV in `/data/` to avoid rate limits
- Handle promoted/relegated teams:
  - Map Championship final standings to relegated EPL teams
  - 1st promoted → 18th relegated, 2nd → 19th, 3rd → 20th