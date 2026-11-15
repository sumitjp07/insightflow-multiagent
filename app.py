"""
app.py – InsightFlow Main Streamlit Application
================================================
SaaS-style Interactive AI Data Research & Analysis Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import os
import sys
import logging

logger = logging.getLogger(__name__)

# Project root path add karo taaki local imports properly work karein
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

import config
from tools.data_tools import (
    load_dataset,
    get_data_summary,
    clean_dataset,
    get_column_stats,
    filter_data,
    get_value_counts
)
from tools.stats_tools import (
    calculate_correlation,
    group_analysis,
    detect_anomalies,
    get_top_bottom,
    calculate_growth
)
from tools.chart_tools import (
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
    create_scatter_plot,
    create_heatmap,
    create_histogram
)
from tools.file_tools import save_uploaded_file, get_sample_files
from tools.pdf_generator import generate_pdf_report
from memory.session_store import SessionStore
from workflow.graph import run_insightflow_pipeline

# ── Page Configuration ─────────────────────────────────────
st.set_page_config(
    page_title=f"{config.APP_NAME} | Autonomous Multi-Agent AI System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for Professional SaaS Styling ───────────────
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Header Gradient & Badges */
    .brand-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    
    .brand-sub {
        font-size: 0.95rem;
        color: #6B7280;
        font-weight: 500;
        margin-bottom: 1.2rem;
    }

    .metric-card {
        background: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 1.7rem;
        font-weight: 700;
        color: #111827;
    }
    .metric-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #6B7280;
    }
    
    .agent-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 2px;
    }
    .agent-pill-ready { background: #DEF7EC; color: #03543F; }
    .agent-pill-working { background: #FEF08A; color: #713F12; }
    .agent-pill-waiting { background: #F3F4F6; color: #374151; }
</style>
""", unsafe_allow_html=True)

# ── Session State Initialization ───────────────────────────
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "current_df" not in st.session_state:
    st.session_state.current_df = None
if "file_name" not in st.session_state:
    st.session_state.file_name = None
if "cleaning_history" not in st.session_state:
    st.session_state.cleaning_history = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── Top Bar / Header ───────────────────────────────────────
col_logo, col_status = st.columns([3, 1])
with col_logo:
    st.markdown('<p class="brand-title">⚡ InsightFlow</p>', unsafe_allow_html=True)
    st.markdown('<p class="brand-sub">Autonomous Multi-Agent AI Data Research & Analysis System</p>', unsafe_allow_html=True)
with col_status:
    api_ready = bool(config.GEMINI_API_KEY and config.GEMINI_API_KEY != "your_gemini_api_key_here")
    if api_ready:
        st.success(f"🟢 LLM Ready: {config.LLM_MODEL_NAME}")
    else:
        st.warning("⚠️ API Key Pending in .env")

# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📁 Data Ingestion")
    
    data_source = st.radio(
        "Choose Data Source:",
        ["Sample Dataset", "Upload Custom File"],
        horizontal=True
    )
    
    selected_file_path = None
    
    if data_source == "Sample Dataset":
        samples = get_sample_files()
        sample_options = {f["name"]: f["path"] for f in samples}
        
        if sample_options:
            chosen_sample = st.selectbox("Select Sample Dataset:", list(sample_options.keys()))
            selected_file_path = sample_options[chosen_sample]
            if st.button("📥 Load Sample Dataset", use_container_width=True, type="primary"):
                load_res = load_dataset(selected_file_path)
                if load_res["success"]:
                    st.session_state.raw_df = load_res["data"]
                    st.session_state.current_df = load_res["data"].copy()
                    st.session_state.file_name = chosen_sample
                    st.session_state.cleaning_history = ["Original dataset loaded"]
                    st.toast(f"Loaded {chosen_sample}!", icon="✅")
                    st.rerun()
                else:
                    st.error(load_res["message"])
        else:
            st.info("No sample datasets found in sample_data/")
            
    else:
        uploaded_file = st.file_uploader(
            "Upload CSV or Excel file",
            type=["csv", "xlsx", "xls"],
            help="Limit 50MB. Columns will be automatically inferred."
        )
        if uploaded_file is not None:
            if st.button("⚡ Process Uploaded File", use_container_width=True, type="primary"):
                save_res = save_uploaded_file(uploaded_file)
                if save_res["success"]:
                    load_res = load_dataset(save_res["file_path"])
                    if load_res["success"]:
                        st.session_state.raw_df = load_res["data"]
                        st.session_state.current_df = load_res["data"].copy()
                        st.session_state.file_name = uploaded_file.name
                        st.session_state.cleaning_history = ["Uploaded file loaded"]
                        st.toast(f"Successfully processed {uploaded_file.name}!", icon="🚀")
                        st.rerun()
                    else:
                        st.error(load_res["message"])
                else:
                    st.error(save_res["error"])

    st.markdown("---")
    
    # Dataset Quick Metrics in Sidebar
    if st.session_state.current_df is not None:
        df = st.session_state.current_df
        st.markdown(f"**Active Dataset:** `{st.session_state.file_name}`")
        
        c1, c2 = st.columns(2)
        c1.metric("Rows", f"{len(df):,}")
        c2.metric("Columns", f"{len(df.columns):,}")
        
        missing_count = int(df.isnull().sum().sum())
        c3, c4 = st.columns(2)
        c3.metric("Duplicates", int(df.duplicated().sum()))
        c4.metric("Missing", missing_count)
        
        if st.button("🔄 Reset to Original Data", use_container_width=True):
            if st.session_state.raw_df is not None:
                st.session_state.current_df = st.session_state.raw_df.copy()
                st.session_state.cleaning_history.append("Reset to original raw dataset")
                st.toast("Reset complete!", icon="🔄")
                st.rerun()
                
    st.markdown("---")
    st.markdown("### 🤖 Multi-Agent Roster")
    st.markdown("""
    - <span class="agent-pill agent-pill-ready">🧠 Planner</span>
    - <span class="agent-pill agent-pill-ready">📊 Data Analyst</span>
    - <span class="agent-pill agent-pill-ready">🔍 Insight Research</span>
    - <span class="agent-pill agent-pill-ready">⚖️ Evaluator</span>
    - <span class="agent-pill agent-pill-ready">📄 Report Gen</span>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption(f"InsightFlow v{config.APP_VERSION} • Built with LangGraph & Streamlit")

# ── Main Content Area ──────────────────────────────────────
if st.session_state.current_df is None:
    # Empty State Hero Screen
    st.info("👈 **Shuru karne ke liye:** Sidebar se ek Sample Dataset chuno ya apna CSV/Excel upload karo!")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        st.markdown("""
        #### 1. Autonomous Planning
        User query ko subtasks mein break karke optimal execution graph banata hai.
        """)
    with col_f2:
        st.markdown("""
        #### 2. Rigorous Analytics
        Pandas & NumPy validated tools se deep statistical computations & correlation search.
        """)
    with col_f3:
        st.markdown("""
        #### 3. Evidence Evaluation
        Hallucination protection! Har statement ko raw numbers aur dataset evidence se verify karta hai.
        """)
        
    st.markdown("---")
    st.subheader("💡 Sample Data Quick Start")
    st.write("Aap niche diye gaye sample datasets me se choose kar sakte hain:")
    sample_preview_cols = st.columns(2)
    with sample_preview_cols[0]:
        st.markdown("**1. Sales Data (`sales_data.csv`)**")
        st.caption("30 rows of multi-region product sales, revenue, discounts, and customer ratings.")
    with sample_preview_cols[1]:
        st.markdown("**2. Employee Workforce (`employee_data.csv`)**")
        st.caption("20 rows of department roles, salaries, experience, ratings, and remote status.")
        
else:
    df = st.session_state.current_df
    
    # ── Tabs Navigation ────────────────────────────────────
    tab_preview, tab_analytics, tab_cleaning, tab_agents, tab_reports = st.tabs([
        "📋 Data Preview & Stats",
        "📈 Interactive Visualizations",
        "🧹 Data Cleaning & Transform",
        "🤖 AI Agent Workspace",
        "📄 Reports & Export"
    ])
    
    # ── Tab 1: Preview & Summary ───────────────────────────
    with tab_preview:
        st.subheader("📊 Dataset Overview")
        
        # Metric Tiles
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Rows", f"{len(df):,}")
        m2.metric("Total Columns", f"{len(df.columns)}")
        m3.metric("Numeric Cols", len(df.select_dtypes(include=[np.number]).columns))
        m4.metric("Categorical Cols", len(df.select_dtypes(include=['object', 'category']).columns))
        m5.metric("Memory Usage", f"{round(df.memory_usage(deep=True).sum()/1024, 1)} KB")
        
        st.markdown("---")
        
        # Data View Mode
        col_view_opt, col_search = st.columns([2, 3])
        with col_view_opt:
            view_mode = st.radio("Rows to show:", ["First 10 Rows", "Last 10 Rows", "Full Dataset"], horizontal=True)
        with col_search:
            search_query = st.text_input("🔍 Quick Search / Filter in dataset:", "")
            
        display_df = df
        if search_query:
            mask = display_df.astype(str).apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
            display_df = display_df[mask]
            st.caption(f"Filtered {len(display_df)} matching rows for '{search_query}'")
            
        if view_mode == "First 10 Rows":
            st.dataframe(display_df.head(10), use_container_width=True)
        elif view_mode == "Last 10 Rows":
            st.dataframe(display_df.tail(10), use_container_width=True)
        else:
            st.dataframe(display_df, use_container_width=True)
            
        st.markdown("---")
        
        # Column Inspector
        st.subheader("🔬 Column Inspector")
        sel_col = st.selectbox("Inspect specific column details:", list(df.columns))
        if sel_col:
            stats_res = get_column_stats(df, sel_col)
            if stats_res["success"]:
                c_info = stats_res["stats"]
                ci1, ci2, ci3, ci4 = st.columns(4)
                ci1.metric("Data Type", c_info["dtype"])
                ci2.metric("Unique Values", f"{c_info['unique_count']}")
                ci3.metric("Missing Count", f"{c_info['null_count']}")
                ci4.metric("Missing %", f"{c_info['null_percentage']}%")
                
                if "mean" in c_info:
                    st.markdown("**Numeric Summary Statistics:**")
                    num_metrics = st.columns(6)
                    num_metrics[0].metric("Mean", f"{c_info['mean']:,.2f}")
                    num_metrics[1].metric("Median", f"{c_info['median']:,.2f}")
                    num_metrics[2].metric("Std Dev", f"{c_info['std']:,.2f}")
                    num_metrics[3].metric("Min", f"{c_info['min']:,.2f}")
                    num_metrics[4].metric("Max", f"{c_info['max']:,.2f}")
                    num_metrics[5].metric("Skewness", f"{c_info.get('skewness', 0):.2f}")
                elif "top_values" in c_info:
                    st.markdown("**Top Categories Distribution:**")
                    top_v = pd.DataFrame(list(c_info["top_values"].items()), columns=["Category", "Count"])
                    st.dataframe(top_v, use_container_width=True)

    # ── Tab 2: Visualizations ──────────────────────────────
    with tab_analytics:
        st.subheader("📈 Interactive Visualizations")
        
        chart_type = st.selectbox(
            "Select Chart Type:",
            ["Bar Chart", "Line Chart", "Pie / Donut Chart", "Scatter Plot", "Correlation Heatmap", "Histogram Distribution"]
        )
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        all_cols = list(df.columns)
        
        if chart_type == "Bar Chart":
            cb1, cb2, cb3 = st.columns(3)
            x_col = cb1.selectbox("Category / X Axis:", all_cols, index=0)
            y_col = cb2.selectbox("Metric / Y Axis:", numeric_cols if numeric_cols else all_cols, index=0)
            color_col = cb3.selectbox("Group by Color (Optional):", [None] + all_cols, index=0)
            
            # Aggregate if there are many entries for cleaner bar chart
            agg_data = df.groupby(x_col)[y_col].sum().reset_index() if color_col is None else df
            fig_res = create_bar_chart(agg_data, x=x_col, y=y_col, title=f"{y_col} by {x_col}", color=color_col)
            if fig_res["success"]:
                st.plotly_chart(fig_res["figure"], use_container_width=True)
                
        elif chart_type == "Line Chart":
            cl1, cl2, cl3 = st.columns(3)
            x_col = cl1.selectbox("Time / Sequence (X Axis):", all_cols, index=0)
            y_col = cl2.selectbox("Measurement (Y Axis):", numeric_cols if numeric_cols else all_cols, index=0)
            color_col = cl3.selectbox("Color / Group (Optional):", [None] + all_cols, index=0)
            
            fig_res = create_line_chart(df, x=x_col, y=y_col, title=f"Trend: {y_col} across {x_col}", color=color_col)
            if fig_res["success"]:
                st.plotly_chart(fig_res["figure"], use_container_width=True)
                
        elif chart_type == "Pie / Donut Chart":
            cp1, cp2, cp3 = st.columns(3)
            names_col = cp1.selectbox("Category Names:", all_cols, index=0)
            val_col = cp2.selectbox("Values / Weights:", numeric_cols if numeric_cols else all_cols, index=0)
            donut = cp3.checkbox("Donut Style (Hole in middle)", value=True)
            
            pie_agg = df.groupby(names_col)[val_col].sum().reset_index()
            fig_res = create_pie_chart(pie_agg, names=names_col, values=val_col, title=f"{val_col} Share by {names_col}", hole=0.4 if donut else 0.0)
            if fig_res["success"]:
                st.plotly_chart(fig_res["figure"], use_container_width=True)
                
        elif chart_type == "Scatter Plot":
            cs1, cs2, cs3, cs4 = st.columns(4)
            x_col = cs1.selectbox("X Coordinate:", numeric_cols if numeric_cols else all_cols, index=0)
            y_col = cs2.selectbox("Y Coordinate:", numeric_cols if len(numeric_cols) > 1 else all_cols, index=min(1, len(numeric_cols)-1))
            color_col = cs3.selectbox("Color Tag:", [None] + all_cols, index=0)
            trend = cs4.checkbox("Show Trendline (OLS)", value=False)
            
            fig_res = create_scatter_plot(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}", color=color_col, trendline=trend)
            if fig_res["success"]:
                st.plotly_chart(fig_res["figure"], use_container_width=True)
                
        elif chart_type == "Correlation Heatmap":
            st.write("Displays Pearson Correlation coefficients across numeric features.")
            fig_res = create_heatmap(df, title="Feature Correlation Matrix")
            if fig_res["success"]:
                st.plotly_chart(fig_res["figure"], use_container_width=True)
            else:
                st.warning(fig_res.get("error", "Could not generate heatmap"))
                
        elif chart_type == "Histogram Distribution":
            ch1, ch2, ch3 = st.columns(3)
            h_col = ch1.selectbox("Column to analyze:", numeric_cols if numeric_cols else all_cols, index=0)
            bins = ch2.slider("Number of Bins:", min_value=5, max_value=50, value=15)
            color_col = ch3.selectbox("Split by Category:", [None] + all_cols, index=0)
            
            fig_res = create_histogram(df, column=h_col, title=f"Distribution of {h_col}", bins=bins, color=color_col)
            if fig_res["success"]:
                st.plotly_chart(fig_res["figure"], use_container_width=True)

    # ── Tab 3: Data Cleaning ───────────────────────────────
    with tab_cleaning:
        st.subheader("🧹 Data Cleaning & Preprocessing")
        st.write("Apply validated, safe transformations to sanitize the current dataset.")
        
        tc1, tc2 = st.columns(2)
        with tc1:
            st.markdown("#### 1. Deduplication")
            dup_count = int(df.duplicated().sum())
            st.write(f"Current duplicate rows: **{dup_count}**")
            if st.button("🗑️ Drop Duplicate Rows", disabled=(dup_count == 0)):
                clean_res = clean_dataset(df, drop_duplicates=True, fill_strategy="none")
                if clean_res["success"]:
                    st.session_state.current_df = clean_res["data"]
                    st.session_state.cleaning_history.append(f"Dropped {dup_count} duplicates")
                    st.success(f"Removed {dup_count} duplicate rows!")
                    st.rerun()
                    
        with tc2:
            st.markdown("#### 2. Missing Value Imputation")
            total_missing = int(df.isnull().sum().sum())
            st.write(f"Current total null values: **{total_missing}**")
            strategy = st.selectbox(
                "Select Imputation Strategy:",
                ["none", "mean", "median", "mode", "drop"]
            )
            if st.button("✨ Apply Imputation Strategy", disabled=(strategy == "none" or total_missing == 0)):
                clean_res = clean_dataset(df, drop_duplicates=False, fill_strategy=strategy)
                if clean_res["success"]:
                    st.session_state.current_df = clean_res["data"]
                    for change in clean_res["changes"]:
                        st.session_state.cleaning_history.append(change)
                    st.success("Imputation complete!")
                    st.rerun()
                    
        st.markdown("---")
        st.markdown("#### 📜 Transformation Audit Trail")
        for i, step in enumerate(st.session_state.cleaning_history, 1):
            st.caption(f"{i}. {step}")

    # ── Tab 4: AI Agent Workspace ──────────────────────────
    with tab_agents:
        st.subheader("🤖 Autonomous Multi-Agent Workspace")
        st.write("Submit a natural language research query. InsightFlow's 5 specialized agents will autonomously plan, execute tools, cross-verify evidence, and draft verified reports.")
        
        # Suggested Queries
        st.markdown("**💡 Example Analysis Prompts:**")
        col_q1, col_q2, col_q3 = st.columns(3)
        if col_q1.button("📈 Which product brings maximum revenue?"):
            st.session_state.user_prompt_input = "Which product brings maximum revenue and in which region?"
        if col_q2.button("🔍 Find anomalies in discounts & pricing"):
            st.session_state.user_prompt_input = "Identify outliers or anomalies in product pricing and discounts."
        if col_q3.button("📊 Complete executive performance report"):
            st.session_state.user_prompt_input = "Provide a comprehensive performance analysis summary with top trends and growth opportunities."
            
        user_query = st.text_area(
            "Enter your research / analysis request:",
            value=st.session_state.get("user_prompt_input", ""),
            placeholder="e.g. Analyze sales performance by region, check if high discounts lower ratings, and summarize key drivers."
        )
        
        col_exec, col_mode = st.columns([1, 3])
        with col_exec:
            run_btn = st.button("🚀 Run Multi-Agent Analysis", type="primary", use_container_width=True)

        if "latest_pipeline_result" not in st.session_state:
            st.session_state.latest_pipeline_result = None

        if run_btn:
            if not user_query.strip():
                st.warning("Please enter an analysis query first.")
            else:
                progress_container = st.container()
                with progress_container:
                    st.markdown("#### 🔄 Agent Orchestration Pipeline")
                    agent_cols = st.columns(5)
                    agent_cols[0].info("1. 🧠 Planner\nActive...")
                    agent_cols[1].caption("2. 📊 Data Analyst\nQueued")
                    agent_cols[2].caption("3. 🔍 Insight Research\nQueued")
                    agent_cols[3].caption("4. ⚖️ Evaluator\nQueued")
                    agent_cols[4].caption("5. 📄 Report Gen\nQueued")

                with st.spinner("⚡ Agents collaborating in LangGraph StateGraph..."):
                    result = run_insightflow_pipeline(
                        user_query, 
                        df, 
                        file_name=st.session_state.get("file_name", "dataset.csv")
                    )
                    st.session_state.latest_pipeline_result = result

                    # Save to SQLite Session Store
                    try:
                        store = SessionStore()
                        sess_id = f"sess_{int(datetime.now().timestamp())}"
                        store.create_session(
                            session_id=sess_id,
                            dataset_name=st.session_state.get("file_name", "dataset.csv"),
                            row_count=len(df),
                            column_count=len(df.columns),
                            user_query=user_query,
                            status=result.get("status", "completed")
                        )
                        eval_res = result.get("evaluation_result", {})
                        store.record_evaluation(
                            session_id=sess_id,
                            accuracy=eval_res.get("calculation_accuracy_pct", 100.0),
                            coverage=eval_res.get("evidence_coverage_pct", 100.0),
                            retries=result.get("retry_count", 0),
                            status="approved" if result.get("is_approved") else "flagged"
                        )
                        store.save_report(sess_id, result.get("final_report_md", ""))
                    except Exception as e:
                        logger.warning(f"Could not persist session to SQLite: {e}")

                st.rerun()

        # Render Latest Analysis Results
        if st.session_state.latest_pipeline_result:
            res = st.session_state.latest_pipeline_result
            st.markdown("---")
            st.markdown(f"### 🎯 Results for: *'{res.get('user_query')}'*")
            st.caption(f"Completed in **{res.get('execution_time_seconds')}s** • LangGraph Status: `{res.get('status')}`")

            # Scorecard Metrics
            eval_data = res.get("evaluation_result", {})
            sc1, sc2, sc3, sc4 = st.columns(4)
            sc1.metric("Calculation Accuracy", f"{eval_data.get('calculation_accuracy_pct', 100.0)}%", "Audited ✅")
            sc2.metric("Evidence Coverage", f"{eval_data.get('evidence_coverage_pct', 100.0)}%", "Complete")
            sc3.metric("Self-Correction Retries", f"{res.get('retry_count', 0)}", "Controlled")
            sc4.metric("Verified Claims", f"{eval_data.get('verified_claims', len(res.get('insights', [])))}", "Evidence-backed")

            # Subtask Decomposition Expander
            with st.expander("🧠 View Planner Decomposition & Execution Graph", expanded=False):
                plan_tasks = res.get("subtasks", [])
                if plan_tasks:
                    tasks_table = []
                    for t in plan_tasks:
                        tasks_table.append({
                            "Step": t.get("task_id"),
                            "Assigned Agent": t.get("assigned_agent"),
                            "Action": t.get("action"),
                            "Tool": t.get("tool_name"),
                            "Description": t.get("description")
                        })
                    st.dataframe(pd.DataFrame(tasks_table), use_container_width=True)

            # Evaluator Audit Log Expander
            with st.expander("⚖️ View Evaluator Audit Log & Mathematical Checks", expanded=False):
                for log in res.get("evaluation_logs", []):
                    st.write(log)

            # Final Executive Report
            st.markdown("---")
            st.markdown(res.get("final_report_md", ""))

            # Quick PDF Download Button
            pdf_res = generate_pdf_report(res)
            if pdf_res["success"]:
                pdf_path = Path(pdf_res["pdf_path"])
                if pdf_path.exists():
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    st.download_button(
                        label="📄 Download Official PDF Executive Brief",
                        data=pdf_bytes,
                        file_name=pdf_path.name,
                        mime="application/pdf",
                        type="primary"
                    )

    # ── Tab 5: Reports & History ────────────────────────────
    with tab_reports:
        st.subheader("📄 Analysis History & Reports Repository")
        st.write("Browse persistent SQLite session logs, previous evaluations, and export assets.")

        col_h1, col_h2 = st.columns([1, 1])
        with col_h1:
            st.markdown("#### 📥 Cleaned Dataset Export")
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download Cleaned CSV",
                data=csv_data,
                file_name=f"cleaned_{st.session_state.file_name or 'dataset.csv'}",
                mime="text/csv",
                use_container_width=True
            )

        with col_h2:
            st.markdown("#### 📑 Instant PDF Brief")
            if st.session_state.latest_pipeline_result:
                pdf_res = generate_pdf_report(st.session_state.latest_pipeline_result)
                if pdf_res["success"]:
                    with open(pdf_res["pdf_path"], "rb") as f:
                        st.download_button(
                            label="⬇️ Download Latest PDF Report",
                            data=f.read(),
                            file_name=Path(pdf_res["pdf_path"]).name,
                            mime="application/pdf",
                            use_container_width=True
                        )
            else:
                st.caption("Run an analysis in the Agent Workspace first to generate PDF.")

        st.markdown("---")
        st.markdown("#### 📜 Persistent Session History (SQLite Memory)")
        try:
            store = SessionStore()
            sessions = store.get_recent_sessions(limit=10)
            if sessions:
                sess_df = pd.DataFrame(sessions)
                st.dataframe(sess_df, use_container_width=True)
            else:
                st.info("No prior sessions logged in SQLite yet.")
        except Exception as e:
            st.warning(f"Could not load SQLite history: {e}")
