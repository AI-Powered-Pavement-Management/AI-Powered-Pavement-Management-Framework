from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from agent.graph import run_agent

app = FastAPI(title="PCI Prediction API")

# Allow the web/app (different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # fine for local prototype
    allow_methods=["*"],
    allow_headers=["*"],
)

# The 11 inputs the form sends. All optional (some columns are often empty).
class PavementInput(BaseModel):
    Age: Optional[float] = None
    TTh: Optional[float] = None
    ATh: Optional[float] = None
    TAP: Optional[float] = None
    MAAT: Optional[float] = None
    FI: Optional[float] = None
    MIRI: Optional[float] = None
    PI: Optional[float] = None
    AADTT: Optional[float] = None
    Sieve200_subgrade: Optional[float] = None
    Sieve200_base: Optional[float] = None

@app.get("/")
def home():
    return {"status": "API is running"}

@app.post("/predict")
def predict(data: PavementInput):
    input_dict = data.dict()
    try:
        result = run_agent(input_dict)
    except Exception as e:
        return {"pci": None, "band": "Error", "factors": [], "note": f"Agent failed: {str(e)}"}
    return result