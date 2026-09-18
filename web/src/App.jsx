import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const API_URL = `${API_BASE}/predict`;
const DECISION_URL = `${API_BASE}/decision`;

const GROUPS = [
  { title: "Pavement structure", fields: [
    ["Age", "Age (years)"], ["TTh", "Total thickness TTh"],
    ["ATh", "AC thickness ATh"], ["MIRI", "Mean IRI (MIRI)"] ] },
  { title: "Climate", fields: [
    ["TAP", "Total ann. precip TAP"], ["MAAT", "Mean air temp MAAT"],
    ["FI", "Freeze index FI"] ] },
  { title: "Traffic & soil", fields: [
    ["AADTT", "Traffic AADTT"], ["PI", "Plasticity index PI"],
    ["Sieve200_subgrade", "Sieve 200 subgrade"],
    ["Sieve200_base", "Sieve 200 base/subbase"] ] },
];

function band(pci) {
  if (pci >= 70) return { label: "Good", color: "#2E7D46", bg: "#E7F1E9" };
  if (pci >= 40) return { label: "Fair", color: "#C77D12", bg: "#FBF1E1" };
  return { label: "Poor", color: "#C0392B", bg: "#F8E9E7" };
}
function priorityColor(p) {
  if (p === "High") return "#C0392B";
  if (p === "Medium") return "#C77D12";
  return "#2E7D46";
}

export default function App() {
  const [values, setValues] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [decision, setDecision] = useState(null);

  const setField = (k, v) => setValues({ ...values, [k]: v });

  const onPredict = async () => {
    setLoading(true); setError(null); setResult(null); setDecision(null);
    try {
      const payload = {};
      Object.keys(values).forEach((k) => {
        payload[k] = values[k] === "" ? null : parseFloat(values[k]);
      });
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("API returned " + res.status);
      setResult(await res.json());
    } catch (e) {
      setError("Could not reach the API. The server may be waking up — try again in a minute.");
    } finally {
      setLoading(false);
    }
  };

  const sendDecision = async (choice) => {
    setDecision(choice);
    try {
      await fetch(DECISION_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pci: result.pci, band: result.band,
          priority: result.priority, decision: choice,
        }),
      });
    } catch (e) { console.log("Could not save decision", e); }
  };

  const b = result && result.pci != null ? band(result.pci) : null;

  return (
    <div className="page">
      <div className="card">
        <h1 style={{ fontSize: 21, margin: 0 }}>Pavement condition prediction</h1>
        <p style={{ color: "#5A6672", margin: "4px 0 20px", fontSize: 14 }}>
          Enter section data, then predict
        </p>

        {GROUPS.map((g) => (
          <div key={g.title} style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: "#5A6672",
                          textTransform: "uppercase", letterSpacing: "0.05em",
                          margin: "0 0 10px" }}>{g.title}</div>
            <div className="fields">
              {g.fields.map(([key, label]) => (
                <div key={key}>
                  <label style={{ display: "block", fontSize: 12, color: "#5A6672", marginBottom: 4 }}>
                    {label}
                  </label>
                  <input className="inp" value={values[key] || ""}
                    onChange={(e) => setField(key, e.target.value)} />
                </div>
              ))}
            </div>
          </div>
        ))}

        <button className="btn-predict" onClick={onPredict} disabled={loading}>
          {loading ? "Predicting..." : "Predict PCI"}
        </button>

        {error && (
          <div style={{ marginTop: 16, padding: 12, background: "#F8E9E7",
                        color: "#C0392B", borderRadius: 8, fontSize: 14 }}>{error}</div>
        )}

        {result && b && (
          <div style={{ marginTop: 20, padding: 16, background: b.bg, borderRadius: 12 }}>
            <div className="res-head">
              <div className="score" style={{ color: b.color }}>{result.pci}</div>
              <div>
                <div style={{ fontWeight: 600, color: b.color, fontSize: 16 }}>
                  {b.label} condition
                </div>
                <div style={{ fontSize: 12, color: "#5A6672" }}>{result.note}</div>
              </div>
              <div className="decide">
                <button onClick={() => sendDecision("approved")}
                  style={{ border: "1px solid #2E7D46",
                           background: decision === "approved" ? "#2E7D46" : "#fff",
                           color: decision === "approved" ? "#fff" : "#2E7D46" }}>
                  Approve
                </button>
                <button onClick={() => sendDecision("rejected")}
                  style={{ border: "1px solid #C0392B",
                           background: decision === "rejected" ? "#C0392B" : "#fff",
                           color: decision === "rejected" ? "#fff" : "#C0392B" }}>
                  Reject
                </button>
              </div>
            </div>

            {result.factors && (
              <div style={{ marginTop: 16, borderTop: "1px solid rgba(0,0,0,0.08)", paddingTop: 14 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: "#5A6672", marginBottom: 10 }}>
                  Why — top contributing factors
                </div>
                {result.factors.map((f) => {
                  const pos = f.value >= 0;
                  const c = pos ? "#2E7D46" : "#C0392B";
                  const w = Math.min(100, Math.abs(f.value) * 4);
                  return (
                    <div className="why-row" key={f.name}>
                      <span className="why-name">{f.name}</span>
                      <div className="why-bar">
                        <div style={{ width: `${w}%`, height: "100%", background: c }} />
                      </div>
                      <span className="why-val" style={{ color: c }}>
                        {pos ? "+" : "−"}{Math.abs(f.value)}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}

            {result.recommendation && (
              <div style={{ marginTop: 16, padding: 14, background: "#EAF1F8", borderRadius: 10 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8,
                              marginBottom: 6, flexWrap: "wrap" }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: "#2E5E8C" }}>
                    Recommended action
                  </span>
                  {result.priority && (
                    <span style={{ fontSize: 11, fontWeight: 700, padding: "2px 10px",
                                   borderRadius: 99, color: "#fff",
                                   background: priorityColor(result.priority) }}>
                      {result.priority} priority
                    </span>
                  )}
                </div>
                <div style={{ fontSize: 13, lineHeight: 1.5 }}>{result.recommendation}</div>
              </div>
            )}

            {decision && (
              <div style={{ marginTop: 14, fontSize: 14, fontWeight: 600,
                            color: decision === "approved" ? "#2E7D46" : "#C0392B" }}>
                {decision === "approved"
                  ? "✓ Result approved by engineer"
                  : "✕ Result rejected by engineer"}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}