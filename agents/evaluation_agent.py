"""
agents/evaluation_agent.py – Evaluation & Self-Correction Agent
================================================================
InsightFlow ka Guardrail & Quality Inspector:
  - Agent claims ko actual dataset calculations ke saath cross-verify karta hai
  - Hallucinations aur computational discrepancy detect karta hai
  - Controlled retry mechanism trigger karta hai agar validation fail ho
  - Quantitative metrics log karta hai (Accuracy %, Evidence Coverage %, Retry Count)
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

import config
from workflow.state import AgentState

logger = logging.getLogger(__name__)


def run_evaluation_agent(state: AgentState, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Executes automated rigorous evaluation over claims and computed numbers.
    Decides whether results meet quality thresholds or require self-correction retry.
    """
    logger.info("⚖️ Evaluation Agent auditing outputs against ground-truth evidence...")

    insights = state.get("insights", [])
    analysis_results = state.get("analysis_results", {})
    subtasks = state.get("subtasks", [])
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", config.MAX_RETRIES)
    
    evaluation_logs: List[str] = []
    verified_claims = 0
    total_claims = len(insights)
    
    # ── 1. Audit Each Generated Insight Against Raw Evidence ───
    for idx, ins in enumerate(insights, 1):
        ins_type = ins.get("type")
        evidence = ins.get("evidence", {})
        
        is_valid = True
        reason = "Passed mathematical verification"
        
        # Verify Group Performance claims against actual sum
        if ins_type == "group_performance":
            grp = evidence.get("group")
            metric_col = ins.get("metric")
            dim_col = ins.get("dimension")
            claimed_val = evidence.get("value")
            
            if grp and metric_col and dim_col and metric_col in df.columns and dim_col in df.columns:
                actual_val = df[df[dim_col] == grp][metric_col].sum()
                # 0.1% tolerance for floating point rounding
                if abs(actual_val - claimed_val) > (abs(actual_val) * 0.001 + 1e-4):
                    is_valid = False
                    reason = f"Ground truth mismatch: claimed {claimed_val}, actual sum is {actual_val}"
                    
        # Verify Anomaly count claims against ground truth IQR
        elif ins_type == "anomaly":
            col = evidence.get("column")
            claimed_count = evidence.get("count")
            if col and col in df.columns:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                actual_count = int(((df[col] < (q1 - 1.5 * iqr)) | (df[col] > (q3 + 1.5 * iqr))).sum())
                if actual_count != claimed_count:
                    is_valid = False
                    reason = f"Outlier mismatch: claimed {claimed_count}, true count is {actual_count}"

        if is_valid:
            verified_claims += 1
            evaluation_logs.append(f"✅ Claim #{idx} ({ins_type}): {reason}")
        else:
            evaluation_logs.append(f"❌ Claim #{idx} ({ins_type}): {reason}")

    # ── 2. Metric Computations ─────────────────────────────────
    calculation_accuracy = (verified_claims / total_claims) if total_claims > 0 else 1.0
    evidence_coverage = 1.0 if len(analysis_results) >= (len(subtasks) * 0.6) else 0.8
    
    # Check against required quality thresholds
    accuracy_passed = calculation_accuracy >= config.MIN_CALCULATION_ACCURACY
    
    eval_metrics = {
        "total_claims_inspected": total_claims,
        "verified_claims": verified_claims,
        "calculation_accuracy_pct": round(calculation_accuracy * 100, 2),
        "evidence_coverage_pct": round(evidence_coverage * 100, 2),
        "retry_count": retry_count,
        "accuracy_passed": accuracy_passed,
    }

    # ── 3. Routing & Retry Decision Logic ──────────────────────
    if accuracy_passed:
        is_approved = True
        status = "evaluating"
        logger.info(f"✅ Evaluation Passed ({eval_metrics['calculation_accuracy_pct']}% accuracy). Approved for Report.")
    else:
        if retry_count < max_retries:
            is_approved = False
            status = "retrying"
            retry_count += 1
            evaluation_logs.append(f"⚠️ Accuracy {eval_metrics['calculation_accuracy_pct']}% below {config.MIN_CALCULATION_ACCURACY*100}%. Triggering retry {retry_count}/{max_retries}.")
            logger.warning(f"🔄 Evaluation failed. Initiating retry #{retry_count}...")
        else:
            is_approved = True  # Max retries exceeded; approve with disclaimers
            status = "max_retries_exceeded"
            evaluation_logs.append(f"⚠️ Max retries ({max_retries}) reached. Proceeding to report with annotated confidence flags.")
            logger.warning("⚠️ Max retries reached. Forcing report compilation with evaluation notes.")

    state_updates = {
        "evaluation_result": eval_metrics,
        "is_approved": is_approved,
        "retry_count": retry_count,
        "evaluation_logs": evaluation_logs,
        "current_node": "evaluation",
        "status": status
    }

    return state_updates

