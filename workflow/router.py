"""
workflow/router.py – Conditional Routing for LangGraph
========================================================
Evaluation Agent ke verification ke basis pe workflow ka next step decide karta hai:
  - Agar calculations valid hain -> 'report_generator' node pe jao
  - Agar discrepancies hain aur retry budget bacha hai -> 'retry' (data_analyst) pe jao
  - Agar retry limit cross ho gayi -> 'report_generator' pe jao (with disclaimers)
"""

import logging
from workflow.state import AgentState

logger = logging.getLogger(__name__)


def route_after_evaluation(state: AgentState) -> str:
    """
    Evaluator ke result ke basis pe conditional edge route karta hai.
    Returns: 'report_generator' | 'retry'
    """
    is_approved = state.get("is_approved", True)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    status = state.get("status", "")

    if is_approved:
        logger.info("🔀 Router: Evaluation approved. Proceeding to 'report_generator'.")
        return "report_generator"
    
    if retry_count < max_retries and status == "retrying":
        logger.info(f"🔀 Router: Evaluation requested retry ({retry_count}/{max_retries}). Routing back to 'data_analyst'.")
        return "retry"
    
    logger.info("🔀 Router: Max retries reached. Proceeding to 'report_generator' with disclaimers.")
    return "report_generator"

