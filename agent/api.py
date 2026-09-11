from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

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
    # FAKE hard-coded answer for now. Student A's model replaces this on Day 6.
    return {
        "pci": 78,
        "band": "Good",
        "factors": [
            {"name": "Low IRI (smooth)", "value": 9.1},
            {"name": "Thick AC layer", "value": 5.4},
            {"name": "Age of section", "value": -6.2},
        ],
        "note": "Fake result — real model connects on Day 6",
    }