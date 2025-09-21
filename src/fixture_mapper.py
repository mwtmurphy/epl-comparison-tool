"""
Fixture mapper for matching EPL fixtures between seasons.
Handles promoted/relegated teams by mapping Championship standings.
"""

import pandas as pd
from typing import Dict, Optional
from data_fetcher import get_fixtures, get_championship_standings


class FixtureMapper:
    """Maps fixtures between different EPL seasons, handling team changes."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize in offline mode. API key parameter ignored."""
        self.api_key = None  # Force offline mode
        self._team_mappings = {}

    def map_fixtures(self, current_season: int, comparison_season: int) -> pd.DataFrame:
        """
        Map fixtures from current season to equivalent fixtures in comparison season.

        Args:
            current_season: The current season year (e.g., 2025 for 2025/26)
            comparison_season: The comparison season year (e.g., 2024 for 2024/25)

        Returns:
            DataFrame with mapped fixtures containing both seasons' data
        """
        # Get fixtures for both seasons
        current_fixtures = get_fixtures(current_season, self.api_key)
        comparison_fixtures = get_fixtures(comparison_season, self.api_key)

        # Create team mappings for promoted/relegated teams
        team_mapping = self._create_team_mapping(current_season, comparison_season)

        # Map fixtures
        mapped_fixtures = []

        for _, current_fixture in current_fixtures.iterrows():
            current_home = current_fixture["home_team"]
            current_away = current_fixture["away_team"]

            # Map teams if they were promoted/relegated
            mapped_home = team_mapping.get(current_home, current_home)
            mapped_away = team_mapping.get(current_away, current_away)

            # Find equivalent fixture in comparison season
            equivalent_fixture = self._find_equivalent_fixture(
                comparison_fixtures, mapped_home, mapped_away
            )

            # Create mapped fixture record
            mapped_record = {
                # Current season data
                "current_season": current_season,
                "current_fixture_id": current_fixture["id"],
                "current_matchday": current_fixture.get("matchday"),
                "current_home_team": current_home,
                "current_away_team": current_away,
                "current_home_score": current_fixture.get("home_score"),
                "current_away_score": current_fixture.get("away_score"),
                "current_status": current_fixture.get("status"),
                "current_date": current_fixture.get("utcDate"),
                # Comparison season data
                "comparison_season": comparison_season,
                "mapped_home_team": mapped_home,
                "mapped_away_team": mapped_away,
            }

            if equivalent_fixture is not None:
                mapped_record.update(
                    {
                        "comparison_fixture_id": equivalent_fixture["id"],
                        "comparison_matchday": equivalent_fixture.get("matchday"),
                        "comparison_home_score": equivalent_fixture.get("home_score"),
                        "comparison_away_score": equivalent_fixture.get("away_score"),
                        "comparison_status": equivalent_fixture.get("status"),
                        "comparison_date": equivalent_fixture.get("utcDate"),
                        "mapping_found": True,
                    }
                )
            else:
                mapped_record.update(
                    {
                        "comparison_fixture_id": None,
                        "comparison_matchday": None,
                        "comparison_home_score": None,
                        "comparison_away_score": None,
                        "comparison_status": None,
                        "comparison_date": None,
                        "mapping_found": False,
                    }
                )

            mapped_fixtures.append(mapped_record)

        return pd.DataFrame(mapped_fixtures)

    def _create_team_mapping(
        self, current_season: int, comparison_season: int
    ) -> Dict[str, str]:
        """
        Create mapping between promoted/relegated teams.

        Logic:
        - Identify teams that are in current season but not in comparison season (promoted)
        - Identify teams that are in comparison season but not in current season (relegated)
        - Map promoted teams to relegated teams based on Championship final standings

        Args:
            current_season: Current season year
            comparison_season: Comparison season year

        Returns:
            Dictionary mapping current season teams to comparison season teams
        """
        current_fixtures = get_fixtures(current_season, self.api_key)
        comparison_fixtures = get_fixtures(comparison_season, self.api_key)

        # Get unique teams from each season
        current_teams = set(
            list(current_fixtures["home_team"]) + list(current_fixtures["away_team"])
        )
        comparison_teams = set(
            list(comparison_fixtures["home_team"])
            + list(comparison_fixtures["away_team"])
        )

        # Find promoted and relegated teams
        promoted_teams = current_teams - comparison_teams
        relegated_teams = comparison_teams - current_teams

        print(
            f"Promoted teams in {current_season}/{current_season+1}: {promoted_teams}"
        )
        print(
            f"Relegated teams from {comparison_season}/{comparison_season+1}: {relegated_teams}"
        )

        # If no team changes, return empty mapping
        if not promoted_teams and not relegated_teams:
            return {}

        # Get Championship final standings for the season between comparison and current
        # For promoted teams in 2025/26, we need 2024/25 Championship standings
        championship_season = comparison_season
        championship_standings = get_championship_standings(
            championship_season, self.api_key
        )

        # Create mapping based on Championship positions
        team_mapping = {}

        if not championship_standings.empty and len(promoted_teams) == len(
            relegated_teams
        ):
            # Get promoted teams from Championship (top 3 positions)
            promoted_from_championship = championship_standings.head(3)

            # Sort promoted teams by their Championship position
            promoted_teams_sorted = []
            for _, row in promoted_from_championship.iterrows():
                team_name = row["team_name"]
                # Try to match Championship team names to EPL team names
                matched_team = self._match_team_name(team_name, promoted_teams)
                if matched_team:
                    promoted_teams_sorted.append((row["position"], matched_team))

            # Sort by Championship position
            promoted_teams_sorted.sort(key=lambda x: x[0])

            # Sort relegated teams (you'd typically get this from final EPL table)
            # For now, we'll sort alphabetically as a fallback
            relegated_teams_sorted = sorted(relegated_teams)

            # Map: 1st promoted -> 18th relegated, 2nd -> 19th, 3rd -> 20th
            for i, (_, promoted_team) in enumerate(promoted_teams_sorted):
                if i < len(relegated_teams_sorted):
                    relegated_team = relegated_teams_sorted[
                        -(i + 1)
                    ]  # Reverse order for relegation positions
                    team_mapping[promoted_team] = relegated_team
                    print(f"Mapping: {promoted_team} -> {relegated_team}")

        # Add any remaining teams not mapped (fallback)
        remaining_promoted = promoted_teams - set(team_mapping.keys())
        remaining_relegated = relegated_teams - set(team_mapping.values())

        for promoted, relegated in zip(
            sorted(remaining_promoted), sorted(remaining_relegated)
        ):
            team_mapping[promoted] = relegated
            print(f"Fallback mapping: {promoted} -> {relegated}")

        return team_mapping

    def _match_team_name(self, championship_name: str, epl_teams: set) -> Optional[str]:
        """
        Match Championship team name to EPL team name.

        Handles common name variations between leagues.
        """
        # Direct match
        if championship_name in epl_teams:
            return championship_name

        # Common name mappings
        name_mappings = {
            "Leicester City": "Leicester",
            "Leeds United": "Leeds",
            "Southampton FC": "Southampton",
            "Norwich City": "Norwich",
            "Watford FC": "Watford",
            "Burnley FC": "Burnley",
        }

        # Try mapped name
        mapped_name = name_mappings.get(championship_name)
        if mapped_name and mapped_name in epl_teams:
            return mapped_name

        # Try partial matching (more flexible)
        championship_lower = championship_name.lower()
        for epl_team in epl_teams:
            epl_lower = epl_team.lower()
            # Check if significant words match
            champ_words = set(championship_lower.split())
            epl_words = set(epl_lower.split())

            # If there's significant overlap in words, consider it a match
            if champ_words & epl_words:  # Any common words
                return epl_team

        return None

    def _find_equivalent_fixture(
        self, fixtures: pd.DataFrame, home_team: str, away_team: str
    ) -> Optional[pd.Series]:
        """
        Find fixture with matching home and away teams.

        Args:
            fixtures: DataFrame of fixtures to search
            home_team: Home team name
            away_team: Away team name

        Returns:
            Series with fixture data or None if not found
        """
        # Look for exact match
        match = fixtures[
            (fixtures["home_team"] == home_team) & (fixtures["away_team"] == away_team)
        ]

        if not match.empty:
            return match.iloc[0]

        # Look for reverse match (home/away swapped)
        reverse_match = fixtures[
            (fixtures["home_team"] == away_team) & (fixtures["away_team"] == home_team)
        ]

        if not reverse_match.empty:
            return reverse_match.iloc[0]

        return None

    def get_team_mapping_summary(
        self, current_season: int, comparison_season: int
    ) -> Dict:
        """Get a summary of team mappings between seasons."""
        team_mapping = self._create_team_mapping(current_season, comparison_season)

        return {
            "current_season": f"{current_season}/{current_season+1}",
            "comparison_season": f"{comparison_season}/{comparison_season+1}",
            "mappings": team_mapping,
            "promoted_teams": list(team_mapping.keys()),
            "relegated_teams": list(team_mapping.values()),
            "mapping_count": len(team_mapping),
        }


# Convenience functions
def map_fixtures_between_seasons(
    current_season: int, comparison_season: int, api_key: Optional[str] = None
) -> pd.DataFrame:
    """
    Map fixtures between two seasons.

    Args:
        current_season: Current season year (e.g., 2025)
        comparison_season: Comparison season year (e.g., 2024)
        api_key: Optional API key (ignored in offline mode)

    Returns:
        DataFrame with mapped fixtures
    """
    mapper = FixtureMapper(None)  # Force offline mode
    return mapper.map_fixtures(current_season, comparison_season)


def get_team_mappings(
    current_season: int, comparison_season: int, api_key: Optional[str] = None
) -> Dict:
    """
    Get team mappings between seasons.

    Args:
        current_season: Current season year
        comparison_season: Comparison season year
        api_key: Optional API key (ignored in offline mode)

    Returns:
        Dictionary with mapping summary
    """
    mapper = FixtureMapper(None)  # Force offline mode
    return mapper.get_team_mapping_summary(current_season, comparison_season)
