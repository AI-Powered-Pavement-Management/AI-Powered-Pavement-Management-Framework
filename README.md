# AI-Powered Pavement Management Framework

Predicts Pavement Condition Index (PCI) from pavement, climate and traffic data using
XGBoost, explains each prediction with SHAP, and wraps the whole thing in a LangGraph
agentic workflow with a human approve/reject step.

## What's in here

| Folder | Contents |
|---|---|
| `agent/` | FastAPI API (`api.py`) + LangGraph agent (`graph.py`, `nodes.py`) |
| `model/` | Trained XGBoost model (`model.pkl`) |
| `web/` | React web interface (Vite) |
| `app/` | React Native mobile interface (Expo SDK 57) |
| `data/` | Development dataset (`dry.csv`, LTPP-derived) |
| `docs/` | Daily artefacts and documentation |

## The 11 model inputs

Age, TTh (total thickness), ATh (asphalt thickness), TAP (annual precipitation),
MAAT (mean air temperature), FI (freeze index), MIRI (roughness), PI (plasticity index),
AADTT (truck traffic), pass Sieve 200 subgrade, pass Sieve 200 base_subbase.

Target: **PCI** (0–100).

## Model performance

R² = 0.916, RMSE ≈ 8.9 PCI points (5-fold cross-validation, 1,493 rows).

Not yet validated for spatial or temporal generalisation. This is a research prototype,
not a production decision tool.

## How to run locally

Requires Python 3.11 and Node.js 20+.

**1. API** (from project root)

py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn agent.api:app --reload --port 8000

API docs at http://127.0.0.1:8000/docs

**2. Web interface**

cd web
npm install
npm run dev

Opens at http://localhost:5173

**3. Mobile interface** (optional)

cd app
npm install
npx expo start --web

Opens at http://localhost:8081

## API

`POST /predict` — send the 11 inputs (nulls allowed), returns:
```json
{ "pci": 59.2, "band": "Fair", "factors": [...], "note": "...",
  "recommendation": "...", "priority": "Medium" }
```

`POST /decision` — records the engineer's approve/reject decision.

## Notes

- `model/model.pkl` is force-added past `.gitignore` (`*.pkl`). Do not remove it —
  the agent needs it.
- Missing values are handled natively by XGBoost; four columns in the dataset are
  ~88–90% empty.
- The API has no authentication. Anyone with the URL can call `/predict`.

## Team

Student A — ML, SHAP, LangGraph agent
Student B — API, web and mobile interfaces, integration