"""
Tests for data_fetcher module.
"""

import sys
import os

# Add src to path for imports - must be before other imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest  # noqa: E402
import pandas as pd  # noqa: E402
from unittest.mock import Mock, patch  # noqa: E402
from pathlib import Path  # noqa: E402
from data_fetcher import FootballDataAPI, get_fixtures, get_results  # noqa: E402


class TestFootballDataAPI:
    """Test cases for FootballDataAPI class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.api = FootballDataAPI(api_key="test_key")

    def test_init_with_api_key(self):
        """Test initialization with API key (always None in offline mode)."""
        api = FootballDataAPI(api_key="test_key")
        assert api.api_key is None  # Always None in offline mode
        assert api.session is None  # No session in offline mode

    def test_init_from_environment(self):
        """Test initialization from environment variable (always None in offline mode)."""
        with patch.dict(os.environ, {"FOOTBALL_DATA_API_KEY": "env_key"}):
            api = FootballDataAPI()
            assert api.api_key is None  # Always None in offline mode

    def test_get_season_string(self):
        """Test season string conversion."""
        assert self.api._get_season_string(2025) == "2025"
        assert self.api._get_season_string(2024) == "2024"

    def test_calculate_points_home_win(self):
        """Test points calculation for home team win."""
        row = pd.Series({"home_score": 3, "away_score": 1})
        assert self.api._calculate_points(row, "home") == 3
        assert self.api._calculate_points(row, "away") == 0

    def test_calculate_points_away_win(self):
        """Test points calculation for away team win."""
        row = pd.Series({"home_score": 1, "away_score": 3})
        assert self.api._calculate_points(row, "home") == 0
        assert self.api._calculate_points(row, "away") == 3

    def test_calculate_points_draw(self):
        """Test points calculation for draw."""
        row = pd.Series({"home_score": 2, "away_score": 2})
        assert self.api._calculate_points(row, "home") == 1
        assert self.api._calculate_points(row, "away") == 1

    def test_calculate_points_no_score(self):
        """Test points calculation with missing scores."""
        row = pd.Series({"home_score": None, "away_score": None})
        assert self.api._calculate_points(row, "home") == 0
        assert self.api._calculate_points(row, "away") == 0

    def test_make_request_offline_mode(self):
        """Test that API requests are disabled in offline mode."""
        with pytest.raises(RuntimeError, match="API requests disabled"):
            self.api._make_request("/test")

    def test_make_request_failure_offline_mode(self):
        """Test that API requests always fail in offline mode."""
        with pytest.raises(RuntimeError, match="API requests disabled"):
            self.api._make_request("/test")

    def test_get_fixtures_offline_mode_missing_file(self):
        """Test getting fixtures in offline mode with missing file."""
        # Ensure no cache file exists
        cache_file = Path("data/fixtures_2025.csv")
        if cache_file.exists():
            cache_file.unlink()

        with pytest.raises(
            FileNotFoundError, match="CRITICAL: Missing fixture data file"
        ):
            self.api.get_fixtures(2025)

    def test_get_fixtures_from_cache(self, tmp_path):
        """Test getting fixtures from cache."""
        # Create a temporary cache file with sufficient data (100+ rows)
        teams = ["Arsenal", "Chelsea", "Liverpool", "Man City", "Man United"]
        cache_data = pd.DataFrame(
            {
                "id": list(range(1, 151)),  # 150 fixtures
                "home_team": [teams[i % len(teams)] for i in range(150)],
                "away_team": [teams[(i + 1) % len(teams)] for i in range(150)],
                "season": [2025] * 150,
            }
        )

        # Temporarily change data directory
        original_data_dir = self.api.data_dir
        self.api.data_dir = tmp_path
        cache_file = tmp_path / "fixtures_2025.csv"
        cache_data.to_csv(cache_file, index=False)

        result = self.api.get_fixtures(2025)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 150
        assert result.iloc[0]["home_team"] == "Arsenal"

        # Restore original data directory
        self.api.data_dir = original_data_dir

    def test_get_results_filters_finished(self):
        """Test that get_results only returns finished matches."""
        # Mock get_fixtures to return mix of finished and scheduled
        fixtures_data = pd.DataFrame(
            {
                "id": [1, 2],
                "status": ["FINISHED", "SCHEDULED"],
                "home_team": ["Arsenal", "Liverpool"],
                "away_team": ["Chelsea", "Man City"],
                "home_score": [2, None],
                "away_score": [1, None],
                "season": [2025, 2025],
            }
        )

        with patch.object(self.api, "get_fixtures", return_value=fixtures_data):
            results = self.api.get_results(2025)

        assert len(results) == 1
        assert results.iloc[0]["status"] == "FINISHED"
        assert "home_points" in results.columns
        assert "away_points" in results.columns


class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch("data_fetcher.FootballDataAPI")
    def test_get_fixtures_function(self, mock_api_class):
        """Test get_fixtures convenience function."""
        mock_api = Mock()
        mock_api.get_fixtures.return_value = pd.DataFrame()
        mock_api_class.return_value = mock_api

        get_fixtures(2025, "test_key")

        mock_api_class.assert_called_once_with(None)  # Always None in offline mode
        mock_api.get_fixtures.assert_called_once_with(2025)

    @patch("data_fetcher.FootballDataAPI")
    def test_get_results_function(self, mock_api_class):
        """Test get_results convenience function."""
        mock_api = Mock()
        mock_api.get_results.return_value = pd.DataFrame()
        mock_api_class.return_value = mock_api

        get_results(2025, "test_key")

        mock_api_class.assert_called_once_with(None)  # Always None in offline mode
        mock_api.get_results.assert_called_once_with(2025)
