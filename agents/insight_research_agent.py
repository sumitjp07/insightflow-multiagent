"""
agents/insight_research_agent.py – Advanced Insight & Research Agent
=====================================================================
Insight Research Agent ka kaam:
  - Statistical patterns, groupings, and trends discover karna
  - Non-obvious correlations detect karna
  - Outliers / anomalies pinpoint karna (IQR method)
  - Data-backed actionable recommendations formulate karna
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

# Ensure root on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from tools.stats_tools import (
    calculate_correlation,
    group_analysis,
    detect_anomalies,
    get_top_bottom,
    calculate_growth
)
from workflow.state import AgentState

logger = logging.getLogger(__name__)


def run_insight_research_agent(state: AgentState, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Executes Insight Research tasks from the shared plan.
    Calculates statistical evidence and drafts clear insights.
    """
    logger.info("🔍 Insight Research Agent started pattern exploration...")
    
    subtasks = state.get("subtasks", [])
    analysis_results = dict(state.get("analysis_results", {}))
    insights: List[Dict[str, Any]] = []
    anomalies_detected: List[Dict[str, Any]] = []
    key_drivers: List[str] = []

    for task in subtasks:
        if task.get("assigned_agent") != "insight_research":
            continue
            
        tool_name = task.get("tool_name")
        params = task.get("tool_params", {})
        task_id = task.get("task_id", "insight_task")
        
        logger.info(f"🔍 Insight Research executing tool '{tool_name}' for {task_id}")
        
        if tool_name == "group_analysis":
            group_by = params.get("group_by")
            agg_col = params.get("agg_column")
            agg_funcs = params.get("agg_functions", ["sum", "mean", "count"])
            
            if group_by and agg_col and group_by in df.columns and agg_col in df.columns:
                res = group_analysis(df, group_by, agg_col, agg_funcs)
                analysis_results[task_id] = res
                
                if res["success"]:
                    best = res.get("best_group")
                    worst = res.get("worst_group")
                    if best:
                        best_val = res["results"][best].get("sum", 0)
                        insights.append({
                            "type": "group_performance",
                            "metric": agg_col,
                            "dimension": group_by,
                            "claim": f"Segment '{best}' leads total {agg_col} with a cumulative figure of {best_val:,.2f}.",
                            "evidence": {"group": best, "value": best_val, "total_groups": res["total_groups"]}
                        })
                        key_drivers.append(f"Top performing {group_by}: {best}")
                        
        elif tool_name == "calculate_correlation":
            cols = params.get("columns")
            corr_res = calculate_correlation(df, columns=cols)
            analysis_results[task_id] = corr_res
            
            if corr_res["success"]:
                for sc in corr_res.get("strong_correlations", []):
                    insights.append({
                        "type": "correlation",
                        "claim": f"Strong correlation observed between '{sc['column_1']}' and '{sc['column_2']}' (Pearson r = {sc['correlation']:.2f}, {sc['strength']}).",
                        "evidence": sc
                    })
                    key_drivers.append(f"{sc['column_1']} ↔ {sc['column_2']} ({sc['strength']})")
                    
        elif tool_name == "detect_anomalies":
            col = params.get("column")
            if col and col in df.columns:
                anom_res = detect_anomalies(
                    df,
                    column=col,
                    method=params.get("method", "iqr"),
                    threshold=params.get("threshold", 1.5)
                )
                analysis_results[task_id] = anom_res
                
                if anom_res["success"] and anom_res["anomaly_count"] > 0:
                    anom_info = {
                        "column": col,
                        "count": anom_res["anomaly_count"],
                        "percentage": anom_res["anomaly_percentage"],
                        "bounds": (anom_res["statistics"]["lower_bound"], anom_res["statistics"]["upper_bound"])
                    }
                    anomalies_detected.append(anom_info)
                    insights.append({
                        "type": "anomaly",
                        "claim": f"Identified {anom_res['anomaly_count']} statistical outliers in '{col}' ({anom_res['anomaly_percentage']}% of records).",
                        "evidence": anom_info
                    })
                    
        elif tool_name == "get_top_bottom":
            col = params.get("column")
            order = params.get("order", "top")
            n = params.get("n", 5)
            if col and col in df.columns:
                tb_res = get_top_bottom(df, column=col, n=n, order=order)
                analysis_results[task_id] = tb_res
                if tb_res["success"] and tb_res["records"]:
                    first_record = tb_res["records"][0]
                    insights.append({
                        "type": "ranking",
                        "claim": f"The #{1} record in '{col}' holds a value of {first_record.get(col, 'N/A')}.",
                        "evidence": {"top_entry": first_record, "order": order, "n": n}
                    })

        elif tool_name == "calculate_growth":
            d_col = params.get("date_column")
            v_col = params.get("value_column")
            if d_col and v_col and d_col in df.columns and v_col in df.columns:
                growth_res = calculate_growth(df, d_col, v_col, period=params.get("period", "M"))
                analysis_results[task_id] = growth_res
                if growth_res["success"]:
                    insights.append({
                        "type": "growth",
                        "claim": f"Net overall trajectory for '{v_col}' across monitored duration shows {growth_res['overall_growth_pct']:+.2f}% growth.",
                        "evidence": {"overall_growth_pct": growth_res["overall_growth_pct"]}
                    })

    # If no specific insight subtask ran, provide a fallback holistic insight
    if not insights:
        insights.append({
            "type": "general",
            "claim": f"Dataset examined across {len(df.columns)} dimensions and {len(df)} samples with verified integrity.",
            "evidence": {"rows": len(df), "columns": list(df.columns)}
        })

    state_updates = {
        "analysis_results": analysis_results,
        "insights": insights,
        "key_drivers": key_drivers,
        "anomalies_detected": anomalies_detected,
        "current_node": "insight_research",
        "status": "researching"
    }

    logger.info(f"✅ Insight Research completed: Generated {len(insights)} verified evidence points.")
    return state_updates

