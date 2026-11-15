# Contributing to InsightFlow

First off, thank you for considering contributing to InsightFlow! We welcome contributions to make autonomous multi-agent data research safer, faster, and more robust.

---

## 🛠️ Development Setup

1. **Fork and Clone the Repository:**
   ```bash
   git clone https://github.com/<your-username>/insightflow.git
   cd insightflow
   ```

2. **Create and Activate Virtual Environment:**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables:**
   ```bash
   cp .env.example .env
   ```
   Add your `GEMINI_API_KEY` inside `.env`.

5. **Verify Installation:**
   ```bash
   python verify_setup.py
   pytest -v tests/
   ```

---

## 📐 Engineering Principles

When adding or modifying agents and tools:
- **Zero Arbitrary Execution:** Never use `eval()` or `exec()` for LLM-generated code. All tools must be statically defined with strict Pydantic schemas.
- **Auditable Claims:** Any numerical insight produced must pass through the `EvaluationAgent` for ground-truth verification.
- **Deterministic Fallback:** Ensure agents handle API rate limits and network degradation gracefully without hanging.
- **Clean Commits:** Write semantic git commit messages (e.g. `feat(agent): ...`, `fix(tools): ...`, `test: ...`).

---

## 🚀 Submitting a Pull Request

1. Create a feature branch: `git checkout -b feature/agent-enhancement`
2. Run automated test suite: `pytest -v tests/`
3. Commit your changes: `git commit -m "feat(agent): add clustering capability"`
4. Push to branch: `git push origin feature/agent-enhancement`
5. Open a Pull Request on GitHub.
