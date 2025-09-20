"""
Data fetcher for Football-Data.org API to get EPL fixtures and results.
"""

import os
import pandas as pd
import requests
from pathlib import Path
from typing import Optional
import time


class FootballDataAPI:
    """Interface to Football-Data.org API for EPL data."""

    BASE_URL = "https://api.football-data.org/v4"
    EPL_COMPETITION_ID = "PL"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from environment or parameter."""
        self.api_key = api_key or os.getenv("FOOTBALL_DATA_API_KEY")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"X-Auth-Token": self.api_key})

        # Ensure data directory exists
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

    def _make_request(self, endpoint: str) -> dict:
        """Make API request with error handling and rate limiting."""
        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = self.session.get(url)
            response.raise_for_status()

            # Basic rate limiting - free tier allows 10 requests per minute
            time.sleep(6)

            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            raise

    def _get_season_string(self, season: int) -> str:
        """Convert season year to Football-Data.org format (e.g., 2025 -> '2025')."""
        return str(season)

    def get_fixtures(self, season: int) -> pd.DataFrame:
        """
        Get EPL fixtures for a specific season.

        Args:
            season: The season year (e.g., 2025 for 2025/26 season)

        Returns:
            DataFrame with fixture data
        """
        cache_file = self.data_dir / f"fixtures_{season}.csv"

        # Return cached data if available
        if cache_file.exists():
            print(f"Loading cached fixtures for {season}/{season+1} season")
            return pd.read_csv(cache_file)

        print(f"Fetching fixtures for {season}/{season+1} season from API")

        endpoint = f"/competitions/{self.EPL_COMPETITION_ID}/matches"

        # For free tier, we can't use query parameters
        # We'll get all matches and filter if needed
        data = self._make_request(endpoint)

        fixtures = []
        for match in data.get("matches", []):
            fixture = {
                "id": match["id"],
                "matchday": match.get("matchday"),
                "utcDate": match["utcDate"],
                "status": match["status"],
                "home_team": match["homeTeam"]["name"],
                "away_team": match["awayTeam"]["name"],
                "home_team_id": match["homeTeam"]["id"],
                "away_team_id": match["awayTeam"]["id"],
                "season": season,
            }

            # Add score information if available
            score = match.get("score", {})
            if score and score.get("fullTime"):
                fixture.update(
                    {
                        "home_score": score["fullTime"].get("home"),
                        "away_score": score["fullTime"].get("away"),
                    }
                )
            else:
                fixture.update({"home_score": None, "away_score": None})

            fixtures.append(fixture)

        df = pd.DataFrame(fixtures)

        # Cache the data
        df.to_csv(cache_file, index=False)
        print(f"Cached {len(df)} fixtures to {cache_file}")

        return df

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
        Get Championship final standings for promoted team mapping.

        Args:
            season: The season year

        Returns:
            DataFrame with Championship final table
        """
        cache_file = self.data_dir / f"championship_standings_{season}.csv"

        if cache_file.exists():
            print(f"Loading cached Championship standings for {season}/{season+1}")
            return pd.read_csv(cache_file)

        print(f"Fetching Championship standings for {season}/{season+1} from API")

        # Championship competition ID
        endpoint = "/competitions/ELC/standings"

        try:
            data = self._make_request(endpoint)
            standings = []

            for table in data.get("standings", []):
                if table["type"] == "TOTAL":
                    for entry in table["table"]:
                        standing = {
                            "position": entry["position"],
                            "team_name": entry["team"]["name"],
                            "team_id": entry["team"]["id"],
                            "points": entry["points"],
                            "goal_difference": entry["goalDifference"],
                            "season": season,
                        }
                        standings.append(standing)

            df = pd.DataFrame(standings)
            df.to_csv(cache_file, index=False)
            print(f"Cached Championship standings to {cache_file}")

            return df

        except Exception as e:
            print(f"Could not fetch Championship data: {e}")
            # Return empty DataFrame with expected structure
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
    """Get EPL fixtures for a season."""
    api = FootballDataAPI(api_key)
    return api.get_fixtures(season)


def get_results(season: int, api_key: Optional[str] = None) -> pd.DataFrame:
    """Get EPL results for a season."""
    api = FootballDataAPI(api_key)
    return api.get_results(season)


def get_championship_standings(
    season: int, api_key: Optional[str] = None
) -> pd.DataFrame:
    """Get Championship final standings for a season."""
    api = FootballDataAPI(api_key)
    return api.get_championship_standings(season)
