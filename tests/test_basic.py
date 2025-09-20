"""
Basic tests to ensure CI pipeline functionality.
"""


def test_basic_math():
    """Test basic functionality."""
    assert 2 + 2 == 4


def test_imports():
    """Test that core dependencies can be imported."""
    import streamlit  # noqa: F401
    import pandas  # noqa: F401
    import requests  # noqa: F401

    assert True
