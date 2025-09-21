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

## Season Naming Convention
- **Important**: When referencing season years (e.g., "2026 season"), this means the season ending in that year
  - "2026 season" = 2025-26 season (starts August 2025, ends May 2026)
  - "2025 season" = 2024-25 season (starts August 2024, ends May 2025)
  - This applies to ALL season references throughout the codebase and user communication

### File Naming Standards
- **Data Files**: `fixtures_YYYY.csv` where YYYY is the **ending year**
  - `fixtures_2026.csv` contains 2025-26 season data (ends May 2026)
  - `fixtures_2025.csv` contains 2024-25 season data (ends May 2025)
- **Championship Data**: `championship_standings_YYYY.csv` for season ending in YYYY
  - `championship_standings_2025.csv` contains 2024-25 Championship final table

### Code Standards
- **Season Parameters**: Always use **ending year** (e.g., `season=2025` for 2024-25 season)
- **UI Display**: Show full format to users (e.g., "2024/25" where 2025 is the ending year)
- **Documentation**: Always clarify that year references mean **ending year** of season
- **Default Seasons**: App defaults to comparing current season (2026) vs previous (2025)

### Examples
- User says "2026 season" → Code uses `season=2026` → File `fixtures_2026.csv` → UI shows "2025/26"
- User says "2025 season" → Code uses `season=2025` → File `fixtures_2025.csv` → UI shows "2024/25"

## API Usage
- Football-Data.org API for EPL data
- Cache responses as CSV in `/data/` to avoid rate limits
- Handle promoted/relegated teams:
  - Map Championship final standings to relegated EPL teams
  - 1st promoted → 18th relegated, 2nd → 19th, 3rd → 20th