"""
tests/test_data_tools.py – Unit Tests for Data & Stats Tools
=============================================================
Pytest unit tests verifying that all data processing, cleaning,
and statistical computation tools produce verified, accurate results.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from tools.data_tools import (
    load_dataset,
    get_data_summary,
    clean_dataset,
    get_column_stats,
    filter_data,
    get_value_counts
)
from tools.stats_tools import (
    calculate_correlation,
    group_analysis,
    detect_anomalies,
    get_top_bottom,
    calculate_growth
)


@pytest.fixture
def sample_sales_df():
    """Provides the sample sales dataset as a fixture."""
    file_path = BASE_DIR / "sample_data" / "sales_data.csv"
    result = load_dataset(str(file_path))
    assert result["success"] is True
    return result["data"]


def test_load_dataset(sample_sales_df):
    """Checks dataset loads correctly with accurate row and column counts."""
    assert len(sample_sales_df) == 30
    assert "Revenue" in sample_sales_df.columns
    assert "Region" in sample_sales_df.columns


def test_get_data_summary(sample_sales_df):
    """Validates summary statistics and data shape generation."""
    res = get_data_summary(sample_sales_df)
    assert res["success"] is True
    summary = res["summary"]
    assert summary["shape"]["rows"] == 30
    assert summary["shape"]["columns"] == 10
    assert "Revenue" in summary["numeric_columns"]
    assert "Region" in summary["categorical_columns"]


def test_clean_dataset():
    """Checks deduplication and missing value imputation."""
    df_dirty = pd.DataFrame({
        "A": [1, 2, 2, None, 5],
        "B": ["x", "y", "y", "z", "w"]
    })
    # Test duplicate removal
    res = clean_dataset(df_dirty, drop_duplicates=True, fill_strategy="mean")
    assert res["success"] is True
    cleaned_df = res["data"]
    assert len(cleaned_df) == 4  # 1 duplicate dropped
    assert cleaned_df["A"].isnull().sum() == 0  # Missing imputed with mean


def test_get_column_stats(sample_sales_df):
    """Validates statistical calculations for numeric column."""
    res = get_column_stats(sample_sales_df, "Revenue")
    assert res["success"] is True
    stats = res["stats"]
    assert stats["min"] == 65000.0
    assert stats["max"] == 990000.0
    assert round(stats["mean"], 2) == 280316.67


def test_filter_data(sample_sales_df):
    """Validates safe data filtering with equality operator."""
    res = filter_data(sample_sales_df, "Region", "==", "North")
    assert res["success"] is True
    assert res["filtered_count"] == 8


def test_group_analysis(sample_sales_df):
    """Validates group by aggregation results."""
    res = group_analysis(sample_sales_df, "Region", "Revenue", ["sum", "mean", "count"])
    assert res["success"] is True
    assert res["best_group"] == "West"
    assert "North" in res["results"]
    assert res["results"]["North"]["count"] == 8.0


def test_detect_anomalies(sample_sales_df):
    """Validates IQR anomaly detection."""
    res = detect_anomalies(sample_sales_df, "Revenue")
    assert res["success"] is True
    assert "anomaly_count" in res
    assert res["statistics"]["q3"] >= res["statistics"]["q1"]


def test_get_top_bottom(sample_sales_df):
    """Validates top N and bottom N queries."""
    top_res = get_top_bottom(sample_sales_df, "Revenue", n=3, order="top")
    assert top_res["success"] is True
    assert len(top_res["records"]) == 3
    assert top_res["records"][0]["Revenue"] == 990000.0
