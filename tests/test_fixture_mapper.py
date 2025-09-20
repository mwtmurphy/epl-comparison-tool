"""
Tests for fixture_mapper module.
"""

import sys
import os

# Add src to path for imports - must be before other imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pandas as pd  # noqa: E402
from unittest.mock import Mock, patch  # noqa: E402
from fixture_mapper import (  # noqa: E402
    FixtureMapper,
    map_fixtures_between_seasons,
    get_team_mappings,
)


class TestFixtureMapper:
    """Test cases for FixtureMapper class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = FixtureMapper(api_key="test_key")

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        mapper = FixtureMapper(api_key="test_key")
        assert mapper.api_key == "test_key"
        assert mapper._team_mappings == {}

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        mapper = FixtureMapper()
        assert mapper.api_key is None

    def test_match_team_name_direct_match(self):
        """Test direct team name matching."""
        epl_teams = {"Arsenal", "Chelsea", "Liverpool"}
        result = self.mapper._match_team_name("Arsenal", epl_teams)
        assert result == "Arsenal"

    def test_match_team_name_mapping(self):
        """Test team name mapping for common variations."""
        epl_teams = {"Leicester", "Southampton", "Leeds"}

        result = self.mapper._match_team_name("Leicester City", epl_teams)
        assert result == "Leicester"

        result = self.mapper._match_team_name("Southampton FC", epl_teams)
        assert result == "Southampton"

    def test_match_team_name_partial_match(self):
        """Test partial team name matching."""
        epl_teams = {"Manchester United", "Manchester City"}

        result = self.mapper._match_team_name("Man United", epl_teams)
        assert result == "Manchester United"

    def test_match_team_name_no_match(self):
        """Test when no matching team is found."""
        epl_teams = {"Arsenal", "Chelsea", "Liverpool"}
        result = self.mapper._match_team_name("Barcelona", epl_teams)
        assert result is None

    def test_find_equivalent_fixture_exact_match(self):
        """Test finding exact fixture match."""
        fixtures = pd.DataFrame(
            [
                {
                    "id": 1,
                    "home_team": "Arsenal",
                    "away_team": "Chelsea",
                    "home_score": 2,
                    "away_score": 1,
                },
                {
                    "id": 2,
                    "home_team": "Liverpool",
                    "away_team": "Man City",
                    "home_score": 1,
                    "away_score": 1,
                },
            ]
        )

        result = self.mapper._find_equivalent_fixture(fixtures, "Arsenal", "Chelsea")
        assert result is not None
        assert result["id"] == 1
        assert result["home_team"] == "Arsenal"
        assert result["away_team"] == "Chelsea"

    def test_find_equivalent_fixture_reverse_match(self):
        """Test finding fixture with home/away reversed."""
        fixtures = pd.DataFrame(
            [
                {
                    "id": 1,
                    "home_team": "Chelsea",
                    "away_team": "Arsenal",
                    "home_score": 1,
                    "away_score": 2,
                }
            ]
        )

        result = self.mapper._find_equivalent_fixture(fixtures, "Arsenal", "Chelsea")
        assert result is not None
        assert result["id"] == 1
        assert result["home_team"] == "Chelsea"
        assert result["away_team"] == "Arsenal"

    def test_find_equivalent_fixture_no_match(self):
        """Test when no matching fixture is found."""
        fixtures = pd.DataFrame(
            [
                {
                    "id": 1,
                    "home_team": "Liverpool",
                    "away_team": "Man City",
                    "home_score": 1,
                    "away_score": 1,
                }
            ]
        )

        result = self.mapper._find_equivalent_fixture(fixtures, "Arsenal", "Chelsea")
        assert result is None

    @patch("fixture_mapper.get_fixtures")
    @patch("fixture_mapper.get_championship_standings")
    def test_create_team_mapping_with_promotions(
        self, mock_championship, mock_fixtures
    ):
        """Test team mapping creation with promoted/relegated teams."""
        # Mock current season fixtures (2025/26)
        current_fixtures = pd.DataFrame(
            [
                {
                    "home_team": "Arsenal",
                    "away_team": "Leicester",
                },  # Leicester promoted
                {"home_team": "Leeds", "away_team": "Chelsea"},  # Leeds promoted
                {
                    "home_team": "Southampton",
                    "away_team": "Liverpool",
                },  # Southampton promoted
            ]
        )

        # Mock comparison season fixtures (2024/25)
        comparison_fixtures = pd.DataFrame(
            [
                {"home_team": "Arsenal", "away_team": "Burnley"},  # Burnley relegated
                {
                    "home_team": "Sheffield United",
                    "away_team": "Chelsea",
                },  # Sheffield United relegated
                {"home_team": "Luton", "away_team": "Liverpool"},  # Luton relegated
            ]
        )

        # Mock Championship standings
        championship_standings = pd.DataFrame(
            [
                {"position": 1, "team_name": "Leicester City", "points": 97},
                {"position": 2, "team_name": "Leeds United", "points": 90},
                {"position": 3, "team_name": "Southampton FC", "points": 87},
            ]
        )

        mock_fixtures.side_effect = [current_fixtures, comparison_fixtures]
        mock_championship.return_value = championship_standings

        result = self.mapper._create_team_mapping(2025, 2024)

        # Verify mappings exist
        assert len(result) == 3
        assert "Leicester" in result
        assert "Leeds" in result
        assert "Southampton" in result

    @patch("fixture_mapper.get_fixtures")
    def test_create_team_mapping_no_changes(self, mock_fixtures):
        """Test team mapping when no teams changed between seasons."""
        same_fixtures = pd.DataFrame(
            [
                {"home_team": "Arsenal", "away_team": "Chelsea"},
                {"home_team": "Liverpool", "away_team": "Man City"},
            ]
        )

        mock_fixtures.return_value = same_fixtures

        result = self.mapper._create_team_mapping(2025, 2024)
        assert result == {}

    @patch("fixture_mapper.get_fixtures")
    @patch("fixture_mapper.get_championship_standings")
    def test_map_fixtures_basic_scenario(self, mock_championship, mock_fixtures):
        """Test basic fixture mapping scenario."""
        # Current season fixtures
        current_fixtures = pd.DataFrame(
            [
                {
                    "id": 1,
                    "matchday": 1,
                    "home_team": "Arsenal",
                    "away_team": "Chelsea",
                    "home_score": 2,
                    "away_score": 1,
                    "status": "FINISHED",
                    "utcDate": "2025-08-17T15:00:00Z",
                }
            ]
        )

        # Comparison season fixtures
        comparison_fixtures = pd.DataFrame(
            [
                {
                    "id": 101,
                    "matchday": 1,
                    "home_team": "Arsenal",
                    "away_team": "Chelsea",
                    "home_score": 1,
                    "away_score": 0,
                    "status": "FINISHED",
                    "utcDate": "2024-08-17T15:00:00Z",
                }
            ]
        )

        # Mock both calls to get_fixtures (for mapping and for actual fixture retrieval)
        mock_fixtures.side_effect = [
            current_fixtures,
            comparison_fixtures,
            current_fixtures,
            comparison_fixtures,
        ]
        mock_championship.return_value = pd.DataFrame()  # No promotions

        result = self.mapper.map_fixtures(2025, 2024)

        assert len(result) == 1
        assert result.iloc[0]["current_home_team"] == "Arsenal"
        assert result.iloc[0]["current_away_team"] == "Chelsea"
        assert result.iloc[0]["comparison_fixture_id"] == 101
        assert result.iloc[0]["mapping_found"] == True  # noqa: E712

    @patch("fixture_mapper.get_fixtures")
    @patch("fixture_mapper.get_championship_standings")
    def test_map_fixtures_with_promotions(self, mock_championship, mock_fixtures):
        """Test fixture mapping with promoted teams."""
        # Current season with promoted team
        current_fixtures = pd.DataFrame(
            [
                {
                    "id": 1,
                    "matchday": 1,
                    "home_team": "Arsenal",
                    "away_team": "Leicester",  # Leicester promoted
                    "home_score": None,
                    "away_score": None,
                    "status": "SCHEDULED",
                    "utcDate": "2025-08-17T15:00:00Z",
                }
            ]
        )

        # Comparison season with relegated team
        comparison_fixtures = pd.DataFrame(
            [
                {
                    "id": 101,
                    "matchday": 1,
                    "home_team": "Arsenal",
                    "away_team": "Burnley",  # Burnley relegated
                    "home_score": 1,
                    "away_score": 2,
                    "status": "FINISHED",
                    "utcDate": "2024-08-17T15:00:00Z",
                }
            ]
        )

        # Championship standings showing Leicester was promoted
        championship_standings = pd.DataFrame(
            [{"position": 1, "team_name": "Leicester City", "points": 97}]
        )

        mock_fixtures.side_effect = [
            current_fixtures,
            comparison_fixtures,
            current_fixtures,
            comparison_fixtures,
        ]
        mock_championship.return_value = championship_standings

        result = self.mapper.map_fixtures(2025, 2024)

        assert len(result) == 1
        assert result.iloc[0]["current_away_team"] == "Leicester"
        assert (
            result.iloc[0]["mapped_away_team"] == "Burnley"
        )  # Mapped to relegated team
        assert result.iloc[0]["comparison_fixture_id"] == 101

    def test_get_team_mapping_summary(self):
        """Test team mapping summary generation."""
        with patch.object(self.mapper, "_create_team_mapping") as mock_mapping:
            mock_mapping.return_value = {
                "Leicester": "Burnley",
                "Leeds": "Sheffield United",
            }

            result = self.mapper.get_team_mapping_summary(2025, 2024)

            assert result["current_season"] == "2025/2026"
            assert result["comparison_season"] == "2024/2025"
            assert result["mapping_count"] == 2
            assert "Leicester" in result["promoted_teams"]
            assert "Burnley" in result["relegated_teams"]


class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch("fixture_mapper.FixtureMapper")
    def test_map_fixtures_between_seasons(self, mock_mapper_class):
        """Test map_fixtures_between_seasons convenience function."""
        mock_mapper = Mock()
        mock_mapper.map_fixtures.return_value = pd.DataFrame()
        mock_mapper_class.return_value = mock_mapper

        map_fixtures_between_seasons(2025, 2024, "test_key")

        mock_mapper_class.assert_called_once_with("test_key")
        mock_mapper.map_fixtures.assert_called_once_with(2025, 2024)

    @patch("fixture_mapper.FixtureMapper")
    def test_get_team_mappings(self, mock_mapper_class):
        """Test get_team_mappings convenience function."""
        mock_mapper = Mock()
        mock_mapper.get_team_mapping_summary.return_value = {"mappings": {}}
        mock_mapper_class.return_value = mock_mapper

        get_team_mappings(2025, 2024, "test_key")

        mock_mapper_class.assert_called_once_with("test_key")
        mock_mapper.get_team_mapping_summary.assert_called_once_with(2025, 2024)
