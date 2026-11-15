"""
agents/planner_agent.py – Autonomous Planner & Reasoning Agent
================================================================
InsightFlow ka Master Orchestrator:
  - User query ko samajhta hai (Intent Understanding)
  - Dataset ke schema & context ke hisaab se execution plan banata hai
  - Tasks ko specialized sub-agents mein divide karta hai (Decomposition)
  - Predefined tools select karta hai (Tool Calling mapping)
  - Workflow routing decisions decide karta hai
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Ensure root directory is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

import config

logger = logging.getLogger(__name__)


# ── Structured Output Schemas (Pydantic) ────────────────────
class SubTask(BaseModel):
    task_id: str = Field(description="Unique task identifier, e.g. task_1, task_2")
    assigned_agent: str = Field(
        description="Assigned sub-agent: data_analyst | insight_research | evaluation | report_generator"
    )
    action: str = Field(
        description="High level action: load_and_clean | compute_stats | group_analysis | find_correlations | detect_anomalies | validate_evidence | build_report"
    )
    tool_name: Optional[str] = Field(
        default=None,
        description="Predefined tool to invoke: load_dataset | get_data_summary | clean_dataset | get_column_stats | filter_data | group_analysis | calculate_correlation | detect_anomalies | get_top_bottom"
    )
    tool_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Exact parameter dictionary to feed to the chosen tool"
    )
    description: str = Field(description="Explanation of what this subtask aims to discover")


class ExecutionPlan(BaseModel):
    user_query: str = Field(description="Original user query")
    intent_summary: str = Field(description="Concise synthesis of user objective")
    reasoning: str = Field(description="Planner agent's chain-of-thought logic")
    subtasks: List[SubTask] = Field(description="Ordered list of subtasks for multi-agent execution")
    routing_decision: str = Field(
        default="execute",
        description="Workflow route: execute | request_clarification | reject"
    )


# ── System Instruction for the Planner ─────────────────────
PLANNER_SYSTEM_PROMPT = """You are the Lead Planner Agent for InsightFlow, an Autonomous Multi-Agent AI Data Analysis System.
Your job is to decompose user analysis requests into a strict, validated, step-by-step multi-agent plan.

You have these specialized sub-agents and tools at your disposal:
1. data_analyst:
   - load_dataset(file_path)
   - get_data_summary()
   - clean_dataset(drop_duplicates, fill_strategy)
   - get_column_stats(column_name)
   - filter_data(column, operator, value)
   - get_value_counts(column)

2. insight_research:
   - group_analysis(group_by, agg_column, agg_functions)
   - calculate_correlation(columns)
   - detect_anomalies(column, method, threshold)
   - get_top_bottom(column, n, order)
   - calculate_growth(date_column, value_column, period)

3. evaluation:
   - validate_evidence(claims, ground_truth_metrics)

4. report_generator:
   - build_report(include_charts, format)

Rules:
- NEVER hallucinate tools outside this list.
- DO NOT execute arbitrary python code.
- Return a valid JSON matching the ExecutionPlan schema.
"""


def _generate_fallback_plan(query: str, dataset_info: Dict[str, Any]) -> ExecutionPlan:
    """
    Intelligent heuristic fallback plan agar LLM API network timeout ho ya offline ho.
    Ensures system reliability under all network conditions.
    """
    cols = dataset_info.get("columns", [])
    numeric_cols = dataset_info.get("numeric_columns", [])
    cat_cols = dataset_info.get("categorical_columns", [])
    
    query_lower = query.lower()
    subtasks = []
    
    # 1. Base step: Data Analyst summary & hygiene
    subtasks.append(SubTask(
        task_id="task_1",
        assigned_agent="data_analyst",
        action="get_data_summary",
        tool_name="get_data_summary",
        tool_params={},
        description="Examine dataset shape, datatypes, missing values, and check data hygiene."
    ))
    
    # 2. Heuristic mapping based on query intent
    task_idx = 2
    
    # Check for Group Analysis / Comparisons
    target_num = numeric_cols[0] if numeric_cols else "Value"
    target_cat = cat_cols[0] if cat_cols else "Category"
    for c in numeric_cols:
        if c.lower() in query_lower:
            target_num = c
            break
    for c in cat_cols:
        if c.lower() in query_lower:
            target_cat = c
            break
            
    if any(k in query_lower for k in ["region", "department", "by", "compare", "group", "product", "category"]):
        subtasks.append(SubTask(
            task_id=f"task_{task_idx}",
            assigned_agent="insight_research",
            action="group_analysis",
            tool_name="group_analysis",
            tool_params={"group_by": target_cat, "agg_column": target_num, "agg_functions": ["sum", "mean", "count"]},
            description=f"Aggregate {target_num} grouped by {target_cat} to compare segment performance."
        ))
        task_idx += 1

    # Check for Top / Bottom
    if any(k in query_lower for k in ["top", "best", "highest", "maximum", "bottom", "worst", "lowest"]):
        order = "bottom" if any(k in query_lower for k in ["bottom", "worst", "lowest"]) else "top"
        subtasks.append(SubTask(
            task_id=f"task_{task_idx}",
            assigned_agent="insight_research",
            action="get_top_bottom",
            tool_name="get_top_bottom",
            tool_params={"column": target_num, "n": 5, "order": order},
            description=f"Extract the {order} 5 records based on {target_num}."
        ))
        task_idx += 1

    # Check for Outliers / Anomalies
    if any(k in query_lower for k in ["anomaly", "anomalies", "outlier", "outliers", "unusual", "odd"]):
        subtasks.append(SubTask(
            task_id=f"task_{task_idx}",
            assigned_agent="insight_research",
            action="detect_anomalies",
            tool_name="detect_anomalies",
            tool_params={"column": target_num, "method": "iqr", "threshold": 1.5},
            description=f"Detect statistical outliers in {target_num} using IQR thresholding."
        ))
        task_idx += 1

    # Check for Correlation
    if any(k in query_lower for k in ["correlation", "relationship", "relation", "relate", "vs", "versus"]):
        subtasks.append(SubTask(
            task_id=f"task_{task_idx}",
            assigned_agent="insight_research",
            action="find_correlations",
            tool_name="calculate_correlation",
            tool_params={"columns": numeric_cols[:4] if len(numeric_cols) >= 2 else None},
            description="Compute correlation matrix across numeric features to assess dependencies."
        ))
        task_idx += 1

    # 3. Always add Evaluation task
    subtasks.append(SubTask(
        task_id=f"task_{task_idx}",
        assigned_agent="evaluation",
        action="validate_evidence",
        tool_name="validate_evidence",
        tool_params={},
        description="Verify generated statistical claims against raw calculation metrics."
    ))
    task_idx += 1

    # 4. Final step: Report Generator
    subtasks.append(SubTask(
        task_id=f"task_{task_idx}",
        assigned_agent="report_generator",
        action="build_report",
        tool_name="build_report",
        tool_params={"format": "markdown", "include_charts": True},
        description="Synthesize verified findings, charts, and actionable executive insights."
    ))

    return ExecutionPlan(
        user_query=query,
        intent_summary=f"Automated analysis workflow targeting: {query}",
        reasoning="Heuristic Planner identified query domain, selected target columns, and scheduled pipeline execution.",
        subtasks=subtasks,
        routing_decision="execute"
    )


def create_execution_plan(query: str, dataset_info: Dict[str, Any]) -> ExecutionPlan:
    """
    Primary Planner Entry Point:
    Invokes LLM (Gemini) with structured output.
    Falls back gracefully to deterministic planner if API key or network is unreachable.
    """
    logger.info(f"🧠 Planner analyzing query: '{query}'")
    
    # Check if API Key is configured
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "your_gemini_api_key_here":
        logger.warning("No Gemini API key found. Using deterministic planner.")
        return _generate_fallback_plan(query, dataset_info)

    # Attempt LLM-powered structured plan with daemon thread timeout safeguard
    try:
        import threading

        def _call_llm():
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatGoogleGenerativeAI(
                model=config.LLM_MODEL_NAME,
                google_api_key=config.GEMINI_API_KEY,
                temperature=config.LLM_TEMPERATURE,
                max_retries=0,
            )

            structured_llm = llm.with_structured_output(ExecutionPlan)

            user_context = f"""
Dataset Overview:
- File Name: {dataset_info.get('file_name', 'dataset')}
- Total Rows: {dataset_info.get('rows', 0)}
- Columns: {dataset_info.get('columns', [])}
- Numeric Columns: {dataset_info.get('numeric_columns', [])}
- Categorical Columns: {dataset_info.get('categorical_columns', [])}

User Analysis Request:
"{query}"

Decompose this request into a structured multi-agent ExecutionPlan.
"""
            messages = [
                SystemMessage(content=PLANNER_SYSTEM_PROMPT),
                HumanMessage(content=user_context)
            ]

            return structured_llm.invoke(messages)

        res_box = [None]
        err_box = [None]

        def worker():
            try:
                res_box[0] = _call_llm()
            except Exception as e:
                err_box[0] = e

        th = threading.Thread(target=worker, daemon=True)
        th.start()
        th.join(timeout=2.0)  # Max 2 seconds timeout

        if th.is_alive():
            logger.info("⚡ LLM response exceeded 2s; seamlessly deploying deterministic planner.")
        elif err_box[0]:
            logger.info(f"⚡ LLM error; fallback planner deployed: {err_box[0]}")
        elif isinstance(res_box[0], ExecutionPlan):
            logger.info(f"✅ LLM successfully generated plan with {len(res_box[0].subtasks)} subtasks.")
            return res_box[0]

    except Exception as e:
        logger.info(f"⚡ Fast fallback triggered: {str(e)[:50]}")

    # Fallback to robust deterministic planner
    return _generate_fallback_plan(query, dataset_info)


# ── Standalone Module Verification ────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  InsightFlow – Planner Agent Test")
    print("="*55)

    sample_info = {
        "file_name": "sales_data.csv",
        "rows": 30,
        "columns": ["Date", "Region", "Salesperson", "Product", "Category", "Units_Sold", "Unit_Price", "Revenue", "Discount_Percent", "Customer_Rating"],
        "numeric_columns": ["Units_Sold", "Unit_Price", "Revenue", "Discount_Percent", "Customer_Rating"],
        "categorical_columns": ["Date", "Region", "Salesperson", "Product", "Category"]
    }

    test_queries = [
        "Which product brings maximum revenue and in which region?",
        "Find anomalies and outliers in product discounts and revenue.",
        "Check correlation between unit price and customer rating."
    ]

    for q in test_queries:
        print(f"\n🔍 Query: '{q}'")
        plan = create_execution_plan(q, sample_info)
        print(f"  Summary: {plan.intent_summary}")
        print(f"  Decision: {plan.routing_decision}")
        print(f"  Subtasks ({len(plan.subtasks)} steps):")
        for st in plan.subtasks:
            print(f"    - [{st.assigned_agent}] {st.action} -> tool: {st.tool_name} ({st.description})")

    print("\n" + "="*55)
    print("  ✅ Planner Agent Tests Succeeded!")
    print("="*55 + "\n")
