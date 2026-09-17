import requests, sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"

sample = {
    "Age": 12, "TTh": 160, "ATh": 76, "TAP": 900, "MAAT": 14,
    "FI": 30, "MIRI": 1.4, "PI": None, "AADTT": None,
    "Sieve200_subgrade": None, "Sieve200_base": None
}

r = requests.post(f"{BASE}/predict", json=sample, timeout=60)
r.raise_for_status()
data = r.json()

assert data.get("pci") is not None, f"No PCI returned: {data}"
assert 0 <= data["pci"] <= 100, f"PCI out of range: {data['pci']}"
assert data.get("factors"), "No SHAP factors returned"
assert data.get("recommendation"), "No recommendation returned"

print(f"OK  PCI={data['pci']}  band={data['band']}  priority={data['priority']}")