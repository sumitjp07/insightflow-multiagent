"""
workflow/state.py – Shared Multi-Agent State Definition
=========================================================
LangGraph workflow ke liye central 'AgentState' TypedDict.
Har Agent is state notebook se data padhta hai aur naye insights/outputs write karta hai.
"""

from typing import TypedDict, List, Dict, Any, Optional
import pandas as pd


class AgentState(TypedDict, total=False):
    # ── User & Dataset Inputs ──────────────────────────────
    user_query: str
    file_path: Optional[str]
    dataset_info: Dict[str, Any]
    
    # ── Planning & Task Orchestration ──────────────────────
    plan: Optional[Dict[str, Any]]               # Serialized ExecutionPlan
    subtasks: List[Dict[str, Any]]              # Ordered list of SubTasks
    current_task_idx: int                       # Current running step
    
    # ── Execution Outputs ──────────────────────────────────
    data_summary: Dict[str, Any]                # Summary from Data Analyst
    cleaning_log: List[str]                     # Changes made during cleaning
    analysis_results: Dict[str, Any]            # Intermediate tool calculations
    
    # ── Insights & Research ────────────────────────────────
    insights: List[Dict[str, Any]]              # Evidence-backed findings
    key_drivers: List[str]                      # Core drivers identified
    anomalies_detected: List[Dict[str, Any]]    # Outliers found
    
    # ── Evaluation & Self-Correction ───────────────────────
    evaluation_result: Dict[str, Any]           # Accuracy score, evidence coverage
    is_approved: bool                           # True if verified, False if retry needed
    retry_count: int                            # Number of retries triggered
    max_retries: int                            # Maximum allowed retries (from config)
    evaluation_logs: List[str]                  # Audit trail of evaluator
    
    # ── Final Synthesis & Deliverables ─────────────────────
    final_report_md: str                        # Formatted Markdown executive brief
    charts_metadata: List[Dict[str, Any]]       # Chart configs to render in UI
    
    # ── Workflow Control & Telemetry ───────────────────────
    current_node: str                           # Active node: planner, analyst, etc.
    status: str                                 # running | completed | failed | max_retries_exceeded
    execution_time_seconds: float               # Total duration
    error_message: Optional[str]

