"""
config.py – InsightFlow Global Configuration
============================================
Yahan saari project settings define hain.
Koi bhi value change karni ho, sirf yahan karo.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env file load karo (project root se)
load_dotenv()

# ── Project Paths ──────────────────────────────────────────
# BASE_DIR = jahan ye config.py file hai (project root)
BASE_DIR = Path(__file__).parent

AGENTS_DIR    = BASE_DIR / "agents"
TOOLS_DIR     = BASE_DIR / "tools"
WORKFLOW_DIR  = BASE_DIR / "workflow"
MEMORY_DIR    = BASE_DIR / "memory"
EVAL_DIR      = BASE_DIR / "evaluation"
REPORTS_DIR   = BASE_DIR / "reports"
SAMPLE_DIR    = BASE_DIR / "sample_data"
DOCS_DIR      = BASE_DIR / "docs"

# Reports directory automatically create karo agar nahi hai
REPORTS_DIR.mkdir(exist_ok=True)
MEMORY_DIR.mkdir(exist_ok=True)

# ── API Keys ───────────────────────────────────────────────
# os.getenv() environment variable se padhta hai (.env file se)
# NEVER hardcode keys yahan!
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    print("⚠️  WARNING: GEMINI_API_KEY not found in .env file!")
    print("   Please copy .env.example to .env and add your API key.")

# ── LLM Settings ───────────────────────────────────────────
LLM_MODEL_NAME   = os.getenv("LLM_MODEL_NAME", "gemini-3.8-flash")
LLM_TEMPERATURE  = 0.1                   # Low = more deterministic (good for analysis)
LLM_MAX_TOKENS   = 8192
FALLBACK_TO_OFFLINE = True               # Agar API timeout ya network fail ho to deterministic fallback use karein

# ── App Settings ───────────────────────────────────────────
APP_NAME    = os.getenv("APP_NAME", "InsightFlow")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG_MODE  = os.getenv("DEBUG_MODE", "False").lower() == "true"
LOG_LEVEL   = os.getenv("LOG_LEVEL", "INFO")

# ── File Upload Settings ───────────────────────────────────
MAX_FILE_SIZE_MB    = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
ALLOWED_EXTENSIONS  = {"csv", "xlsx", "xls"}

# ── Database Settings ──────────────────────────────────────
DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "memory/insightflow.db")

# ── Agent Execution Settings ───────────────────────────────
MAX_RETRIES              = int(os.getenv("MAX_RETRIES", "3"))
EXECUTION_TIMEOUT        = int(os.getenv("EXECUTION_TIMEOUT_SECONDS", "120"))
MAX_AGENT_ITERATIONS     = 10   # Infinite loop se bachne ke liye limit

# ── Evaluation Thresholds ──────────────────────────────────
# Agar accuracy in se kam ho, evaluation fail hogi
MIN_CALCULATION_ACCURACY = 0.95   # 95%
MIN_TASK_COMPLETION_RATE = 0.90   # 90%

# ── Logging Format ─────────────────────────────────────────
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_config_summary() -> dict:
    """
    Config summary return karta hai (API key hide karke).
    Debug ke liye useful hai.
    """
    return {
        "app_name":       APP_NAME,
        "app_version":    APP_VERSION,
        "debug_mode":     DEBUG_MODE,
        "llm_model":      LLM_MODEL_NAME,
        "llm_temperature":LLM_TEMPERATURE,
        "max_retries":    MAX_RETRIES,
        "timeout":        EXECUTION_TIMEOUT,
        "api_key_set":    bool(GEMINI_API_KEY),  # Key itself nahi dikhate!
        "base_dir":       str(BASE_DIR),
        "database_path":  str(DATABASE_PATH),
    }


# ── Quick Test (direct run karo: python config.py) ─────────
if __name__ == "__main__":
    import json
    print("\n" + "="*50)
    print(f"  {APP_NAME} v{APP_VERSION} – Configuration")
    print("="*50)
    summary = get_config_summary()
    for key, value in summary.items():
        status = "✅" if value else "❌"
        print(f"  {status}  {key}: {value}")
    print("="*50 + "\n")

