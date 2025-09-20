# Premier League Points Comparison

A Streamlit application that compares EPL team performance between the 2025/26 season (current) and the 2024/25 season (previous) using fixture mapping.

## Features

- Compare team performance across seasons using identical fixture mappings
- Handle promoted/relegated teams with Championship standings mapping
- Interactive Streamlit UI with team filtering and conditional formatting
- Cached data fetching to respect API rate limits

## Setup

### Prerequisites

- Python 3.11+
- Poetry

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd prem-points
```

2. Install dependencies:
```bash
poetry install
```

3. Activate the virtual environment:
```bash
poetry shell
```

## Usage

### Run the Application

```bash
poetry run streamlit run app.py
```

### Development Commands

```bash
# Run tests
poetry run pytest

# Lint code
poetry run ruff check . && poetry run black --check .

# Format code
poetry run black .
```

## Data Source

- **API**: [Football-Data.org](https://www.football-data.org/) free tier
- **Coverage**: EPL fixtures and results for 2024/25 and 2025/26 seasons
- **Caching**: Responses cached as CSV in `/data/` directory

## Project Structure

```
prem-points/
├── src/
│   ├── data_fetcher.py      # API integration and data fetching
│   ├── fixture_mapper.py    # Season-to-season fixture mapping
│   └── comparison.py        # Performance comparison logic
├── tests/                   # Test suite
├── data/                    # Cached API responses
├── app.py                   # Streamlit application
└── pyproject.toml          # Poetry configuration
```

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and ensure tests pass: `poetry run pytest`
3. Lint and format code: `poetry run ruff check . && poetry run black .`
4. Submit a pull request

## License

MIT License