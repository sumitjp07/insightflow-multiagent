-- InsightFlow SQLite Memory Schema
-- Stores session history, analysis plans, evaluation metrics, and reports

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dataset_name TEXT,
    row_count INTEGER,
    column_count INTEGER,
    user_query TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS execution_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent_name TEXT,
    action_type TEXT,
    details TEXT,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS evaluation_metrics (
    eval_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    calculation_accuracy REAL,
    evidence_coverage REAL,
    retry_count INTEGER,
    status TEXT,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_markdown TEXT,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);

