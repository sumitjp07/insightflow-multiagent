"""
tests/test_workflow.py – Integration Tests for Multi-Agent Workflow
=====================================================================
Verifies end-to-end LangGraph state transitions, evaluation approval,
and report generation across test queries.
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from workflow.graph import run_insightflow_pipeline
from tools.data_tools import load_dataset


@pytest.fixture
def sales_data():
    csv_path = BASE_DIR / "sample_data" / "sales_data.csv"
    res = load_dataset(str(csv_path))
    assert res["success"] is True
    return res["data"]


def test_pipeline_execution_success(sales_data):
    """Checks complete LangGraph execution returns approved status and report."""
    query = "Find leading region by revenue and top product."
    result = run_insightflow_pipeline(query, sales_data, file_name="sales_data.csv")

    assert result["status"] == "completed"
    assert result["current_node"] == "report_generator"
    assert "final_report_md" in result
    assert len(result["final_report_md"]) > 100
    assert result["is_approved"] is True
    assert result["evaluation_result"]["calculation_accuracy_pct"] >= 95.0


def test_pipeline_anomaly_query(sales_data):
    """Validates pipeline execution for outlier detection requests."""
    query = "Detect statistical anomalies in product revenue."
    result = run_insightflow_pipeline(query, sales_data, file_name="sales_data.csv")

    assert result["status"] == "completed"
    assert len(result["subtasks"]) >= 3
    assert "evaluation_result" in result

