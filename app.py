"""
Streamlit app for comparing EPL team performance between seasons.
"""

import streamlit as st


def main():
    """Main Streamlit application."""
    st.title("Premier League Points Comparison")
    st.write("🚧 **Under Development** 🚧")
    st.write(
        "This app will compare EPL team performance between the 2025/26 and 2024/25 seasons."
    )

    # Placeholder content for health check
    st.sidebar.header("Team Selection")
    st.sidebar.selectbox(
        "Choose Team", ["All Teams", "Arsenal", "Chelsea", "Liverpool"]
    )

    st.subheader("Coming Soon:")
    st.write("- 📊 Season-to-season performance comparison")
    st.write("- 🔄 Fixture mapping with promoted/relegated teams")
    st.write("- 📈 Interactive charts and visualizations")


if __name__ == "__main__":
    main()
