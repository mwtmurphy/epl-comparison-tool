"""
Streamlit app for comparing EPL team performance between seasons.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st  # noqa: E402
import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402

from comparison import (  # noqa: E402
    compare_team_performance,
    get_team_performance_summary,
)
from fixture_mapper import get_team_mappings  # noqa: E402
from data_fetcher import get_data_status  # noqa: E402


def setup_page_config():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Premier League Points Comparison",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def display_header():
    """Display application header and description."""
    st.title("⚽ Premier League Points Comparison")
    st.markdown(
        """
        Compare EPL team performance between seasons using intelligent fixture mapping
        that accounts for promoted and relegated teams. Select a season to automatically
        compare against the previous season using offline data.
        """
    )


def create_sidebar() -> tuple:
    """Create sidebar controls and return selected values."""
    st.sidebar.header("🔧 Analysis Settings")

    # Season selection
    st.sidebar.subheader("Season")
    selected_season = st.sidebar.number_input(
        "Season",
        min_value=2021,
        max_value=2030,
        value=2026,
        help="Season to analyse (will compare to previous season automatically)",
    )

    # Team selection
    st.sidebar.subheader("Team Filter")
    selected_team = st.sidebar.selectbox(
        "Choose Team",
        ["All Teams"] + get_team_options(),
        help="Select a specific team or view all teams",
    )

    return (
        selected_season,
        selected_team,
    )


def get_team_options() -> list:
    """Get list of common EPL team names."""
    return [
        "Arsenal",
        "Aston Villa",
        "Brighton",
        "Burnley",
        "Chelsea",
        "Crystal Palace",
        "Everton",
        "Fulham",
        "Leeds",
        "Leicester",
        "Liverpool",
        "Manchester City",
        "Manchester United",
        "Newcastle",
        "Norwich",
        "Sheffield United",
        "Southampton",
        "Tottenham",
        "Watford",
        "West Ham",
        "Wolves",
        "Brentford",
        "Luton",
    ]


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_comparison_data(current_season: int, comparison_season: int) -> pd.DataFrame:
    """Load and cache comparison data."""
    return compare_team_performance(current_season, comparison_season, None)


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_team_mappings(current_season: int, comparison_season: int) -> dict:
    """Load and cache team mappings."""
    return get_team_mappings(current_season, comparison_season, None)


def format_comparison_table(df: pd.DataFrame) -> pd.DataFrame:
    """Format the comparison table for display."""
    if df.empty:
        return df

    # Select and rename columns for display
    display_columns = {
        "team": "Team",
        f"points_{df.columns[1].split('_')[1]}": "Current Points",
        f"points_{df.columns[2].split('_')[1]}": "Previous Points",
        "points_difference": "Points Δ",
        "points_percentage_change": "Change %",
        f"goal_difference_{df.columns[1].split('_')[1]}": "Current GD",
        f"goal_difference_{df.columns[2].split('_')[1]}": "Previous GD",
        "goal_difference_change": "GD Δ",
        f"games_played_{df.columns[1].split('_')[1]}": "Games",
    }

    # Find the actual column names
    available_cols = {}
    for key, value in display_columns.items():
        if key in df.columns:
            available_cols[key] = value
        elif (
            key.startswith("points_")
            and len(
                [c for c in df.columns if c.startswith("points_") and c.endswith("_")]
            )
            >= 2
        ):
            # Find the actual points columns
            points_cols = [
                c
                for c in df.columns
                if c.startswith("points_")
                and c != "points_difference"
                and c != "points_percentage_change"
                and c != "points_improved"
            ]
            if len(points_cols) >= 2:
                if "current" in key.lower():
                    available_cols[points_cols[0]] = value
                elif "previous" in key.lower():
                    available_cols[points_cols[1]] = value
        elif (
            key.startswith("goal_difference_")
            and len(
                [
                    c
                    for c in df.columns
                    if c.startswith("goal_difference_") and c.endswith("_")
                ]
            )
            >= 2
        ):
            # Find the actual goal difference columns
            gd_cols = [
                c
                for c in df.columns
                if c.startswith("goal_difference_")
                and c != "goal_difference_change"
                and c != "goal_difference_improved"
            ]
            if len(gd_cols) >= 2:
                if "current" in key.lower():
                    available_cols[gd_cols[0]] = value
                elif "previous" in key.lower():
                    available_cols[gd_cols[1]] = value
        elif key.startswith("games_played_"):
            games_cols = [c for c in df.columns if c.startswith("games_played_")]
            if games_cols:
                if "current" in key.lower() and len(games_cols) >= 1:
                    available_cols[games_cols[0]] = value

    # Use available columns
    if available_cols:
        df_display = df[list(available_cols.keys())].copy()
        df_display = df_display.rename(columns=available_cols)
    else:
        # Fallback to essential columns
        essential_cols = ["team", "points_difference", "goal_difference_change"]
        df_display = df[[col for col in essential_cols if col in df.columns]].copy()

    return df_display


def apply_conditional_formatting(df: pd.DataFrame) -> pd.DataFrame:
    """Apply conditional formatting to the dataframe."""

    def highlight_improvements(val):
        """Colour code improvements and declines."""
        if pd.isna(val):
            return ""

        if isinstance(val, (int, float)):
            if val > 0:
                return "background-color: #d4edda; color: #155724"  # Green
            elif val < 0:
                return "background-color: #f8d7da; color: #721c24"  # Red
            else:
                return "background-color: #e2e3e5; color: #383d41"  # Gray
        return ""

    # Apply formatting to difference columns
    styled_df = df.style

    for col in df.columns:
        if "Δ" in col or "Change" in col:
            styled_df = styled_df.applymap(highlight_improvements, subset=[col])

    return styled_df


def create_performance_charts(df: pd.DataFrame, metric: str = "points") -> dict:
    """Create performance comparison charts."""
    if df.empty:
        return {}

    charts = {}

    # Get the actual column names
    diff_col = f"{metric}_difference"
    if diff_col not in df.columns:
        return charts

    # Top improvers chart
    top_improvers = df.nlargest(10, diff_col)
    if not top_improvers.empty:
        fig_improvers = px.bar(
            top_improvers,
            x="team",
            y=diff_col,
            title=f"Top 10 {metric.title()} Improvers",
            color=diff_col,
            color_continuous_scale="RdYlGn",
            labels={diff_col: f"{metric.title()} Difference", "team": "Team"},
        )
        fig_improvers.update_layout(xaxis_tickangle=-45)
        charts["improvers"] = fig_improvers

    # Distribution chart
    fig_dist = px.histogram(
        df,
        x=diff_col,
        nbins=20,
        title=f"{metric.title()} Difference Distribution",
        labels={diff_col: f"{metric.title()} Difference", "count": "Number of Teams"},
    )
    charts["distribution"] = fig_dist

    return charts


def display_data_status():
    """Display current data status and validation information."""
    try:
        status = get_data_status()

        # Show overall status
        if status["status"] == "ready":
            st.success("✅ All required data files are available")
        else:
            st.warning("⚠️ Some data files may be missing")

        # Show data details in expander
        with st.expander("📊 Data Status Details"):
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Configuration:**")
                st.write(f"- Offline Mode: {status['offline_mode']}")
                st.write(f"- API Disabled: {status['api_disabled']}")
                st.write(f"- Status: {status['status'].title()}")

            with col2:
                st.write("**Available Seasons:**")
                validation = status["data_validation"]
                for season in status["recommended_seasons"]:
                    season_key = f"season_{season}"
                    if season_key in validation["validation_details"]:
                        details = validation["validation_details"][season_key]
                        if details["fixtures_file"] and details["has_data"]:
                            st.write(
                                f"✅ {season}/{season+1}: {details['record_count']} fixtures"
                            )
                        elif details["fixtures_file"]:
                            st.write(f"⚠️ {season}/{season+1}: File exists but empty")
                        else:
                            st.write(f"❌ {season}/{season+1}: Missing data file")

    except Exception as e:
        st.error(f"Could not load data status: {str(e)}")


def display_team_mappings(mappings: dict):
    """Display team mappings information."""
    if mappings.get("mapping_count", 0) > 0:
        st.subheader("🔄 Team Mappings")
        st.write(
            f"**{mappings['current_season']}** vs **{mappings['comparison_season']}**"
        )

        if mappings["mappings"]:
            mapping_df = pd.DataFrame(
                [
                    {"Promoted Team": promoted, "Replaced Team": relegated}
                    for promoted, relegated in mappings["mappings"].items()
                ]
            )
            st.dataframe(mapping_df, use_container_width=True)
        else:
            st.info("No team changes detected between seasons.")
    else:
        st.info("No team mappings found.")


def display_team_detail(team_name: str, current_season: int, comparison_season: int):
    """Display detailed analysis for a specific team."""
    st.subheader(f"📊 {team_name} Detailed Analysis")

    try:
        with st.spinner(f"Loading {team_name} data..."):
            team_data = get_team_performance_summary(
                team_name, current_season, comparison_season, None
            )

        if "error" in team_data:
            st.error(team_data["error"])
            return

        # Display metrics in columns
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Points",
                team_data["current_season"]["points"],
                delta=team_data["differences"]["points"],
                help=f"Previous season: {team_data['comparison_season']['points']}",
            )

        with col2:
            st.metric(
                "Goal Difference",
                team_data["current_season"]["goal_difference"],
                delta=team_data["differences"]["goal_difference"],
                help=f"Previous season: {team_data['comparison_season']['goal_difference']}",
            )

        with col3:
            st.metric(
                "Goals For",
                team_data["current_season"]["goals_for"],
                delta=team_data["differences"]["goals_for"],
                help=f"Previous season: {team_data['comparison_season']['goals_for']}",
            )

        with col4:
            st.metric(
                "Goals Against",
                team_data["current_season"]["goals_against"],
                delta=team_data["differences"]["goals_against"],
                help=f"Previous season: {team_data['comparison_season']['goals_against']}",
            )

        # Performance summary
        if team_data["differences"]["points_percentage_change"] != 0:
            change_text = (
                f"{team_data['differences']['points_percentage_change']:+.1f}%"
            )
            if team_data["improvements"]["points_improved"]:
                st.success(f"📈 {team_name} improved by {change_text} in points")
            else:
                st.error(f"📉 {team_name} declined by {change_text} in points")
        else:
            st.info(f"➡️ {team_name} maintained the same points total")

    except Exception as e:
        st.error(f"Error loading team data: {str(e)}")


def validate_required_data():
    """Validate that all required data files exist before app starts."""
    try:
        status = get_data_status()

        # Check if all required files are present
        if not status["data_validation"]["all_files_present"]:
            missing_files = status["data_validation"]["missing_files"]
            st.error("❌ **Critical Error: Missing Required Data Files**")
            st.markdown("The following required data files are missing:")
            for file in missing_files:
                st.markdown(f"- `{file}`")
            st.markdown("**The application cannot function without these files.**")
            st.stop()

        # Check if files have actual data
        validation_details = status["data_validation"]["validation_details"]
        empty_files = []

        for season_key, details in validation_details.items():
            if details["fixtures_file"] and not details["has_data"]:
                empty_files.append(details["fixtures_path"])

        if empty_files:
            st.error("❌ **Critical Error: Empty Data Files Detected**")
            st.markdown("The following data files exist but contain no data:")
            for file in empty_files:
                st.markdown(f"- `{file}`")
            st.markdown("**The application cannot function with empty data files.**")
            st.stop()

        # Additional validation: ensure minimum record count
        insufficient_files = []
        for season_key, details in validation_details.items():
            if (
                details["fixtures_file"]
                and details["has_data"]
                and details["record_count"] < 100
            ):
                insufficient_files.append(
                    (details["fixtures_path"], details["record_count"])
                )

        if insufficient_files:
            st.error("❌ **Critical Error: Insufficient Data**")
            st.markdown("The following data files don't contain enough fixture data:")
            for file, count in insufficient_files:
                st.markdown(f"- `{file}`: {count} records (minimum 100 required)")
            st.markdown("**A complete EPL season should have 380 fixtures.**")
            st.stop()

    except Exception as e:
        st.error("❌ **Critical Error: Data Validation Failed**")
        st.markdown(f"Could not validate required data files: {str(e)}")
        st.markdown("**The application cannot start without proper data validation.**")
        st.stop()


def main():
    """Main Streamlit application."""
    setup_page_config()

    # CRITICAL: Validate required data before proceeding
    validate_required_data()

    display_header()

    # Display data status
    display_data_status()

    # Create sidebar and get user inputs
    (selected_season, selected_team) = create_sidebar()

    # Calculate comparison season automatically (previous season)
    current_season = selected_season
    comparison_season = selected_season - 1

    # Validate season input
    if current_season < 2020 or current_season > 2030:
        st.error("⚠️ Please select a valid season year")
        return

    try:
        # Load data with progress indicator
        with st.spinner("Loading team performance data..."):
            comparison_df = load_comparison_data(current_season, comparison_season)

        if comparison_df.empty:
            st.warning("📭 No comparison data available for the selected seasons.")
            st.info("This could be due to:")
            st.write("- Seasons haven't started yet")
            st.write("- Missing cached data files")
            st.write("- Data processing issues")
            return

        # Display team mappings
        try:
            mappings = load_team_mappings(current_season, comparison_season)
            display_team_mappings(mappings)
        except Exception as e:
            st.warning(f"Could not load team mappings: {str(e)}")

        # Team-specific analysis
        if selected_team != "All Teams":
            display_team_detail(selected_team, current_season, comparison_season)
            st.divider()

        # Main comparison table
        st.subheader("📋 Team Performance Comparison")

        # Always show all teams (no filtering)
        display_df = comparison_df.copy()

        # Format and display table
        formatted_df = format_comparison_table(display_df)
        if not formatted_df.empty:
            styled_df = apply_conditional_formatting(formatted_df)
            st.dataframe(styled_df, use_container_width=True)

            # Summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                improvers = len(
                    display_df[display_df["points_improved"] == True]  # noqa: E712
                )
                st.metric("Teams Improved", improvers)
            with col2:
                decliners = len(
                    display_df[display_df["points_improved"] == False]  # noqa: E712
                )
                st.metric("Teams Declined", decliners)
            with col3:
                avg_change = display_df["points_difference"].mean()
                st.metric("Avg Points Change", f"{avg_change:.1f}")
        else:
            st.info("No data to display with current filters.")

        # Charts section (always shown)
        if not display_df.empty:
            st.subheader("📈 Performance Visualisations")

            chart_metric = st.selectbox(
                "Select Metric for Charts",
                ["points", "goal_difference", "goals_for"],
                format_func=lambda x: x.replace("_", " ").title(),
            )

            charts = create_performance_charts(display_df, chart_metric)

            if charts:
                col1, col2 = st.columns(2)

                if "improvers" in charts:
                    with col1:
                        st.plotly_chart(charts["improvers"], use_container_width=True)

                if "distribution" in charts:
                    with col2:
                        st.plotly_chart(
                            charts["distribution"], use_container_width=True
                        )

    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        st.info(
            "Please ensure all required data files are present in the data/ directory."
        )

        # Show debug info in expander
        with st.expander("Debug Information"):
            st.write(f"Error type: {type(e).__name__}")
            st.write(f"Error message: {str(e)}")


if __name__ == "__main__":
    main()
