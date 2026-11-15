# 💼 InsightFlow – AI Agent Engineer Interview Preparation Q&A

Use these technical answers when interviewing for AI Agent Engineer / Applied AI Intern roles.

---

### Q1: What makes InsightFlow an AI Agent system rather than a basic LLM wrapper or Chatbot?
**Answer:**
> "A traditional chatbot or API wrapper takes a prompt and produces a single completion without external state, environment feedback, or self-correction. InsightFlow is an autonomous agent architecture built on LangGraph. It has 5 specialized agents with defined boundaries:
> 1. A **Planner** that decomposes unstructured queries into discrete tool-directed subtasks.
> 2. Specialized **Execution Agents** that call validated Python/Pandas tools rather than executing arbitrary unsafe code.
> 3. An independent **Evaluation Agent** that acts as an automated critic, recalculating mathematical statements directly against dataset ground truth to guarantee zero hallucination.
> 4. A **Conditional State Router** that triggers self-correction loops when accuracy dips below 95%.
> 5. Both ephemeral typed state and persistent SQLite session memory."

---

### Q2: Why did you choose LangGraph over traditional sequential LangChain chains?
**Answer:**
> "Traditional linear chains are acyclic—they move only forward. Real-world analytical reasoning requires cycles, conditional branching, and self-correction. LangGraph models workflows as state machines (`StateGraph`), enabling cyclical self-correction where the Evaluator can reject an insight and route back to the Data Analyst to re-compute with refined parameters."

---

### Q3: How do you prevent hallucination when agents quote numbers from datasets?
**Answer:**
> "We implement a 3-tier defense:
> 1. **Tool Restriction:** The LLM does not perform math inside its attention layers; it selects validated deterministic tools (`group_analysis`, `calculate_correlation`, `detect_anomalies`).
> 2. **Structured Outputs:** Insights are produced with an explicit `evidence` payload mapping claimed values to raw calculations.
> 3. **Autonomous Evaluator Guardrail:** The Evaluation Agent intercepts every claim, queries the underlying Pandas dataframe, and tests whether `|claimed - actual| <= tolerance`. If discrepancies occur, the evaluation node rejects the claim and initiates controlled retries."

---

### Q4: How do you handle security and arbitrary code execution?
**Answer:**
> "We explicitly avoid `eval()`, `exec()`, or raw LLM-generated Python string execution. Instead, we implement a closed-world tool calling pattern. Agents choose from a curated registry of validated tools (`filter_data`, `group_analysis`) with strict typing (Pydantic) and operator whitelists (`==`, `!=`, `>`, `<`, `contains`), completely eliminating remote code execution vulnerabilities."

---

### Q5: How is memory managed across sessions?
**Answer:**
> "We use a hybrid memory model:
> - **Short-term Working Memory:** Managed via LangGraph's `AgentState` TypedDict, which passes through nodes in memory.
> - **Long-term Persistent Memory:** Managed via an embedded SQLite database (`memory/insightflow.db`), logging session metadata, execution traces, evaluation scorecards, and final markdown reports for auditability."
