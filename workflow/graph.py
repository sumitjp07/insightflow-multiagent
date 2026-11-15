"""
workflow/graph.py – LangGraph Multi-Agent Workflow Engine
===========================================================
InsightFlow ka primary execution engine:
  - 5 Specialized AI Agents ko stateful graph mein bind karta hai
  - Shared AgentState manage karta hai
  - Conditional self-correction retry loop handle karta hai
"""

import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any
import pandas as pd

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

import config
from workflow.state import AgentState
from workflow.router import route_after_evaluation
from agents.planner_agent import create_execution_plan
from agents.data_analyst_agent import run_data_analyst_agent
from agents.insight_research_agent import run_insight_research_agent
from agents.evaluation_agent import run_evaluation_agent
from agents.report_generator_agent import run_report_generator_agent
from tools.data_tools import load_dataset

from langgraph.graph import StateGraph, START, END

logger = logging.getLogger(__name__)

# In-memory dataframe cache keyed by file_path or 'active_session'
_DATAFRAME_CACHE: Dict[str, pd.DataFrame] = {}


def register_dataframe(df: pd.DataFrame, key: str = "active_session"):
    """Registers active working dataframe into cache for node access."""
    _DATAFRAME_CACHE[key] = df


def get_cached_dataframe(key: str = "active_session", file_path: str = None) -> pd.DataFrame:
    """Retrieves cached dataframe or loads from disk if missing."""
    if key in _DATAFRAME_CACHE:
        return _DATAFRAME_CACHE[key]
    if file_path:
        res = load_dataset(file_path)
        if res["success"]:
            _DATAFRAME_CACHE[key] = res["data"]
            return res["data"]
    raise ValueError("No active dataset found in memory or file_path")


# ── LangGraph Node Functions ───────────────────────────────
def planner_node(state: AgentState) -> Dict[str, Any]:
    """1. Planner Node: Intent parsing & subtask decomposition."""
    logger.info("📍 Entering [planner_node]...")
    query = state.get("user_query", "")
    info = state.get("dataset_info", {})
    
    plan = create_execution_plan(query, info)
    
    subtasks_dict = [st.model_dump() for st in plan.subtasks]
    
    return {
        "plan": plan.model_dump(),
        "subtasks": subtasks_dict,
        "current_node": "planner",
        "status": "planned"
    }


def data_analyst_node(state: AgentState) -> Dict[str, Any]:
    """2. Data Analyst Node: Data hygiene, cleaning & summary stats."""
    logger.info("📍 Entering [data_analyst_node]...")
    file_path = state.get("file_path")
    df = get_cached_dataframe("active_session", file_path)
    
    updates, updated_df = run_data_analyst_agent(state, df)
    if updated_df is not None:
        register_dataframe(updated_df, "active_session")
        
    return updates


def insight_research_node(state: AgentState) -> Dict[str, Any]:
    """3. Insight Research Node: Groupings, trends, anomalies & correlations."""
    logger.info("📍 Entering [insight_research_node]...")
    file_path = state.get("file_path")
    df = get_cached_dataframe("active_session", file_path)
    
    updates = run_insight_research_agent(state, df)
    return updates


def evaluation_node(state: AgentState) -> Dict[str, Any]:
    """4. Evaluation Node: Audits claims against calculations."""
    logger.info("📍 Entering [evaluation_node]...")
    file_path = state.get("file_path")
    df = get_cached_dataframe("active_session", file_path)
    
    updates = run_evaluation_agent(state, df)
    return updates


def report_generator_node(state: AgentState) -> Dict[str, Any]:
    """5. Report Generator Node: Formats final verified executive report."""
    logger.info("📍 Entering [report_generator_node]...")
    file_path = state.get("file_path")
    df = get_cached_dataframe("active_session", file_path)
    
    updates = run_report_generator_agent(state, df)
    return updates


# ── Graph Construction ─────────────────────────────────────
def build_multi_agent_graph() -> StateGraph:
    """
    Constructs and compiles the full LangGraph workflow.
    """
    workflow = StateGraph(AgentState)

    # 1. Register Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("data_analyst", data_analyst_node)
    workflow.add_node("insight_research", insight_research_node)
    workflow.add_node("evaluation", evaluation_node)
    workflow.add_node("report_generator", report_generator_node)

    # 2. Sequential Edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "data_analyst")
    workflow.add_edge("data_analyst", "insight_research")
    workflow.add_edge("insight_research", "evaluation")

    # 3. Conditional Self-Correction Routing from Evaluator
    workflow.add_conditional_edges(
        "evaluation",
        route_after_evaluation,
        {
            "report_generator": "report_generator",
            "retry": "data_analyst",
        }
    )

    workflow.add_edge("report_generator", END)

    app = workflow.compile()
    return app


# ── Execution Pipeline Entry Point ─────────────────────────
def run_insightflow_pipeline(query: str, df: pd.DataFrame, file_name: str = "dataset.csv") -> Dict[str, Any]:
    """
    Convenience orchestrator function to run the complete workflow.
    """
    start_time = time.time()
    
    # 1. Register working dataframe
    register_dataframe(df, "active_session")
    
    # 2. Extract dataset metadata
    info = {
        "file_name": file_name,
        "rows": len(df),
        "columns": list(df.columns),
        "numeric_columns": df.select_dtypes(include=["number"]).columns.tolist(),
        "categorical_columns": df.select_dtypes(include=["object", "category"]).columns.tolist()
    }
    
    # 3. Initialize Starting State
    initial_state: AgentState = {
        "user_query": query,
        "file_path": None,
        "dataset_info": info,
        "retry_count": 0,
        "max_retries": config.MAX_RETRIES,
        "analysis_results": {},
        "cleaning_log": [],
        "insights": [],
        "key_drivers": [],
        "anomalies_detected": [],
        "evaluation_logs": [],
        "status": "starting"
    }

    # 4. Compile & Run Graph
    compiled_app = build_multi_agent_graph()
    final_state = compiled_app.invoke(initial_state)
    
    duration = time.time() - start_time
    final_state["execution_time_seconds"] = round(duration, 2)
    logger.info(f"⚡ Pipeline execution finished in {final_state['execution_time_seconds']}s")
    
    return final_state


# ── Quick Pipeline Standalone Test ─────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  InsightFlow – End-to-End LangGraph Pipeline Test")
    print("="*55)

    test_df = pd.read_csv("sample_data/sales_data.csv")
    query = "Analyze revenue by region, find outliers, and identify top sales drivers."

    print(f"\n🚀 Running Pipeline for Query: '{query}'")
    result = run_insightflow_pipeline(query, test_df, file_name="sales_data.csv")

    print(f"\n✅ Pipeline Complete in {result.get('execution_time_seconds')}s!")
    print(f"  Final Node: {result.get('current_node')}")
    print(f"  Status: {result.get('status')}")
    print(f"  Accuracy: {result.get('evaluation_result', {}).get('calculation_accuracy_pct')}%")
    print(f"  Retries: {result.get('retry_count')}")
    print(f"  Insights Generated: {len(result.get('insights', []))}")
    
    print("\n--- Preview of Generated Final Report ---\n")
    print(result.get("final_report_md", "")[:500] + "\n...[truncated for preview]...\n")

    print("="*55)
    print("  🎉 LangGraph Multi-Agent Workflow Fully Operational!")
    print("="*55 + "\n")
