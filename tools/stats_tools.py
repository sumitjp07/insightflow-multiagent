"""
tools/stats_tools.py – Statistical Analysis Tools
====================================================
Advanced statistical analysis tools jo Insight Research Agent use karta hai.

Har tool ka kaam:
  - calculate_correlation()  → Columns ke beech relationship measure karo
  - group_analysis()         → Group by karke aggregations nikalo
  - detect_anomalies()       → Outliers dhundho (IQR method)
  - get_top_bottom()         → Top/Bottom N records nikalo
  - calculate_growth()       → Period over period growth calculate karo
"""

import pandas as pd
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def calculate_correlation(df: pd.DataFrame, 
                          columns: Optional[list] = None) -> dict:
    """
    Numeric columns ke beech correlation calculate karta hai.
    
    Correlation kya hai? (Simple Hinglish)
    → Do numbers ke beech ka relationship measure karta hai.
    → +1 = dono saath badhte hain
    → -1 = ek badhta hai, dusra ghatta hai
    → 0  = koi relationship nahi
    
    Args:
        df: DataFrame
        columns: Specific columns (None = sab numeric columns)
    
    Returns:
        dict with correlation matrix
    """
    try:
        if columns:
            # Check ki sab columns exist karte hain
            missing = [c for c in columns if c not in df.columns]
            if missing:
                return {"success": False, "error": f"Columns not found: {missing}"}
            numeric_df = df[columns].select_dtypes(include=[np.number])
        else:
            numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            return {"success": False, "error": "No numeric columns found"}
        
        corr_matrix = numeric_df.corr().round(4)
        
        # Strong correlations dhundho (> 0.7 ya < -0.7)
        strong_correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                val = corr_matrix.iloc[i, j]
                if abs(val) >= 0.7:
                    strong_correlations.append({
                        "column_1": corr_matrix.columns[i],
                        "column_2": corr_matrix.columns[j],
                        "correlation": float(val),
                        "strength": "Strong Positive" if val > 0 else "Strong Negative"
                    })
        
        return {
            "success": True,
            "correlation_matrix": corr_matrix.to_dict(),
            "strong_correlations": strong_correlations,
            "columns_analyzed": list(numeric_df.columns),
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def group_analysis(df: pd.DataFrame, group_by: str,
                   agg_column: str, 
                   agg_functions: list = None) -> dict:
    """
    Data ko group karke aggregate karta hai.
    
    Example: group_analysis(df, "Region", "Revenue", ["sum", "mean", "count"])
    → Har Region ka total Revenue, average Revenue, aur count dega.
    
    Args:
        df: DataFrame
        group_by: Kis column se group karna hai
        agg_column: Kis column pe calculation karna hai
        agg_functions: ["sum", "mean", "count", "min", "max", "median", "std"]
    
    Returns:
        dict with grouped results
    """
    try:
        if group_by not in df.columns:
            return {"success": False, "error": f"Column '{group_by}' not found"}
        if agg_column not in df.columns:
            return {"success": False, "error": f"Column '{agg_column}' not found"}
        
        # Allowed aggregation functions only — security!
        allowed_funcs = {"sum", "mean", "count", "min", "max", "median", "std"}
        if agg_functions is None:
            agg_functions = ["sum", "mean", "count"]
        
        invalid_funcs = [f for f in agg_functions if f not in allowed_funcs]
        if invalid_funcs:
            return {"success": False, "error": f"Invalid functions: {invalid_funcs}. Allowed: {allowed_funcs}"}
        
        grouped = df.groupby(group_by)[agg_column].agg(agg_functions)
        
        # Round numeric values
        if isinstance(grouped, pd.DataFrame):
            grouped = grouped.round(2)
        
        result_dict = {}
        if isinstance(grouped, pd.DataFrame):
            for group_name in grouped.index:
                result_dict[str(group_name)] = {
                    func: float(grouped.loc[group_name, func])
                    for func in agg_functions
                }
        
        # Best aur worst group identify karo
        if "sum" in agg_functions:
            sums = {k: v.get("sum", 0) for k, v in result_dict.items()}
            best_group = max(sums, key=sums.get) if sums else None
            worst_group = min(sums, key=sums.get) if sums else None
        else:
            best_group = worst_group = None
        
        logger.info(f"📊 Group analysis: {group_by} × {agg_column} → {len(result_dict)} groups")
        
        return {
            "success": True,
            "group_by": group_by,
            "agg_column": agg_column,
            "results": result_dict,
            "best_group": best_group,
            "worst_group": worst_group,
            "total_groups": len(result_dict),
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def detect_anomalies(df: pd.DataFrame, column: str,
                     method: str = "iqr",
                     threshold: float = 1.5) -> dict:
    """
    Outliers / anomalies detect karta hai IQR method se.
    
    IQR Method (Simple Hinglish):
    → IQR = Q3 - Q1 (middle 50% data ka range)
    → Lower bound = Q1 - 1.5 × IQR
    → Upper bound = Q3 + 1.5 × IQR
    → Jo values in bounds ke bahar hain = anomalies!
    
    Args:
        df: DataFrame
        column: Numeric column name
        method: "iqr" (abhi sirf yahi supported hai)
        threshold: IQR multiplier (default 1.5)
    
    Returns:
        dict with anomaly details
    """
    try:
        if column not in df.columns:
            return {"success": False, "error": f"Column '{column}' not found"}
        
        if not pd.api.types.is_numeric_dtype(df[column]):
            return {"success": False, "error": f"Column '{column}' is not numeric"}
        
        col_data = df[column].dropna()
        
        q1 = float(col_data.quantile(0.25))
        q3 = float(col_data.quantile(0.75))
        iqr = q3 - q1
        
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        # Anomalies dhundho
        anomaly_mask = (col_data < lower_bound) | (col_data > upper_bound)
        anomalies = df.loc[col_data[anomaly_mask].index]
        
        return {
            "success": True,
            "column": column,
            "method": method,
            "statistics": {
                "q1": round(q1, 2),
                "q3": round(q3, 2),
                "iqr": round(iqr, 2),
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
            },
            "anomaly_count": int(anomaly_mask.sum()),
            "anomaly_percentage": round(anomaly_mask.sum() / len(col_data) * 100, 2),
            "anomaly_indices": anomalies.index.tolist(),
            "total_data_points": len(col_data),
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_top_bottom(df: pd.DataFrame, column: str,
                   n: int = 5, 
                   order: str = "top") -> dict:
    """
    Top ya Bottom N records deta hai kisi column ke basis pe.
    
    Args:
        df: DataFrame
        column: Sort kis column pe karna hai
        n: Kitne records (default 5)
        order: "top" (highest first) ya "bottom" (lowest first)
    
    Returns:
        dict with top/bottom records
    """
    try:
        if column not in df.columns:
            return {"success": False, "error": f"Column '{column}' not found"}
        
        n = min(n, len(df))  # N zyada ho toh adjust karo
        
        if order == "top":
            result_df = df.nlargest(n, column)
        elif order == "bottom":
            result_df = df.nsmallest(n, column)
        else:
            return {"success": False, "error": f"Invalid order '{order}'. Use 'top' or 'bottom'"}
        
        return {
            "success": True,
            "order": order,
            "column": column,
            "n": n,
            "records": result_df.to_dict(orient="records"),
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def calculate_growth(df: pd.DataFrame, date_column: str,
                     value_column: str,
                     period: str = "M") -> dict:
    """
    Time period ke basis pe growth rate calculate karta hai.
    
    Args:
        df: DataFrame
        date_column: Date column name
        value_column: Value column (e.g., Revenue)
        period: "M" (monthly), "Q" (quarterly), "Y" (yearly)
    
    Returns:
        dict with growth rates
    """
    try:
        if date_column not in df.columns:
            return {"success": False, "error": f"Column '{date_column}' not found"}
        if value_column not in df.columns:
            return {"success": False, "error": f"Column '{value_column}' not found"}
        
        df_copy = df.copy()
        df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors="coerce")
        
        # NaT (not a time) rows hatao
        df_copy = df_copy.dropna(subset=[date_column])
        
        # Period ke basis pe group karo
        df_copy = df_copy.set_index(date_column)
        period_code = "ME" if period == "M" else period
        period_sum = df_copy[value_column].resample(period_code).sum()
        
        # Growth rate calculate karo
        growth_rates = period_sum.pct_change() * 100
        
        results = {}
        for period_idx, (total, growth) in enumerate(zip(period_sum, growth_rates)):
            period_label = str(period_sum.index[period_idx].strftime("%Y-%m"))
            results[period_label] = {
                "total": round(float(total), 2),
                "growth_rate_pct": round(float(growth), 2) if not pd.isna(growth) else None,
            }
        
        # Overall growth
        if len(period_sum) >= 2:
            first_val = float(period_sum.iloc[0])
            last_val = float(period_sum.iloc[-1])
            overall_growth = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0
        else:
            overall_growth = 0
        
        return {
            "success": True,
            "date_column": date_column,
            "value_column": value_column,
            "period": period,
            "results": results,
            "overall_growth_pct": round(overall_growth, 2),
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Quick Test ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  InsightFlow – Stats Tools Test")
    print("="*55)
    
    # Load sample data
    df = pd.read_csv("sample_data/sales_data.csv")
    
    # Test 1: Correlation
    print("\n📌 Test 1: Correlation Analysis")
    corr = calculate_correlation(df, ["Units_Sold", "Unit_Price", "Revenue"])
    if corr['success']:
        for sc in corr['strong_correlations']:
            print(f"  {sc['column_1']} ↔ {sc['column_2']}: {sc['correlation']} ({sc['strength']})")
        if not corr['strong_correlations']:
            print("  No strong correlations found (>0.7)")
    
    # Test 2: Group Analysis
    print("\n📌 Test 2: Group Analysis (Region × Revenue)")
    ga = group_analysis(df, "Region", "Revenue", ["sum", "mean", "count"])
    if ga['success']:
        for group, vals in ga['results'].items():
            print(f"  {group}: Total=₹{vals['sum']:,.0f}, Avg=₹{vals['mean']:,.0f}, Count={vals['count']:.0f}")
        print(f"  🏆 Best: {ga['best_group']}")
    
    # Test 3: Anomaly Detection
    print("\n📌 Test 3: Anomaly Detection (Revenue)")
    anomalies = detect_anomalies(df, "Revenue")
    if anomalies['success']:
        print(f"  Anomalies found: {anomalies['anomaly_count']}")
        print(f"  Bounds: ₹{anomalies['statistics']['lower_bound']:,.0f} to ₹{anomalies['statistics']['upper_bound']:,.0f}")
    
    # Test 4: Top 5
    print("\n📌 Test 4: Top 5 by Revenue")
    top = get_top_bottom(df, "Revenue", n=5, order="top")
    if top['success']:
        for i, rec in enumerate(top['records'], 1):
            print(f"  #{i}: {rec.get('Product', 'N/A')} - ₹{rec['Revenue']:,.0f}")
    
    # Test 5: Growth
    print("\n📌 Test 5: Monthly Growth (Revenue)")
    growth = calculate_growth(df, "Date", "Revenue", "M")
    if growth['success']:
        for period, vals in growth['results'].items():
            gr = f"{vals['growth_rate_pct']:+.1f}%" if vals['growth_rate_pct'] is not None else "N/A"
            print(f"  {period}: ₹{vals['total']:,.0f} ({gr})")
        print(f"  📈 Overall Growth: {growth['overall_growth_pct']:+.1f}%")
    
    print("\n" + "="*55)
    print("  ✅ All Stats Tools Tests Passed!")
    print("="*55 + "\n")

