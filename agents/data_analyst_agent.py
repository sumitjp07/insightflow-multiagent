"""
agents/data_analyst_agent.py – Specialized Data Analyst Agent
==============================================================
Data Analyst Agent ka kaam:
  - Dataset load & validate karna
  - Schema, data types, missing values aur duplicates detect karna
  - Safe data cleaning execute karna
  - Column level summary statistics nikalna
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd

# Ensure root on sys.path
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
from workflow.state import AgentState

logger = logging.getLogger(__name__)


def run_data_analyst_agent(state: AgentState, df: pd.DataFrame = None) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Executes Data Analyst tasks from the shared AgentState plan.
    Returns: (state_updates, current_df)
    """
    logger.info("📊 Data Analyst Agent started execution...")
    
    file_path = state.get("file_path")
    subtasks = state.get("subtasks", [])
    analysis_results = dict(state.get("analysis_results", {}))
    cleaning_log = list(state.get("cleaning_log", []))
    
    # 1. Load dataset if not passed in memory
    if df is None:
        if file_path:
            load_res = load_dataset(file_path)
            if load_res["success"]:
                df = load_res["data"]
            else:
                return {
                    "error_message": f"Data Analyst failed to load file: {load_res['message']}",
                    "status": "failed"
                }, None
        else:
            return {"error_message": "No dataset or file path provided to Data Analyst", "status": "failed"}, None

    # 2. Get initial dataset summary & hygiene audit
    summary_res = get_data_summary(df)
    data_summary = summary_res["summary"] if summary_res["success"] else {}
    
    # 3. Process subtasks assigned to data_analyst
    for task in subtasks:
        if task.get("assigned_agent") != "data_analyst":
            continue
            
        tool_name = task.get("tool_name")
        params = task.get("tool_params", {})
        task_id = task.get("task_id", "data_task")
        
        logger.info(f"📊 Data Analyst executing tool '{tool_name}' for {task_id}")
        
        if tool_name == "clean_dataset":
            clean_res = clean_dataset(
                df,
                drop_duplicates=params.get("drop_duplicates", True),
                fill_strategy=params.get("fill_strategy", "none")
            )
            if clean_res["success"]:
                df = clean_res["data"]
                cleaning_log.extend(clean_res["changes"])
                analysis_results[task_id] = clean_res["stats"]
                
        elif tool_name == "get_column_stats":
            col = params.get("column_name")
            if col:
                stats_res = get_column_stats(df, col)
                analysis_results[task_id] = stats_res
                
        elif tool_name == "filter_data":
            f_res = filter_data(
                df,
                column=params.get("column"),
                operator=params.get("operator", "=="),
                value=params.get("value")
            )
            analysis_results[task_id] = {
                "filtered_count": f_res.get("filtered_count", 0),
                "original_count": f_res.get("original_count", 0),
                "message": f_res.get("message", "")
            }
            
        elif tool_name == "get_value_counts":
            col = params.get("column")
            if col:
                vc_res = get_value_counts(df, col, top_n=params.get("top_n", 10))
                analysis_results[task_id] = vc_res
                
        elif tool_name == "get_data_summary":
            analysis_results[task_id] = data_summary

    state_updates = {
        "data_summary": data_summary,
        "cleaning_log": cleaning_log,
        "analysis_results": analysis_results,
        "current_node": "data_analyst",
        "status": "analyzing"
    }
    
    logger.info(f"✅ Data Analyst completed. Cleaned dataset has {len(df)} rows.")
    return state_updates, df
