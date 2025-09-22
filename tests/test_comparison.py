"""
Tests for comparison module.
"""

import sys
import os

# Add src to path for imports - must be before other imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pandas as pd  # noqa: E402
from unittest.mock import Mock, patch  # noqa: E402
from comparison import (  # noqa: E402
    TeamPerformanceComparison,
    compare_team_performance,
    get_team_performance_summary,
)


class TestTeamPerformanceComparison:
    """Test cases for TeamPerformanceComparison class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.comparator = TeamPerformanceComparison(api_key="test_key")

    def test_init_with_api_key(self):
        """Test initialization with API key (always None in offline mode)."""
        comparator = TeamPerformanceComparison(api_key="test_key")
        assert comparator.api_key is None  # Always None in offline mode

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        comparator = TeamPerformanceComparison()
        assert comparator.api_key is None

    def test_calculate_fixtures_stats_empty(self):
        """Test statistics calculation with empty fixtures."""
        empty_fixtures = pd.DataFrame()
        result = self.comparator._calculate_fixtures_stats(
            empty_fixtures, "home_score", "away_score", True
        )

        expected = {
            "games": 0,
            "points": 0,
            "goals_for": 0,
            "goals_against": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
        }
        assert result == expected

    def test_calculate_fixtures_stats_home_wins(self):
        """Test statistics calculation for home team wins."""
        fixtures = pd.DataFrame(
            [
                {"home_score": 3, "away_score": 1},  # Win
                {"home_score": 2, "away_score": 0},  # Win
                {"home_score": 1, "away_score": 1},  # Draw
            ]
        )

        result = self.comparator._calculate_fixtures_stats(
            fixtures, "home_score", "away_score", True
        )

        expected = {
            "games": 3,
            "points": 7,  # 2 wins (6 points) + 1 draw (1 point)
            "goals_for": 6,  # 3 + 2 + 1
            "goals_against": 2,  # 1 + 0 + 1
            "wins": 2,
            "draws": 1,
            "losses": 0,
        }
        assert result == expected

    def test_calculate_fixtures_stats_away_performance(self):
        """Test statistics calculation for away team performance."""
        fixtures = pd.DataFrame(
            [
                {"home_score": 1, "away_score": 3},  # Away win
                {"home_score": 2, "away_score": 1},  # Away loss
                {"home_score": 1, "away_score": 1},  # Draw
            ]
        )

        result = self.comparator._calculate_fixtures_stats(
            fixtures, "away_score", "home_score", False
        )

        expected = {
            "games": 3,
            "points": 4,  # 1 win (3 points) + 1 draw (1 point)
            "goals_for": 5,  # 3 + 1 + 1
            "goals_against": 4,  # 1 + 2 + 1
            "wins": 1,
            "draws": 1,
            "losses": 1,
        }
        assert result == expected

    def test_calculate_team_performance_empty_data(self):
        """Test team performance calculation with no valid fixtures."""
        empty_mapped = pd.DataFrame(
            columns=[
                "current_home_team",
                "current_away_team",
                "current_home_score",
                "current_away_score",
                "mapped_home_team",
                "mapped_away_team",
                "comparison_home_score",
                "comparison_away_score",
                "mapping_found",
            ]
        )

        result = self.comparator._calculate_team_performance(empty_mapped, "current")

        assert result.empty
        expected_columns = [
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
        assert list(result.columns) == expected_columns

    def test_calculate_team_performance_current_season(self):
        """Test team performance calculation for current season."""
        mapped_fixtures = pd.DataFrame(
            [
                {
                    "current_home_team": "Arsenal",
                    "current_away_team": "Chelsea",
                    "current_home_score": 2,
                    "current_away_score": 1,
                    "mapping_found": True,
                },
                {
                    "current_home_team": "Chelsea",
                    "current_away_team": "Liverpool",
                    "current_home_score": 1,
                    "current_away_score": 3,
                    "mapping_found": True,
                },
            ]
        )

        result = self.comparator._calculate_team_performance(mapped_fixtures, "current")

        assert len(result) == 3  # Arsenal, Chelsea, Liverpool

        # Check Arsenal (1 home win)
        arsenal = result[result["team"] == "Arsenal"].iloc[0]
        assert arsenal["games_played"] == 1
        assert arsenal["points"] == 3  # Win
        assert arsenal["goals_for"] == 2
        assert arsenal["goals_against"] == 1
        assert arsenal["goal_difference"] == 1
        assert arsenal["wins"] == 1
        assert arsenal["draws"] == 0
        assert arsenal["losses"] == 0

        # Check Chelsea (1 home loss, 1 away loss)
        chelsea = result[result["team"] == "Chelsea"].iloc[0]
        assert chelsea["games_played"] == 2
        assert chelsea["points"] == 0  # Two losses
        assert chelsea["goals_for"] == 2  # 1 + 1
        assert chelsea["goals_against"] == 5  # 2 + 3
        assert chelsea["goal_difference"] == -3

    def test_merge_and_calculate_differences(self):
        """Test merging performance data and calculating differences."""
        current_performance = pd.DataFrame(
            [
                {
                    "team": "Arsenal",
                    "games_played": 10,
                    "points": 25,
                    "goals_for": 30,
                    "goals_against": 15,
                    "goal_difference": 15,
                    "wins": 8,
                    "draws": 1,
                    "losses": 1,
                }
            ]
        )

        comparison_performance = pd.DataFrame(
            [
                {
                    "team": "Arsenal",
                    "games_played": 10,
                    "points": 20,
                    "goals_for": 25,
                    "goals_against": 20,
                    "goal_difference": 5,
                    "wins": 6,
                    "draws": 2,
                    "losses": 2,
                }
            ]
        )

        result = self.comparator._merge_and_calculate_differences(
            current_performance, comparison_performance, 2025, 2024
        )

        assert len(result) == 1
        row = result.iloc[0]

        assert row["Team name"] == "Arsenal"
        assert row["League position"] == 1  # Should be 1st by points
        assert row["Points"] == 25
        assert row["Previous points"] == 20
        assert row["Current vs previous points difference"] == 5  # 25 - 20
        assert row["Goal difference"] == 15
        assert row["Previous goal difference"] == 5
        assert row["_goal_difference_change"] == 10  # 15 - 5
        assert row["_goals_for_difference"] == 5  # 30 - 25
        assert row["_goals_against_difference"] == -5  # 15 - 20
        assert row["_points_percentage_change"] == 25.0  # (5/20) * 100
        assert row["_points_improved"] == True  # noqa: E712
        assert row["_goal_difference_improved"] == True  # noqa: E712

    def test_merge_with_missing_teams(self):
        """Test merging when teams appear in only one season - only shows Premier League teams."""
        current_performance = pd.DataFrame(
            [
                {
                    "team": "Arsenal",
                    "games_played": 10,
                    "points": 25,
                    "goals_for": 30,
                    "goals_against": 15,
                    "goal_difference": 15,
                    "wins": 8,
                    "draws": 1,
                    "losses": 1,
                }
            ]
        )

        comparison_performance = pd.DataFrame(
            [
                {
                    "team": "Burnley",
                    "games_played": 10,
                    "points": 20,
                    "goals_for": 18,
                    "goals_against": 23,
                    "goal_difference": -5,
                    "wins": 6,
                    "draws": 2,
                    "losses": 2,
                }
            ]
        )

        result = self.comparator._merge_and_calculate_differences(
            current_performance, comparison_performance, 2025, 2024
        )

        # Only shows teams that played in current season (Premier League teams)
        assert len(result) == 1  # Only Arsenal (played current season)

        # Arsenal (new team, no comparison data)
        arsenal = result[result["Team name"] == "Arsenal"].iloc[0]
        assert arsenal["Points"] == 25
        assert arsenal["Previous points"] == 0  # Filled with 0
        assert arsenal["Current vs previous points difference"] == 25

        # Burnley is not shown as it didn't play in current season (relegated)

    @patch("comparison.map_fixtures_between_seasons")
    def test_compare_seasons_integration(self, mock_map_fixtures):
        """Test full season comparison integration."""
        # Mock mapped fixtures data
        mock_mapped_fixtures = pd.DataFrame(
            [
                {
                    "current_home_team": "Arsenal",
                    "current_away_team": "Chelsea",
                    "current_home_score": 2,
                    "current_away_score": 1,
                    "mapped_home_team": "Arsenal",
                    "mapped_away_team": "Chelsea",
                    "comparison_home_score": 1,
                    "comparison_away_score": 2,
                    "mapping_found": True,
                }
            ]
        )
        mock_map_fixtures.return_value = mock_mapped_fixtures

        result = self.comparator.compare_seasons(2025, 2024)

        assert len(result) >= 2  # Arsenal and Chelsea
        assert "Current vs previous points difference" in result.columns
        assert "_goal_difference_change" in result.columns
        assert "_points_improved" in result.columns

    def test_get_team_comparison_not_found(self):
        """Test team comparison when team is not found."""
        with patch.object(self.comparator, "compare_seasons") as mock_compare:
            mock_compare.return_value = pd.DataFrame(columns=["Team name"])

            result = self.comparator.get_team_comparison("NonExistent", 2025, 2024)

            assert "error" in result
            assert "NonExistent" in result["error"]

    def test_get_team_comparison_success(self):
        """Test successful team comparison."""
        mock_comparison_data = pd.DataFrame(
            [
                {
                    "League position": 1,
                    "Team name": "Arsenal",
                    "Won": 8,
                    "Draw": 1,
                    "Lost": 1,
                    "Goals for": 30,
                    "Goals against": 15,
                    "Goal difference": 15,
                    "Points": 25,
                    "Previous won": 6,
                    "Previous draw": 2,
                    "Previous lost": 2,
                    "Previous goals for": 25,
                    "Previous goals against": 20,
                    "Previous goal difference": 5,
                    "Previous points": 20,
                    "Current vs previous points difference": 5,
                    "_goal_difference_change": 10,
                    "_goals_for_difference": 5,
                    "_goals_against_difference": -5,
                    "_points_percentage_change": 25.0,
                    "_points_improved": True,
                    "_goal_difference_improved": True,
                }
            ]
        )

        with patch.object(self.comparator, "compare_seasons") as mock_compare:
            mock_compare.return_value = mock_comparison_data

            result = self.comparator.get_team_comparison("Arsenal", 2025, 2024)

            assert result["team"] == "Arsenal"
            assert result["seasons"]["current"] == "2025/2026"
            assert result["seasons"]["comparison"] == "2024/2025"
            assert result["current_season"]["points"] == 25
            assert result["comparison_season"]["points"] == 20
            assert result["differences"]["points"] == 5
            assert result["improvements"]["points_improved"] == True  # noqa: E712

    def test_get_top_improvers(self):
        """Test getting top improving teams."""
        mock_comparison_data = pd.DataFrame(
            [
                {
                    "Team name": "Arsenal",
                    "Current vs previous points difference": 10,
                    "Points": 30,
                    "Previous points": 20,
                },
                {
                    "Team name": "Chelsea",
                    "Current vs previous points difference": 5,
                    "Points": 25,
                    "Previous points": 20,
                },
                {
                    "Team name": "Liverpool",
                    "Current vs previous points difference": -3,
                    "Points": 17,
                    "Previous points": 20,
                },
            ]
        )

        with patch.object(self.comparator, "compare_seasons") as mock_compare:
            mock_compare.return_value = mock_comparison_data

            result = self.comparator.get_top_improvers(2025, 2024, "points", 2)

            assert len(result) == 2
            assert result[0]["team"] == "Arsenal"
            assert result[0]["improvement"] == 10
            assert result[1]["team"] == "Chelsea"
            assert result[1]["improvement"] == 5

    def test_get_top_improvers_invalid_metric(self):
        """Test error handling for invalid metric."""
        with patch.object(self.comparator, "compare_seasons"):
            try:
                self.comparator.get_top_improvers(2025, 2024, "invalid_metric")
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "Invalid metric" in str(e)


class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch("comparison.TeamPerformanceComparison")
    def test_compare_team_performance(self, mock_comparator_class):
        """Test compare_team_performance convenience function."""
        mock_comparator = Mock()
        mock_comparator.compare_seasons.return_value = pd.DataFrame()
        mock_comparator_class.return_value = mock_comparator

        compare_team_performance(2025, 2024, "test_key")

        mock_comparator_class.assert_called_once_with(
            None
        )  # Always None in offline mode
        mock_comparator.compare_seasons.assert_called_once_with(2025, 2024)

    @patch("comparison.TeamPerformanceComparison")
    def test_get_team_performance_summary(self, mock_comparator_class):
        """Test get_team_performance_summary convenience function."""
        mock_comparator = Mock()
        mock_comparator.get_team_comparison.return_value = {"team": "Arsenal"}
        mock_comparator_class.return_value = mock_comparator

        get_team_performance_summary("Arsenal", 2025, 2024, "test_key")

        mock_comparator_class.assert_called_once_with(
            None
        )  # Always None in offline mode
        mock_comparator.get_team_comparison.assert_called_once_with(
            "Arsenal", 2025, 2024
        )
