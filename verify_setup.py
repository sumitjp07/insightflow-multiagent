"""
verify_setup.py – Phase 1 Setup Verification
=============================================
Ye script check karti hai ki sab kuch sahi install hua hai.
Run karo: python verify_setup.py
"""

import sys
import os
from pathlib import Path

def print_header(text):
    print("\n" + "="*55)
    print(f"  {text}")
    print("="*55)

def check(label, condition, fix_hint=""):
    if condition:
        print(f"  ✅  {label}")
        return True
    else:
        print(f"  ❌  {label}")
        if fix_hint:
            print(f"       Fix: {fix_hint}")
        return False

results = []

# ── 1. Python Version ──────────────────────────────────────
print_header("1. Python Version Check")
major, minor = sys.version_info[:2]
results.append(check(
    f"Python {major}.{minor} (need 3.11+)",
    major == 3 and minor >= 11,
    "Install Python 3.11 from python.org"
))

# ── 2. Project Structure ───────────────────────────────────
print_header("2. Project Folder Structure")
base = Path(__file__).parent
required_dirs = ["agents","tools","workflow","memory","evaluation","tests","sample_data","reports","docs"]
for d in required_dirs:
    results.append(check(
        f"Folder: {d}/",
        (base / d).exists(),
        f"Run: mkdir {d}"
    ))

# ── 3. Required Files ──────────────────────────────────────
print_header("3. Required Files")
required_files = [
    "config.py",
    ".env.example",
    ".gitignore",
    "requirements.txt",
    "sample_data/sales_data.csv",
    "sample_data/employee_data.csv",
]
for f in required_files:
    results.append(check(f"File: {f}", (base / f).exists()))

# ── 4. .env File Check ─────────────────────────────────────
print_header("4. Environment File (.env)")
env_path = base / ".env"
env_exists = env_path.exists()
results.append(check(
    ".env file exists",
    env_exists,
    "Copy .env.example to .env, then add your GEMINI_API_KEY"
))
if env_exists:
    content = env_path.read_text()
    key_set = "your_gemini_api_key_here" not in content and "GEMINI_API_KEY=" in content
    results.append(check(
        "GEMINI_API_KEY is set (not placeholder)",
        key_set,
        "Open .env and replace 'your_gemini_api_key_here' with your actual key"
    ))

# ── 5. Package Imports ─────────────────────────────────────
print_header("5. Python Package Availability")
packages_to_check = [
    ("pandas",        "pandas"),
    ("numpy",         "numpy"),
    ("plotly",        "plotly"),
    ("streamlit",     "streamlit"),
    ("dotenv",        "python-dotenv"),
    ("reportlab",     "reportlab"),
    ("langchain",     "langchain"),
    ("langgraph",     "langgraph"),
    ("google.generativeai", "google-generativeai"),
    ("pydantic",      "pydantic"),
    ("openpyxl",      "openpyxl"),
    ("pytest",        "pytest"),
]

for module, pkg_name in packages_to_check:
    try:
        __import__(module)
        results.append(check(f"Package: {pkg_name}", True))
    except ImportError:
        results.append(check(
            f"Package: {pkg_name}",
            False,
            f"Run: pip install {pkg_name}"
        ))

# ── 6. Sample Data Quick Load ──────────────────────────────
print_header("6. Sample Data Verification")
try:
    import pandas as pd
    sales = pd.read_csv(base / "sample_data" / "sales_data.csv")
    emp   = pd.read_csv(base / "sample_data" / "employee_data.csv")
    results.append(check(f"sales_data.csv loaded ({len(sales)} rows, {len(sales.columns)} cols)", True))
    results.append(check(f"employee_data.csv loaded ({len(emp)} rows, {len(emp.columns)} cols)", True))
except Exception as e:
    results.append(check(f"Sample data load failed: {e}", False))

# ── 7. Config Module ───────────────────────────────────────
print_header("7. Config Module")
try:
    import config
    summary = config.get_config_summary()
    results.append(check("config.py imports successfully", True))
    results.append(check(
        "GEMINI_API_KEY configured",
        summary.get("api_key_set", False),
        "Add GEMINI_API_KEY to your .env file"
    ))
except Exception as e:
    results.append(check(f"config.py import failed: {e}", False))

# ── Final Summary ──────────────────────────────────────────
passed = sum(results)
total  = len(results)
print_header("PHASE 1 VERIFICATION SUMMARY")
print(f"  Passed: {passed}/{total}")
if passed == total:
    print("\n  🎉 PHASE 1 COMPLETE! Sab kuch sahi hai.")
    print("  Phase 2 start karne ke liye ready ho!")
else:
    failed = total - passed
    print(f"\n  ⚠️  {failed} issues fix karo pehle.")
    print("  Upar ❌ wale items dekho aur fix hints follow karo.")
print("="*55 + "\n")

