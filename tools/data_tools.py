"""
tools/data_tools.py – Data Loading & Cleaning Tools
=====================================================
Ye predefined, validated tools hain jo agents use karte hain.
LLM directly Python code nahi chalata — sirf ye safe tools call karta hai.

Har tool ka kaam:
  - load_dataset()    → CSV/Excel file load karo
  - get_data_summary()→ Dataset ka quick overview
  - clean_dataset()   → Missing values, duplicates handle karo
  - get_column_stats()→ Ek column ki detailed statistics
  - filter_data()     → Rows filter karo condition ke basis pe
  - get_value_counts()→ Column mein kitni baar kya aaya
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def load_dataset(file_path: str) -> dict:
    """
    CSV ya Excel file load karta hai.
    
    Args:
        file_path: File ka path (CSV ya Excel)
    
    Returns:
        dict with keys: 'success', 'data' (DataFrame), 'message', 'info'
    
    Example:
        result = load_dataset("sample_data/sales_data.csv")
        if result['success']:
            df = result['data']
    """
    try:
        path = Path(file_path)
        
        # File exists check
        if not path.exists():
            return {
                "success": False,
                "data": None,
                "message": f"❌ File not found: {file_path}",
                "info": {}
            }
        
        # File extension check
        ext = path.suffix.lower()
        if ext not in [".csv", ".xlsx", ".xls"]:
            return {
                "success": False,
                "data": None,
                "message": f"❌ Unsupported file type: {ext}. Use CSV or Excel.",
                "info": {}
            }
        
        # Load based on extension
        if ext == ".csv":
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path, engine="openpyxl")
        
        # Basic info collect karo
        info = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "file_name": path.name,
            "file_size_kb": round(path.stat().st_size / 1024, 2)
        }
        
        logger.info(f"✅ Loaded {path.name}: {info['rows']} rows × {info['columns']} columns")
        
        return {
            "success": True,
            "data": df,
            "message": f"✅ Successfully loaded '{path.name}' ({info['rows']} rows × {info['columns']} columns)",
            "info": info
        }
        
    except Exception as e:
        logger.error(f"❌ Error loading {file_path}: {str(e)}")
        return {
            "success": False,
            "data": None,
            "message": f"❌ Error loading file: {str(e)}",
            "info": {}
        }


def get_data_summary(df: pd.DataFrame) -> dict:
    """
    Dataset ka complete summary deta hai — shape, types, missing values, etc.
    
    Args:
        df: Pandas DataFrame
    
    Returns:
        dict with summary information
    """
    try:
        # Missing values per column
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)
        
        # Numeric columns ki basic stats
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_stats = {}
        for col in numeric_cols:
            numeric_stats[col] = {
                "mean": round(float(df[col].mean()), 2),
                "median": round(float(df[col].median()), 2),
                "std": round(float(df[col].std()), 2),
                "min": round(float(df[col].min()), 2),
                "max": round(float(df[col].max()), 2),
            }
        
        # Categorical columns
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        cat_stats = {}
        for col in cat_cols:
            cat_stats[col] = {
                "unique_count": int(df[col].nunique()),
                "top_value": str(df[col].mode().iloc[0]) if not df[col].mode().empty else "N/A",
                "sample_values": df[col].unique()[:5].tolist()
            }
        
        summary = {
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_values": {col: int(val) for col, val in missing.items() if val > 0},
            "missing_percentage": {col: float(val) for col, val in missing_pct.items() if val > 0},
            "duplicate_rows": int(df.duplicated().sum()),
            "numeric_columns": numeric_cols,
            "categorical_columns": cat_cols,
            "numeric_stats": numeric_stats,
            "categorical_stats": cat_stats,
            "memory_usage_kb": round(df.memory_usage(deep=True).sum() / 1024, 2),
        }
        
        logger.info(f"📊 Summary generated: {summary['shape']}")
        return {"success": True, "summary": summary}
        
    except Exception as e:
        logger.error(f"❌ Error generating summary: {str(e)}")
        return {"success": False, "summary": {}, "error": str(e)}


def clean_dataset(df: pd.DataFrame, 
                  drop_duplicates: bool = True,
                  fill_strategy: str = "none") -> dict:
    """
    Dataset ko clean karta hai — duplicates aur missing values handle karta hai.
    
    Args:
        df: Input DataFrame
        drop_duplicates: True = duplicate rows hatao
        fill_strategy: "none" | "mean" | "median" | "mode" | "drop"
            - none: kuch mat karo
            - mean: numeric columns mein mean se fill karo
            - median: numeric columns mein median se fill karo
            - mode: sabse common value se fill karo
            - drop: missing value wali rows hatao
    
    Returns:
        dict with 'data' (cleaned DataFrame), 'changes' (kya kya hua)
    """
    try:
        original_rows = len(df)
        df_clean = df.copy()
        changes = []
        
        # Step 1: Duplicates handle karo
        if drop_duplicates:
            dup_count = df_clean.duplicated().sum()
            if dup_count > 0:
                df_clean = df_clean.drop_duplicates()
                changes.append(f"🗑️ Removed {dup_count} duplicate rows")
        
        # Step 2: Missing values handle karo
        missing_before = df_clean.isnull().sum().sum()
        
        if fill_strategy == "mean":
            numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if df_clean[col].isnull().any():
                    fill_val = df_clean[col].mean()
                    count = df_clean[col].isnull().sum()
                    df_clean[col] = df_clean[col].fillna(fill_val)
                    changes.append(f"📝 '{col}': {count} missing values filled with mean ({fill_val:.2f})")
                    
        elif fill_strategy == "median":
            numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if df_clean[col].isnull().any():
                    fill_val = df_clean[col].median()
                    count = df_clean[col].isnull().sum()
                    df_clean[col] = df_clean[col].fillna(fill_val)
                    changes.append(f"📝 '{col}': {count} missing values filled with median ({fill_val:.2f})")
                    
        elif fill_strategy == "mode":
            for col in df_clean.columns:
                if df_clean[col].isnull().any():
                    mode_val = df_clean[col].mode()
                    if not mode_val.empty:
                        count = df_clean[col].isnull().sum()
                        df_clean[col] = df_clean[col].fillna(mode_val.iloc[0])
                        changes.append(f"📝 '{col}': {count} missing values filled with mode ({mode_val.iloc[0]})")
                        
        elif fill_strategy == "drop":
            rows_before = len(df_clean)
            df_clean = df_clean.dropna()
            dropped = rows_before - len(df_clean)
            if dropped > 0:
                changes.append(f"🗑️ Dropped {dropped} rows with missing values")
        
        missing_after = df_clean.isnull().sum().sum()
        
        if not changes:
            changes.append("✅ Dataset already clean — no changes needed")
        
        result = {
            "success": True,
            "data": df_clean,
            "changes": changes,
            "stats": {
                "original_rows": original_rows,
                "final_rows": len(df_clean),
                "rows_removed": original_rows - len(df_clean),
                "missing_before": int(missing_before),
                "missing_after": int(missing_after),
            }
        }
        
        logger.info(f"🧹 Cleaning done: {original_rows} → {len(df_clean)} rows")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error cleaning dataset: {str(e)}")
        return {"success": False, "data": df, "changes": [f"❌ Error: {str(e)}"], "stats": {}}


def get_column_stats(df: pd.DataFrame, column_name: str) -> dict:
    """
    Ek specific column ki detailed statistics deta hai.
    
    Args:
        df: DataFrame
        column_name: Column ka naam
    
    Returns:
        dict with column statistics
    """
    try:
        if column_name not in df.columns:
            return {
                "success": False,
                "error": f"❌ Column '{column_name}' not found. Available: {list(df.columns)}"
            }
        
        col = df[column_name]
        stats = {
            "column_name": column_name,
            "dtype": str(col.dtype),
            "total_count": len(col),
            "non_null_count": int(col.count()),
            "null_count": int(col.isnull().sum()),
            "null_percentage": round(col.isnull().sum() / len(col) * 100, 2),
            "unique_count": int(col.nunique()),
        }
        
        # Numeric column ke liye extra stats
        if pd.api.types.is_numeric_dtype(col):
            stats.update({
                "mean": round(float(col.mean()), 4),
                "median": round(float(col.median()), 4),
                "std": round(float(col.std()), 4),
                "min": round(float(col.min()), 4),
                "max": round(float(col.max()), 4),
                "q25": round(float(col.quantile(0.25)), 4),
                "q75": round(float(col.quantile(0.75)), 4),
                "skewness": round(float(col.skew()), 4),
                "kurtosis": round(float(col.kurtosis()), 4),
            })
        else:
            # Categorical column ke liye
            stats.update({
                "top_values": col.value_counts().head(10).to_dict(),
                "sample_values": col.dropna().unique()[:10].tolist(),
            })
        
        return {"success": True, "stats": stats}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def filter_data(df: pd.DataFrame, column: str, 
                operator: str, value) -> dict:
    """
    Data ko filter karta hai given condition ke basis pe.
    
    Args:
        df: DataFrame
        column: Column name
        operator: "==" | "!=" | ">" | "<" | ">=" | "<=" | "contains"
        value: Compare karne ke liye value
    
    Returns:
        dict with filtered DataFrame
    """
    try:
        if column not in df.columns:
            return {
                "success": False,
                "data": None,
                "error": f"❌ Column '{column}' not found."
            }
        
        # Safe operators only — no eval() / no arbitrary code
        allowed_ops = {"==", "!=", ">", "<", ">=", "<=", "contains"}
        if operator not in allowed_ops:
            return {
                "success": False,
                "data": None,
                "error": f"❌ Invalid operator '{operator}'. Use: {allowed_ops}"
            }
        
        if operator == "==":
            filtered = df[df[column] == value]
        elif operator == "!=":
            filtered = df[df[column] != value]
        elif operator == ">":
            filtered = df[df[column] > float(value)]
        elif operator == "<":
            filtered = df[df[column] < float(value)]
        elif operator == ">=":
            filtered = df[df[column] >= float(value)]
        elif operator == "<=":
            filtered = df[df[column] <= float(value)]
        elif operator == "contains":
            filtered = df[df[column].astype(str).str.contains(str(value), case=False, na=False)]
        
        logger.info(f"🔍 Filtered '{column}' {operator} {value}: {len(filtered)} rows")
        
        return {
            "success": True,
            "data": filtered,
            "message": f"Found {len(filtered)} rows where {column} {operator} {value}",
            "original_count": len(df),
            "filtered_count": len(filtered),
        }
        
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


def get_value_counts(df: pd.DataFrame, column: str, 
                     top_n: int = 10) -> dict:
    """
    Column mein har value kitni baar aayi — count deta hai.
    
    Args:
        df: DataFrame
        column: Column name
        top_n: Top kitne results dikhane hain (default 10)
    
    Returns:
        dict with value counts
    """
    try:
        if column not in df.columns:
            return {"success": False, "error": f"Column '{column}' not found."}
        
        counts = df[column].value_counts().head(top_n)
        
        return {
            "success": True,
            "column": column,
            "value_counts": {str(k): int(v) for k, v in counts.items()},
            "total_unique": int(df[column].nunique()),
            "total_rows": len(df),
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Quick Test ─────────────────────────────────────────────
if __name__ == "__main__":
    import json
    
    print("\n" + "="*55)
    print("  InsightFlow – Data Tools Test")
    print("="*55)
    
    # Test 1: Load CSV
    print("\n📌 Test 1: Load sales_data.csv")
    result = load_dataset("sample_data/sales_data.csv")
    print(f"  Status: {result['message']}")
    print(f"  Info: {result['info']['rows']} rows, {result['info']['columns']} cols")
    
    if result['success']:
        df = result['data']
        
        # Test 2: Summary
        print("\n📌 Test 2: Data Summary")
        summary = get_data_summary(df)
        s = summary['summary']
        print(f"  Shape: {s['shape']}")
        print(f"  Missing Values: {s['missing_values'] or 'None'}")
        print(f"  Duplicates: {s['duplicate_rows']}")
        
        # Test 3: Clean
        print("\n📌 Test 3: Clean Dataset")
        clean_result = clean_dataset(df)
        for change in clean_result['changes']:
            print(f"  {change}")
        
        # Test 4: Column Stats
        print("\n📌 Test 4: Column Stats (Revenue)")
        col_stats = get_column_stats(df, "Revenue")
        if col_stats['success']:
            cs = col_stats['stats']
            print(f"  Mean: ₹{cs['mean']:,.2f}")
            print(f"  Median: ₹{cs['median']:,.2f}")
            print(f"  Min: ₹{cs['min']:,.2f}")
            print(f"  Max: ₹{cs['max']:,.2f}")
        
        # Test 5: Filter
        print("\n📌 Test 5: Filter (Region == North)")
        filter_result = filter_data(df, "Region", "==", "North")
        print(f"  {filter_result['message']}")
        
        # Test 6: Value Counts
        print("\n📌 Test 6: Value Counts (Product)")
        vc = get_value_counts(df, "Product")
        if vc['success']:
            for product, count in vc['value_counts'].items():
                print(f"  {product}: {count}")
    
    print("\n" + "="*55)
    print("  ✅ All Data Tools Tests Passed!")
    print("="*55 + "\n")

