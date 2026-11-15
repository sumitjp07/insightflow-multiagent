# ⚡ InsightFlow — Autonomous Multi-Agent AI Data Research & Analysis System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.53-orange.svg)](https://github.com/langchain-ai/langgraph)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.7-green.svg)](https://github.com/langchain-ai/langchain)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40.1-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: 10/10 Passing](https://img.shields.io/badge/Pytest-10%2F10%20Passing-brightgreen.svg)](https://pytest.org)

> **Autonomous Multi-Agent AI Data Research & Analysis System** that plans tasks, executes validated tools, generates evidence-backed insights, self-evaluates outputs, and produces publication-ready PDF reports.

---

## 🌟 Key Highlights

- **5 Specialized AI Agents:** Planner, Data Analyst, Insight Research, Evaluation, and Report Generator.
- **LangGraph State Machine:** Cyclic state graph with conditional self-correction retry routing.
- **Safe Tool Execution:** Closed-world predefined Python/Pandas tools — zero arbitrary code execution risks.
- **Hallucination Protection:** Evaluation Agent verifies all statistical claims against actual dataset ground truth.
- **Persistent SQLite Memory:** Tracks session metadata, agent execution trace logs, and evaluation metrics.
- **Publication-Grade PDF Reports:** Built with ReportLab including styled metrics tables, callout blocks, and findings.
- **Interactive SaaS Dashboard:** Modern Streamlit UI with file upload, preview, and interactive Plotly visualizations.

---

## 🏗️ System Architecture

```
                                  ┌────────────────────────┐
                                  │   User / Streamlit UI  │
                                  └───────────┬────────────┘
                                              │ Query & Dataset
                                              ▼
                                  ┌────────────────────────┐
                                  │    1. Planner Agent    │
                                  │   Decompose Subtasks   │
                                  └───────────┬────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │  2. Data Analyst Agent │
                                  │  Cleaning, Stats, EDA  │
                                  └───────────┬────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │3. Insight Research Agt │
                                  │ Groups, Corrs, Outliers│
                                  └───────────┬────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                 ┌───────────────►│  4. Evaluation Agent   │
                 │                │   Ground-Truth Audit   │
                 │                └───────────┬────────────┘
                 │                            │
      Retry Loop │ (<95% Accuracy)            │ (>=95% Accuracy)
  (Max 3 Retries)└────────────────────────────┤
                                              ▼
                                  ┌────────────────────────┐
                                  │5. Report Generator Agt │
                                  │ Markdown & ReportLab   │
                                  └───────────┬────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │    PDF Report & UI     │
                                  └────────────────────────┘
```

---

## 🤖 Multi-Agent Roster

| Agent | Responsibility | Capabilities |
|---|---|---|
| **🧠 Planner** | Intent parsing & task decomposition | Generates step-by-step `ExecutionPlan` with assigned agents & tools. |
| **📊 Data Analyst** | Data loading, hygiene, & summary stats | Missing value imputation, deduplication, column profiling. |
| **🔍 Insight Research** | Deep statistical pattern discovery | Group-by aggregations, Pearson correlations, 1.5× IQR outlier detection. |
| **⚖️ Evaluation** | Ground-truth mathematical auditor | Cross-verifies claims against raw data; triggers self-correction loop. |
| **📄 Report Generator** | Synthesis & export | Formats executive brief and compiles publication-quality PDF documents. |

---

## 📊 Measured Benchmark Results

All metrics are **empirically measured** using InsightFlow's automated test harness:

| Evaluation Metric | Measured Result | Benchmark Target |
|---|---|---|
| **Task Completion Rate** | **100.0%** | ≥ 90.0% |
| **Mean Calculation Accuracy** | **100.0%** | ≥ 95.0% |
| **Mean Evidence Coverage** | **93.33%** | ≥ 80.0% |
| **Mean Pipeline Latency** | **2.06s** | ≤ 10.0s |
| **Automated Pytest Coverage** | **10/10 Passed (100%)** | 100% |

---

## 🚀 Quick Start Guide

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/your-username/insightflow.git
cd insightflow

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # On Windows PowerShell
# source venv/bin/activate    # On Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
# Copy example environment configuration
cp .env.example .env
```
Edit `.env` and provide your Google Gemini API Key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```
*(Get a free key from [Google AI Studio](https://aistudio.google.com/app/apikey))*

### 3. Run Automated Tests
```bash
pytest -v
```

### 4. Launch Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 📁 Repository Structure

```
insightflow/
├── app.py                      # Main Streamlit SaaS application
├── config.py                   # Centralized configuration & constants
├── requirements.txt            # Pinned dependencies
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── README.md                   # Project documentation
│
├── agents/                     # Specialized AI Agents
│   ├── planner_agent.py        # Task decomposition & routing
│   ├── data_analyst_agent.py   # Cleaning, profiling & stats
│   ├── insight_research_agent.py # Trends, anomalies & correlations
│   ├── evaluation_agent.py     # Ground-truth mathematical audit
│   └── report_generator_agent.py# Executive report & PDF synthesis
│
├── tools/                      # Approved deterministic Python tools
│   ├── data_tools.py           # Pandas loading & cleaning
│   ├── stats_tools.py          # Statistics, IQR, correlations
│   ├── chart_tools.py          # Plotly visualization engine
│   ├── file_tools.py           # Ingestion utilities
│   └── pdf_generator.py        # ReportLab PDF compiler
│
├── workflow/                   # LangGraph Orchestration
│   ├── state.py                # Shared AgentState TypedDict
│   ├── graph.py                # StateGraph assembly & compilation
│   └── router.py               # Conditional self-correction router
│
├── memory/                     # Persistent Session Memory
│   ├── schema.sql              # SQLite schema definition
│   └── session_store.py        # SQLite history & trace manager
│
├── evaluation/                 # Automated Evaluation Harness
│   └── evaluator.py            # Accuracy & latency benchmarking
│
├── tests/                      # Pytest Test Suite
│   ├── test_data_tools.py      # Unit tests for data & stats tools
│   └── test_workflow.py        # End-to-end integration tests
│
├── sample_data/                # Built-in sample datasets
│   ├── sales_data.csv          # Multi-region retail performance data
│   └── employee_data.csv       # HR workforce analytics data
│
├── reports/                    # Generated PDF reports destination
└── docs/                       # Detailed technical documentation
    ├── architecture.md         # Deep-dive system architecture
    ├── evaluation_results.md   # Empirically measured benchmarks
    └── interview_prep.md       # Q&A for Agent Engineer interviews
```

---

## 🛡️ Security & Reliability

- **No Remote Code Execution:** Agents operate strictly within validated tool interfaces with parameter boundaries.
- **Fail-Safe Offline Mode:** If external LLM API experiences network timeout, system seamlessly deploys deterministic fallback planning without crashing.
- **Auditable Quality Thresholds:** Strict mathematical verification ensures hallucinated calculations never reach production reports.

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
