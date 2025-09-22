"""
Data fetcher for Football-Data.org API to get EPL fixtures and results.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, List


class FootballDataAPI:
    """Interface to Football-Data.org API for EPL data."""

    BASE_URL = "https://api.football-data.org/v4"
    EPL_COMPETITION_ID = "PL"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize in offline mode - API key ignored."""
        # Force offline mode - no API calls allowed
        self.api_key = None
        self.session = None
        self.offline_mode = True

        # Ensure data directory exists
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

    def _make_request(self, endpoint: str) -> dict:
        """Disabled - API requests not allowed in offline mode."""
        raise RuntimeError(
            "API requests disabled - operating in offline mode with cached data only"
        )

    def _get_season_string(self, season: int) -> str:
        """Convert season year to Football-Data.org format (e.g., 2025 -> '2025')."""
        return str(season)

    def get_fixtures(self, season: int) -> pd.DataFrame:
        """
        Get EPL fixtures for a specific season from cached data only.

        Args:
            season: The season year (e.g., 2025 for 2025/26 season)

        Returns:
            DataFrame with fixture data

        Raises:
            FileNotFoundError: If cached data file doesn't exist
            ValueError: If data file is empty or corrupt
        """
        cache_file = self.data_dir / f"fixtures_{season}.csv"

        # Check if file exists
        if not cache_file.exists():
            raise FileNotFoundError(
                f"CRITICAL: Missing fixture data file for {season}/{season+1} season.\n"
                f"Expected file: {cache_file}\n"
                f"The application cannot function without this required data file.\n"
                f"Please ensure the data file exists and contains valid EPL fixture data."
            )

        # Load and validate data
        try:
            print(f"Loading cached fixtures for {season}/{season+1} season")
            df = pd.read_csv(cache_file)

            # Validate data is not empty
            if df.empty:
                raise ValueError(
                    f"CRITICAL: Empty fixture data file for {season}/{season+1} season.\n"
                    f"File: {cache_file}\n"
                    f"The data file exists but contains no fixture records.\n"
                    f"A complete EPL season should have 380 fixtures."
                )

            # Validate minimum expected columns
            required_columns = ["id", "home_team", "away_team", "season"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(
                    f"CRITICAL: Invalid fixture data structure for {season}/{season+1} season.\n"
                    f"File: {cache_file}\n"
                    f"Missing required columns: {missing_columns}\n"
                    f"Please ensure the data file has the correct format."
                )

            # Validate record count (warn if suspiciously low)
            if len(df) < 100:
                raise ValueError(
                    f"CRITICAL: Insufficient fixture data for {season}/{season+1} season.\n"
                    f"File: {cache_file}\n"
                    f"Found only {len(df)} fixtures. A complete EPL season should have 380 fixtures.\n"
                    f"Please ensure the data file contains complete season data."
                )

            return df

        except pd.errors.EmptyDataError:
            raise ValueError(
                f"CRITICAL: Corrupted fixture data file for {season}/{season+1} season.\n"
                f"File: {cache_file}\n"
                f"The file appears to be empty or corrupted.\n"
                f"Please replace with a valid CSV file containing EPL fixture data."
            )
        except pd.errors.ParserError as e:
            raise ValueError(
                f"CRITICAL: Invalid CSV format for {season}/{season+1} season.\n"
                f"File: {cache_file}\n"
                f"Parser error: {str(e)}\n"
                f"Please ensure the file is a valid CSV with proper formatting."
            )

    def get_results(self, season: int) -> pd.DataFrame:
        """
        Get EPL results (finished matches) for a specific season.

        Args:
            season: The season year (e.g., 2025 for 2025/26 season)

        Returns:
            DataFrame with completed match results
        """
        # Get all fixtures and filter for finished matches
        fixtures = self.get_fixtures(season)

        # Filter for finished matches only
        results = fixtures[fixtures["status"] == "FINISHED"].copy()

        # Add derived columns for analysis
        results["home_points"] = results.apply(
            self._calculate_points, axis=1, team="home"
        )
        results["away_points"] = results.apply(
            self._calculate_points, axis=1, team="away"
        )
        results["goal_difference_home"] = results["home_score"] - results["away_score"]
        results["goal_difference_away"] = results["away_score"] - results["home_score"]

        return results

    def _calculate_points(self, row: pd.Series, team: str) -> int:
        """Calculate points for a team in a match."""
        if pd.isna(row["home_score"]) or pd.isna(row["away_score"]):
            return 0

        home_score = row["home_score"]
        away_score = row["away_score"]

        if team == "home":
            if home_score > away_score:
                return 3  # Win
            elif home_score == away_score:
                return 1  # Draw
            else:
                return 0  # Loss
        else:  # away team
            if away_score > home_score:
                return 3  # Win
            elif away_score == home_score:
                return 1  # Draw
            else:
                return 0  # Loss

    def get_championship_standings(self, season: int) -> pd.DataFrame:
        """
        Get Championship final standings for promoted team mapping from cached data only.

        Args:
            season: The season year

        Returns:
            DataFrame with Championship final table
        """
        cache_file = self.data_dir / f"championship_standings_{season}.csv"

        if cache_file.exists():
            print(f"Loading cached Championship standings for {season}/{season+1}")
            return pd.read_csv(cache_file)
        else:
            print(f"No cached Championship data found for {season}/{season+1}")
            # Return empty DataFrame with expected structure for graceful handling
            return pd.DataFrame(
                columns=[
                    "position",
                    "team_name",
                    "team_id",
                    "points",
                    "goal_difference",
                    "season",
                ]
            )


# Convenience functions for easy access
def get_fixtures(season: int, api_key: Optional[str] = None) -> pd.DataFrame:
    """Get EPL fixtures for a season. API key parameter ignored in offline mode."""
    api = FootballDataAPI(None)  # Always pass None for offline mode
    return api.get_fixtures(season)


def get_results(season: int, api_key: Optional[str] = None) -> pd.DataFrame:
    """Get EPL results for a season. API key parameter ignored in offline mode."""
    api = FootballDataAPI(None)  # Always pass None for offline mode
    return api.get_results(season)


def get_championship_standings(
    season: int, api_key: Optional[str] = None
) -> pd.DataFrame:
    """Get Championship final standings for a season. API key parameter ignored in offline mode."""
    api = FootballDataAPI(None)  # Always pass None for offline mode
    return api.get_championship_standings(season)


def validate_data_files(seasons: List[int]) -> dict:
    """
    Validate that required CSV files exist for the given seasons.

    Args:
        seasons: List of season years to validate

    Returns:
        Dictionary with validation results
    """
    data_dir = Path("data")
    validation_results = {
        "all_files_present": True,
        "missing_files": [],
        "available_files": [],
        "validation_details": {},
    }

    for season in seasons:
        season_validation = {
            "fixtures_file": False,
            "fixtures_path": None,
            "has_data": False,
            "record_count": 0,
        }

        fixtures_file = data_dir / f"fixtures_{season}.csv"
        season_validation["fixtures_path"] = str(fixtures_file)

        if fixtures_file.exists():
            season_validation["fixtures_file"] = True
            validation_results["available_files"].append(str(fixtures_file))

            # Check if file has data
            try:
                df = pd.read_csv(fixtures_file)
                season_validation["has_data"] = not df.empty
                season_validation["record_count"] = len(df)
            except Exception as e:
                season_validation["error"] = str(e)

        else:
            validation_results["all_files_present"] = False
            validation_results["missing_files"].append(str(fixtures_file))

        validation_results["validation_details"][f"season_{season}"] = season_validation

    return validation_results


def get_data_status() -> dict:
    """
    Get current data status for the app.

    Returns:
        Dictionary with data status information
    """
    # Check for key seasons
    key_seasons = [2025, 2026]
    validation = validate_data_files(key_seasons)

    status = {
        "offline_mode": True,
        "api_disabled": True,
        "data_validation": validation,
        "recommended_seasons": key_seasons,
        "status": "ready" if validation["all_files_present"] else "incomplete",
    }

    return status
