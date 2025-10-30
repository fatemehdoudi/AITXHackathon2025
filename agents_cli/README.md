# Agents CLI

This is the command-line interface (CLI) for the **Agentic AI Healthcare Provider Matching** project.

The CLI provides a simple way to test the provider matching logic and agent reasoning without using the mobile app.  
Currently, the system supports **BCBS insurance** only.

---

## 🚀 Run the CLI

To run the CLI interface:
```bash
python3 main.py
```

This will start the LLM reasoning agent built with **NVIDIA Nemotron**, which handles provider matching and selection.

---

## 🧩 File Overview

| File | Description |
|------|--------------|
| **main.py** | Entry point for running the agent CLI. |
| **models.py** | Language models and helper functions. |
| **scoring.py** | Scoring and matching logic for providers. |
---

## 🧠 Notes
- Works only with BCBS insurance for now.
- The reasoning layer is powered by **NVIDIA Nemotron**.
- This CLI is for backend testing and debugging — it doesn’t use the mobile app UI.
