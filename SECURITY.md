# Security Policy

## 🔒 Safe Tool Execution Guarantee
InsightFlow is designed from the ground up to prevent **Remote Code Execution (RCE)** and **Arbitrary Execution Vulnerabilities**:
- LLM outputs are constrained strictly to predefined Python functions (`tools/data_tools.py`, `tools/stats_tools.py`).
- Inputs to tools are strictly validated using Pydantic schemas.
- Mathematical operations are executed inside sandboxed Pandas runtime environments, eliminating code injection vectors.

---

## 🔑 Credential Safety
- API keys (such as `GEMINI_API_KEY`) are loaded dynamically through `python-dotenv` and are never committed to version control.
- Both `.env` and SQLite database files (`memory/*.db`) are permanently ignored in `.gitignore`.

---

## 🚨 Reporting a Vulnerability
If you discover a security issue or potential exploit within InsightFlow:
1. Please do NOT open a public GitHub issue.
2. Email the maintainers directly with reproduction details and logs.
3. We will respond within 48 hours to acknowledge and issue a patch.
