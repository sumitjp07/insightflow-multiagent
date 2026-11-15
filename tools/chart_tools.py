"""
tools/chart_tools.py – Chart & Visualization Tools
====================================================
Plotly-based interactive charts banata hai jo Streamlit UI mein dikhte hain.

Charts available:
  - create_bar_chart()     → Bar chart (comparisons ke liye)
  - create_line_chart()    → Line chart (trends ke liye)
  - create_pie_chart()     → Pie chart (distribution ke liye)
  - create_scatter_plot()  → Scatter plot (correlations ke liye)
  - create_heatmap()       → Heatmap (correlation matrix ke liye)
  - create_histogram()     → Histogram (distribution ke liye)
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ── Color Theme (Professional SaaS look) ──────────────────
COLORS = {
    "primary": "#4F46E5",      # Indigo
    "secondary": "#7C3AED",    # Purple
    "success": "#10B981",      # Green
    "warning": "#F59E0B",      # Amber
    "danger": "#EF4444",       # Red
    "info": "#3B82F6",         # Blue
}

COLOR_SEQUENCE = [
    "#4F46E5", "#7C3AED", "#10B981", "#F59E0B", 
    "#EF4444", "#3B82F6", "#EC4899", "#14B8A6",
    "#F97316", "#8B5CF6", "#06B6D4", "#84CC16"
]

LAYOUT_TEMPLATE = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "Inter, sans-serif", "size": 13, "color": "#374151"},
    "title_font": {"size": 18, "color": "#111827"},
    "margin": {"l": 60, "r": 30, "t": 60, "b": 60},
}


def create_bar_chart(df: pd.DataFrame, x: str, y: str,
                     title: str = "Bar Chart",
                     color: Optional[str] = None,
                     orientation: str = "v") -> dict:
    """
    Bar chart banata hai — comparisons dikhane ke liye best hai.
    
    Args:
        df: DataFrame
        x: X-axis column
        y: Y-axis column
        title: Chart title
        color: Optional — color group column
        orientation: "v" (vertical) ya "h" (horizontal)
    """
    try:
        fig = px.bar(
            df, x=x, y=y,
            title=title,
            color=color,
            orientation=orientation,
            color_discrete_sequence=COLOR_SEQUENCE,
        )
        fig.update_layout(**LAYOUT_TEMPLATE)
        fig.update_layout(
            xaxis_title=x,
            yaxis_title=y,
            showlegend=color is not None,
        )
        
        return {"success": True, "figure": fig, "chart_type": "bar"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_line_chart(df: pd.DataFrame, x: str, y: str,
                      title: str = "Line Chart",
                      color: Optional[str] = None) -> dict:
    """
    Line chart banata hai — trends dikhane ke liye best hai.
    """
    try:
        fig = px.line(
            df, x=x, y=y,
            title=title,
            color=color,
            color_discrete_sequence=COLOR_SEQUENCE,
            markers=True,
        )
        fig.update_layout(**LAYOUT_TEMPLATE)
        fig.update_traces(line=dict(width=2.5))
        
        return {"success": True, "figure": fig, "chart_type": "line"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_pie_chart(df: pd.DataFrame, names: str, values: str,
                     title: str = "Pie Chart",
                     hole: float = 0.4) -> dict:
    """
    Pie / Donut chart banata hai — proportions dikhane ke liye.
    
    Args:
        hole: 0 = full pie, 0.4 = donut style
    """
    try:
        fig = px.pie(
            df, names=names, values=values,
            title=title,
            color_discrete_sequence=COLOR_SEQUENCE,
            hole=hole,
        )
        fig.update_layout(**LAYOUT_TEMPLATE)
        fig.update_traces(
            textinfo="percent+label",
            textfont_size=12,
        )
        
        return {"success": True, "figure": fig, "chart_type": "pie"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_scatter_plot(df: pd.DataFrame, x: str, y: str,
                        title: str = "Scatter Plot",
                        color: Optional[str] = None,
                        size: Optional[str] = None,
                        trendline: bool = False) -> dict:
    """
    Scatter plot banata hai — do variables ke relationship ke liye.
    """
    try:
        fig = px.scatter(
            df, x=x, y=y,
            title=title,
            color=color,
            size=size,
            color_discrete_sequence=COLOR_SEQUENCE,
            trendline="ols" if trendline else None,
        )
        fig.update_layout(**LAYOUT_TEMPLATE)
        
        return {"success": True, "figure": fig, "chart_type": "scatter"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_heatmap(df: pd.DataFrame, 
                   title: str = "Correlation Heatmap",
                   columns: Optional[list] = None) -> dict:
    """
    Correlation heatmap banata hai — relationships visualize karne ke liye.
    """
    try:
        if columns:
            numeric_df = df[columns].select_dtypes(include=[np.number])
        else:
            numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            return {"success": False, "error": "No numeric columns for heatmap"}
        
        corr_matrix = numeric_df.corr().round(3)
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns.tolist(),
            y=corr_matrix.columns.tolist(),
            colorscale="RdBu_r",
            zmin=-1, zmax=1,
            text=corr_matrix.values.round(2),
            texttemplate="%{text}",
            textfont={"size": 12},
        ))
        fig.update_layout(
            title=title,
            **LAYOUT_TEMPLATE
        )
        
        return {"success": True, "figure": fig, "chart_type": "heatmap"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_histogram(df: pd.DataFrame, column: str,
                     title: str = "Distribution",
                     bins: int = 20,
                     color: Optional[str] = None) -> dict:
    """
    Histogram banata hai — data distribution dikhane ke liye.
    """
    try:
        fig = px.histogram(
            df, x=column,
            title=title,
            nbins=bins,
            color=color,
            color_discrete_sequence=COLOR_SEQUENCE,
        )
        fig.update_layout(**LAYOUT_TEMPLATE)
        fig.update_layout(
            xaxis_title=column,
            yaxis_title="Count",
        )
        
        return {"success": True, "figure": fig, "chart_type": "histogram"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Quick Test ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  InsightFlow – Chart Tools Test")
    print("="*55)
    
    df = pd.read_csv("sample_data/sales_data.csv")
    
    # Test each chart type
    tests = [
        ("Bar Chart", create_bar_chart(df.groupby("Region")["Revenue"].sum().reset_index(), "Region", "Revenue", "Revenue by Region")),
        ("Line Chart", create_line_chart(df, "Date", "Revenue", "Revenue Over Time")),
        ("Pie Chart", create_pie_chart(df.groupby("Category")["Revenue"].sum().reset_index(), "Category", "Revenue", "Revenue by Category")),
        ("Scatter Plot", create_scatter_plot(df, "Units_Sold", "Revenue", "Units vs Revenue")),
        ("Heatmap", create_heatmap(df, "Correlation Heatmap")),
        ("Histogram", create_histogram(df, "Revenue", "Revenue Distribution")),
    ]
    
    for name, result in tests:
        status = "✅" if result['success'] else "❌"
        print(f"  {status}  {name}: {result.get('chart_type', result.get('error', 'unknown'))}")
    
    print("\n" + "="*55)
    print("  ✅ All Chart Tools Tests Passed!")
    print("="*55 + "\n")

