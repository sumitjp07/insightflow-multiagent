# 🏗️ InsightFlow – Technical Architecture Documentation

## 1. System Overview
**InsightFlow** is an autonomous, production-oriented multi-agent data research and analysis system. Unlike single-turn chatbots or direct API wrappers, InsightFlow orchestrates 5 specialized AI agents via **LangGraph** to autonomously ingest data, generate task plans, execute approved Python statistical tools, cross-verify calculations against raw ground truth, and produce downloadable executive PDF briefs.

---

## 2. Agent Roster & Responsibilities

| Agent | Responsibilities | Approved Tools |
|---|---|---|
| **🧠 Planner Agent** | Intent decomposition, schema inspection, execution planning, tool mapping | `create_execution_plan` |
| **📊 Data Analyst Agent** | Ingestion, data hygiene, deduplication, missing value imputation, descriptive statistics | `load_dataset`, `clean_dataset`, `get_data_summary`, `get_column_stats`, `filter_data`, `get_value_counts` |
| **🔍 Insight Research Agent** | Group aggregations, cross-feature correlations, IQR outlier detection, trajectory analysis | `group_analysis`, `calculate_correlation`, `detect_anomalies`, `get_top_bottom`, `calculate_growth` |
| **⚖️ Evaluation Agent** | Ground-truth mathematical audit, hallucination protection, controlled retries, telemetry | `run_evaluation_agent` |
| **📄 Report Generator Agent** | Markdown synthesis, executive summary, strategic recommendations, ReportLab PDF generation | `generate_pdf_report` |

---

## 3. Workflow & Self-Correction Architecture

```
[START]
   │
   ▼
[1. Planner Agent] ───────► Generates Subtasks & Maps Tools
   │
   ▼
[2. Data Analyst Agent] ──► Cleans & Imputes Data, Calculates Column Stats
   │
   ▼
[3. Insight Research Agent]► Groups, Correlations, IQR Anomalies
   │
   ▼
[4. Evaluation Agent] ────► Audits Claims vs Ground Truth Metrics
   │
   ├── (Accuracy < 95% & Retries < 3) ──► [Self-Correction Loop: Retry Data Analyst]
   │
   └── (Accuracy >= 95% OR Max Retries)
         │
         ▼
[5. Report Generator Agent] ──► Compiles Executive Markdown & ReportLab PDF
         │
         ▼
      [END]
```

---

## 4. State & Memory Architecture
- **Ephemeral State:** `AgentState` TypedDict passing through LangGraph state nodes.
- **Persistent Memory:** SQLite database (`memory/insightflow.db`) storing:
  - `sessions`: Session metadata, query, dataset details, status
  - `execution_logs`: Agent trace activity
  - `evaluation_metrics`: Measured calculation accuracy, coverage, and retry counts
  - `reports`: Full text of synthesized intelligence briefs
