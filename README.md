# AITXHackathon2025

**Agentic AI for Healthcare Provider Matching**

This repository contains two main components:
- **agents_mobile_app/** — Mobile application interface for interacting with the AI agent system.
- **agents_cli/** — Command-line interface for running simple tests or lightweight agent interactions.

Both parts share the same Python environment and dependencies.

---

## 🧠 Project Overview

The system implements an **agentic AI pipeline** for intelligent healthcare provider matching.  
It integrates deterministic logic (data filtering and scoring) with a **large language model reasoning layer** built on **NVIDIA Nemotron**, enabling contextual, explainable recommendations.

---

### 🧩 Architecture Overview

1. **Data Layer**
   - The backend ingests structured healthcare provider data (e.g., NPI information, insurance coverage, specialty, and location).
   - Providers are stored in lightweight model classes defined in `models.py`.
   - The CLI and mobile interfaces both interact with this shared data abstraction.

2. **Scoring Engine**
   - Implemented in `scoring.py`, the scoring engine applies deterministic heuristics such as:
     - Insurance compatibility (currently supports **BCBS** only)
     - Geographic distance or service region
     - Specialty and expertise match
     - Provider capacity and network participation
   - The scoring step produces an initial ranked list of potential providers.

3. **Reasoning Layer (LLM Agent)**
   - The **NVIDIA Nemotron** model is used as a reasoning agent that refines or explains provider matches.
   - It receives structured inputs (patient needs, insurance, and scores) and generates contextual reasoning such as:
     - “Why this provider is a better match”
     - “Alternative recommendations given limited availability”
   - The agent operates as a reasoning-on-top layer, not a replacement for the scoring engine.

4. **Execution Interfaces**
   - **CLI (`agents_cli`)**: lightweight entry point for backend testing and model debugging.
     - Run via `python3 main.py`
     - Useful for evaluating matching quality and logging agent reasoning traces.
   - **Mobile App (`agents_mobile_app`)**: UI layer that sends requests to the same backend agent logic.
     - Integrates user input capture and displays ranked providers and rationales.

5. **Interaction Flow**
   - User → CLI/Mobile Input → `models.py` (data structures) → `scoring.py` (initial filtering) → **Nemotron agent** (contextual reasoning) → Final ranked list + reasoning summary.

---

### ⚙️ Implementation Notes

- The agent layer is decoupled via an abstract reasoning API, allowing replacement or fine-tuning of the underlying LLM model.
- Designed for future multi-insurer support (extend scoring rules and add insurance metadata).
- All components share the same environment and dependency set (`requirements.txt`).
- Logging and traceability are implemented in `test.py` to validate scoring stability and reasoning consistency.

---

### 🧱 Example Pipeline

```bash
# Run provider matching and reasoning
python3 main.py --input sample_patient.json

---

## ⚙️ Setup Instructions

### (First-time setup only)
```bash
# 1. Create a virtual environment
python -m venv venv

# 2. Activate the virtual environment
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Running the Project

If you want to run the **mobile app**, navigate to:
```bash
cd agents_mobile_app
# Follow the setup instructions inside this folder
```

If you want to run the **CLI interface** for quick results:
```bash
cd agents_cli
python main.py
```

---

## 👥 Contributors
- **Fatemeh Doudi**
- **Brad Hall**

---

## 📜 License
MIT License — open for research and educational use.

