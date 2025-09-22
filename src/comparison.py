"""
Comparison engine for aggregating and comparing EPL team performance between seasons.
"""

import pandas as pd
from typing import Dict, List, Optional
from fixture_mapper import map_fixtures_between_seasons


class TeamPerformanceComparison:
    """Compares team performance between different EPL seasons."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize in offline mode. API key parameter ignored."""
        self.api_key = None  # Force offline mode

    def compare_seasons(
        self, current_season: int, comparison_season: int
    ) -> pd.DataFrame:
        """
        Compare team performance between two seasons using mapped fixtures.

        Args:
            current_season: Current season year (e.g., 2025 for 2025/26)
            comparison_season: Comparison season year (e.g., 2024 for 2024/25)

        Returns:
            DataFrame with team comparison data

        Raises:
            ValueError: If required data is missing or invalid
        """
        try:
            # Get mapped fixtures between seasons
            mapped_fixtures = map_fixtures_between_seasons(
                current_season, comparison_season, self.api_key
            )
        except (FileNotFoundError, ValueError) as e:
            raise ValueError(
                f"CRITICAL: Cannot perform season comparison for {current_season}/{current_season+1} vs {comparison_season}/{comparison_season+1}.\n"
                f"Data error: {str(e)}\n"
                f"The application requires complete fixture data for both seasons to function."
            ) from e

        if mapped_fixtures.empty:
            raise ValueError(
                f"CRITICAL: No mapped fixtures found for comparison between {current_season}/{current_season+1} and {comparison_season}/{comparison_season+1}.\n"
                f"This could indicate missing or incompatible data files.\n"
                f"Please ensure both seasons have complete fixture data."
            )

        # Validate mapped fixtures
        if not mapped_fixtures.empty:
            mapping_success_rate = (
                mapped_fixtures["mapping_found"].mean() * 100
                if "mapping_found" in mapped_fixtures.columns
                else 0
            )
            total_fixtures = len(mapped_fixtures)
            successful_mappings = (
                mapped_fixtures["mapping_found"].sum()
                if "mapping_found" in mapped_fixtures.columns
                else 0
            )

            print(
                f"Fixture mapping results: {successful_mappings}/{total_fixtures} fixtures mapped ({mapping_success_rate:.1f}%)"
            )

            if mapping_success_rate < 50:
                print(
                    f"⚠️  Warning: Low fixture mapping success rate ({mapping_success_rate:.1f}%)"
                )
                print(
                    "This may indicate significant team roster differences or data issues"
                )

        # Calculate team performance for each season
        current_performance = self._calculate_team_performance(
            mapped_fixtures, "current"
        )
        comparison_performance = self._calculate_team_performance(
            mapped_fixtures, "comparison"
        )

        # Validate performance calculations
        if current_performance.empty:
            print("⚠️  Warning: No current season performance data calculated")
        if comparison_performance.empty:
            print("⚠️  Warning: No comparison season performance data calculated")

        # Merge and calculate differences
        comparison_df = self._merge_and_calculate_differences(
            current_performance,
            comparison_performance,
            current_season,
            comparison_season,
        )

        return comparison_df

    def _calculate_team_performance(
        self, mapped_fixtures: pd.DataFrame, season_type: str
    ) -> pd.DataFrame:
        """
        Calculate aggregated team performance from mapped fixtures.

        Args:
            mapped_fixtures: DataFrame with mapped fixture data
            season_type: "current" or "comparison"

        Returns:
            DataFrame with team performance aggregates
        """
        if season_type == "current":
            prefix = "current"
            home_team_col = f"{prefix}_home_team"
            away_team_col = f"{prefix}_away_team"
            home_score_col = f"{prefix}_home_score"
            away_score_col = f"{prefix}_away_score"
        else:
            prefix = "comparison"
            home_team_col = f"{prefix}_home_team"
            away_team_col = f"{prefix}_away_team"
            home_score_col = f"{prefix}_home_score"
            away_score_col = f"{prefix}_away_score"

        # For comparison season, use mapped team names
        if season_type == "comparison":
            home_team_col = "mapped_home_team"
            away_team_col = "mapped_away_team"

        team_stats = []

        # Filter for fixtures where mapping was found and scores exist
        valid_fixtures = mapped_fixtures[
            (mapped_fixtures["mapping_found"] == True)  # noqa: E712
            & mapped_fixtures[home_score_col].notna()
            & mapped_fixtures[away_score_col].notna()
        ].copy()

        if valid_fixtures.empty:
            return pd.DataFrame(
                columns=[
                    "team",
                    "games_played",
                    "points",
                    "goals_for",
                    "goals_against",
                    "goal_difference",
                    "wins",
                    "draws",
                    "losses",
                ]
            )

        # Get unique teams
        home_teams = valid_fixtures[home_team_col].unique()
        away_teams = valid_fixtures[away_team_col].unique()
        all_teams = list(set(list(home_teams) + list(away_teams)))

        for team in all_teams:
            # Home fixtures
            home_fixtures = valid_fixtures[valid_fixtures[home_team_col] == team]
            # Away fixtures
            away_fixtures = valid_fixtures[valid_fixtures[away_team_col] == team]

            # Calculate home performance
            home_stats = self._calculate_fixtures_stats(
                home_fixtures, home_score_col, away_score_col, is_home=True
            )

            # Calculate away performance
            away_stats = self._calculate_fixtures_stats(
                away_fixtures, away_score_col, home_score_col, is_home=False
            )

            # Aggregate total performance
            total_stats = {
                "team": team,
                "games_played": home_stats["games"] + away_stats["games"],
                "points": home_stats["points"] + away_stats["points"],
                "goals_for": home_stats["goals_for"] + away_stats["goals_for"],
                "goals_against": home_stats["goals_against"]
                + away_stats["goals_against"],
                "wins": home_stats["wins"] + away_stats["wins"],
                "draws": home_stats["draws"] + away_stats["draws"],
                "losses": home_stats["losses"] + away_stats["losses"],
            }
            total_stats["goal_difference"] = (
                total_stats["goals_for"] - total_stats["goals_against"]
            )

            team_stats.append(total_stats)

        return pd.DataFrame(team_stats)

    def _calculate_fixtures_stats(
        self,
        fixtures: pd.DataFrame,
        team_score_col: str,
        opponent_score_col: str,
        is_home: bool,
    ) -> Dict:
        """Calculate statistics for a set of fixtures."""
        if fixtures.empty:
            return {
                "games": 0,
                "points": 0,
                "goals_for": 0,
                "goals_against": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
            }

        games = len(fixtures)
        goals_for = fixtures[team_score_col].sum()
        goals_against = fixtures[opponent_score_col].sum()

        # Calculate wins, draws, losses
        wins = len(fixtures[fixtures[team_score_col] > fixtures[opponent_score_col]])
        draws = len(fixtures[fixtures[team_score_col] == fixtures[opponent_score_col]])
        losses = len(fixtures[fixtures[team_score_col] < fixtures[opponent_score_col]])

        # Calculate points (3 for win, 1 for draw, 0 for loss)
        points = wins * 3 + draws * 1

        return {
            "games": games,
            "points": points,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "wins": wins,
            "draws": draws,
            "losses": losses,
        }

    def _merge_and_calculate_differences(
        self,
        current_performance: pd.DataFrame,
        comparison_performance: pd.DataFrame,
        current_season: int,
        comparison_season: int,
    ) -> pd.DataFrame:
        """Merge performance data and calculate differences."""
        # Merge on team name
        merged = pd.merge(
            current_performance,
            comparison_performance,
            on="team",
            how="outer",
            suffixes=(f"_{current_season}", f"_{comparison_season}"),
        )

        # Fill NaN values with 0 for teams that don't appear in both seasons
        merged = merged.fillna(0)

        # Calculate differences
        merged["points_difference"] = (
            merged[f"points_{current_season}"] - merged[f"points_{comparison_season}"]
        )
        merged["goal_difference_change"] = (
            merged[f"goal_difference_{current_season}"]
            - merged[f"goal_difference_{comparison_season}"]
        )
        merged["goals_for_difference"] = (
            merged[f"goals_for_{current_season}"]
            - merged[f"goals_for_{comparison_season}"]
        )
        merged["goals_against_difference"] = (
            merged[f"goals_against_{current_season}"]
            - merged[f"goals_against_{comparison_season}"]
        )

        # Calculate percentage changes (avoid division by zero)
        merged["points_percentage_change"] = merged.apply(
            lambda row: (
                (row["points_difference"] / row[f"points_{comparison_season}"]) * 100
                if row[f"points_{comparison_season}"] > 0
                else 0
            ),
            axis=1,
        )

        # Add improvement indicators
        merged["points_improved"] = merged["points_difference"] > 0
        merged["goal_difference_improved"] = merged["goal_difference_change"] > 0

        # Filter to only include teams that played in the current season
        # (teams with games played > 0)
        current_games_played = (
            merged[f"wins_{current_season}"] +
            merged[f"draws_{current_season}"] +
            merged[f"losses_{current_season}"]
        )
        merged = merged[current_games_played > 0].copy()

        # Sort by current season points (highest first) to calculate league position
        merged = merged.sort_values(f"points_{current_season}", ascending=False)

        # Add league position (1st, 2nd, 3rd, etc.)
        merged = merged.reset_index(drop=True)
        merged["league_position"] = range(1, len(merged) + 1)

        # Restructure columns to match requested format
        display_df = pd.DataFrame()
        display_df["League position"] = merged["league_position"]
        display_df["Team name"] = merged["team"]
        display_df["Won"] = merged[f"wins_{current_season}"].astype(int)
        display_df["Draw"] = merged[f"draws_{current_season}"].astype(int)
        display_df["Lost"] = merged[f"losses_{current_season}"].astype(int)
        display_df["Goals for"] = merged[f"goals_for_{current_season}"].astype(int)
        display_df["Goals against"] = merged[f"goals_against_{current_season}"].astype(int)
        display_df["Goal difference"] = merged[f"goal_difference_{current_season}"].astype(int)
        display_df["Points"] = merged[f"points_{current_season}"].astype(int)
        display_df["Previous won"] = merged[f"wins_{comparison_season}"].astype(int)
        display_df["Previous draw"] = merged[f"draws_{comparison_season}"].astype(int)
        display_df["Previous lost"] = merged[f"losses_{comparison_season}"].astype(int)
        display_df["Previous goals for"] = merged[f"goals_for_{comparison_season}"].astype(int)
        display_df["Previous goals against"] = merged[f"goals_against_{comparison_season}"].astype(int)
        display_df["Previous goal difference"] = merged[f"goal_difference_{comparison_season}"].astype(int)
        display_df["Previous points"] = merged[f"points_{comparison_season}"].astype(int)
        display_df["Current vs previous points difference"] = merged["points_difference"].astype(int)

        # Keep internal columns for charts and other functionality (prefixed with _)
        display_df["_points_improved"] = merged["points_improved"]
        display_df["_goal_difference_improved"] = merged["goal_difference_improved"]
        display_df["_points_percentage_change"] = merged["points_percentage_change"]
        display_df["_goal_difference_change"] = merged["goal_difference_change"]
        display_df["_goals_for_difference"] = merged["goals_for_difference"]
        display_df["_goals_against_difference"] = merged["goals_against_difference"]

        return display_df

    def get_team_comparison(
        self, team_name: str, current_season: int, comparison_season: int
    ) -> Dict:
        """
        Get detailed comparison for a specific team.

        Args:
            team_name: Name of the team to compare
            current_season: Current season year
            comparison_season: Comparison season year

        Returns:
            Dictionary with detailed team comparison
        """
        comparison_df = self.compare_seasons(current_season, comparison_season)

        team_data = comparison_df[comparison_df["Team name"] == team_name]

        if team_data.empty:
            return {"error": f"Team '{team_name}' not found in comparison data"}

        team_row = team_data.iloc[0]

        return {
            "team": team_name,
            "seasons": {
                "current": f"{current_season}/{current_season+1}",
                "comparison": f"{comparison_season}/{comparison_season+1}",
            },
            "current_season": {
                "games_played": int(team_row["Won"] + team_row["Draw"] + team_row["Lost"]),
                "points": int(team_row["Points"]),
                "wins": int(team_row["Won"]),
                "draws": int(team_row["Draw"]),
                "losses": int(team_row["Lost"]),
                "goals_for": int(team_row["Goals for"]),
                "goals_against": int(team_row["Goals against"]),
                "goal_difference": int(team_row["Goal difference"]),
            },
            "comparison_season": {
                "games_played": int(team_row["Previous won"] + team_row["Previous draw"] + team_row["Previous lost"]),
                "points": int(team_row["Previous points"]),
                "wins": int(team_row["Previous won"]),
                "draws": int(team_row["Previous draw"]),
                "losses": int(team_row["Previous lost"]),
                "goals_for": int(team_row["Previous goals for"]),
                "goals_against": int(team_row["Previous goals against"]),
                "goal_difference": int(team_row["Previous goal difference"]),
            },
            "differences": {
                "points": int(team_row["Current vs previous points difference"]),
                "goal_difference": int(team_row["_goal_difference_change"]),
                "goals_for": int(team_row["_goals_for_difference"]),
                "goals_against": int(team_row["_goals_against_difference"]),
                "points_percentage_change": round(
                    float(team_row["_points_percentage_change"]), 2
                ),
            },
            "improvements": {
                "points_improved": bool(team_row["_points_improved"]),
                "goal_difference_improved": bool(team_row["_goal_difference_improved"]),
            },
        }

    def get_top_improvers(
        self,
        current_season: int,
        comparison_season: int,
        metric: str = "points",
        top_n: int = 5,
    ) -> List[Dict]:
        """
        Get top improving teams by a specific metric.

        Args:
            current_season: Current season year
            comparison_season: Comparison season year
            metric: Metric to sort by ("points", "goal_difference", "goals_for")
            top_n: Number of top teams to return

        Returns:
            List of dictionaries with top improving teams
        """
        comparison_df = self.compare_seasons(current_season, comparison_season)

        if metric == "points":
            sort_col = "Current vs previous points difference"
            current_col = "Points"
            previous_col = "Previous points"
        elif metric == "goal_difference":
            sort_col = "_goal_difference_change"
            current_col = "Goal difference"
            previous_col = "Previous goal difference"
        elif metric == "goals_for":
            sort_col = "_goals_for_difference"
            current_col = "Goals for"
            previous_col = "Previous goals for"
        else:
            raise ValueError(f"Invalid metric: {metric}")

        top_teams = comparison_df.nlargest(top_n, sort_col)

        results = []
        for _, row in top_teams.iterrows():
            results.append(
                {
                    "team": row["Team name"],
                    "improvement": int(row[sort_col]),
                    "current_season_value": int(row[current_col]),
                    "comparison_season_value": int(row[previous_col]),
                }
            )

        return results


# Convenience functions
def compare_team_performance(
    current_season: int, comparison_season: int, api_key: Optional[str] = None
) -> pd.DataFrame:
    """
    Compare team performance between two seasons.

    Args:
        current_season: Current season year (e.g., 2025)
        comparison_season: Comparison season year (e.g., 2024)
        api_key: Optional API key (ignored in offline mode)

    Returns:
        DataFrame with team comparison data
    """
    comparator = TeamPerformanceComparison(None)  # Force offline mode
    return comparator.compare_seasons(current_season, comparison_season)


def get_team_performance_summary(
    team_name: str,
    current_season: int,
    comparison_season: int,
    api_key: Optional[str] = None,
) -> Dict:
    """
    Get performance summary for a specific team.

    Args:
        team_name: Name of the team
        current_season: Current season year
        comparison_season: Comparison season year
        api_key: Optional API key (ignored in offline mode)

    Returns:
        Dictionary with team performance summary
    """
    comparator = TeamPerformanceComparison(None)  # Force offline mode
    return comparator.get_team_comparison(team_name, current_season, comparison_season)
