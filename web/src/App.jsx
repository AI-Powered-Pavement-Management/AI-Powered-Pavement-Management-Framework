import { useState } from "react";

const API_URL = "http://127.0.0.1:8000/predict";

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

const S = {
  page: { minHeight: "100vh", padding: "40px 24px" },
  card: { maxWidth: 880, margin: "0 auto", background: "#fff",
          border: "1px solid #E4E7E4", borderRadius: 14, padding: "28px 32px" },
  h1: { fontSize: 22, margin: 0 },
  sub: { color: "#5A6672", margin: "4px 0 20px" },
  group: { marginBottom: 20 },
  gTitle: { fontSize: 12, fontWeight: 600, color: "#5A6672",
            textTransform: "uppercase", letterSpacing: "0.05em", margin: "0 0 10px" },
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: 12 },
  label: { display: "block", fontSize: 12, color: "#5A6672", marginBottom: 4 },
  input: { width: "100%", height: 38, padding: "0 11px",
           border: "1px solid #D4D8D4", borderRadius: 8, fontSize: 14, background: "#FAFBFA" },
  predict: { width: "100%", height: 44, marginTop: 8, background: "#2E5E8C",
             color: "#fff", border: "none", borderRadius: 9, fontSize: 15,
             fontWeight: 600, cursor: "pointer" },
};

export default function App() {
  const [values, setValues] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [decision, setDecision] = useState(null);

  const setField = (k, v) => setValues({ ...values, [k]: v });

  const onPredict = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setDecision(null);
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
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError("Could not reach the API. Is it running on port 8000?");
    } finally {
      setLoading(false);
    }
  };

  const b = result ? band(result.pci) : null;

  return (
    <div style={S.page}>
      <div style={S.card}>
        <h1 style={S.h1}>Pavement condition prediction</h1>
        <p style={S.sub}>Enter section data, then predict</p>

        {GROUPS.map((g) => (
          <div key={g.title} style={S.group}>
            <div style={S.gTitle}>{g.title}</div>
            <div style={S.grid}>
              {g.fields.map(([key, label]) => (
                <div key={key}>
                  <label style={S.label}>{label}</label>
                  <input style={S.input} value={values[key] || ""}
                    onChange={(e) => setField(key, e.target.value)} />
                </div>
              ))}
            </div>
          </div>
        ))}

        <button style={S.predict} onClick={onPredict} disabled={loading}>
          {loading ? "Predicting..." : "Predict PCI"}
        </button>

        {error && (
          <div style={{ marginTop: 16, padding: 12, background: "#F8E9E7",
                        color: "#C0392B", borderRadius: 8, fontSize: 14 }}>{error}</div>
        )}

        {result && (
          <div style={{ marginTop: 20, padding: 18, background: b.bg, borderRadius: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <div style={{ fontSize: 36, fontWeight: 700, color: b.color }}>{result.pci}</div>
              <div>
                <div style={{ fontWeight: 600, color: b.color }}>{b.label} condition</div>
                <div style={{ fontSize: 12, color: "#5A6672" }}>{result.note}</div>
              </div>
              <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
                <button
                  onClick={() => setDecision("approved")}
                  style={{ height: 38, padding: "0 16px",
                           border: decision === "approved" ? "2px solid #2E7D46" : "1px solid #2E7D46",
                           background: decision === "approved" ? "#2E7D46" : "#fff",
                           color: decision === "approved" ? "#fff" : "#2E7D46",
                           borderRadius: 8, cursor: "pointer", fontWeight: 600 }}>
                  Approve
                </button>
                <button
                  onClick={() => setDecision("rejected")}
                  style={{ height: 38, padding: "0 16px",
                           border: decision === "rejected" ? "2px solid #C0392B" : "1px solid #C0392B",
                           background: decision === "rejected" ? "#C0392B" : "#fff",
                           color: decision === "rejected" ? "#fff" : "#C0392B",
                           borderRadius: 8, cursor: "pointer", fontWeight: 600 }}>
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
                  const w = Math.min(100, Math.abs(f.value) * 8);
                  return (
                    <div key={f.name} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                      <span style={{ fontSize: 12, width: 140, color: "#5A6672" }}>{f.name}</span>
                      <div style={{ flex: 1, height: 14, background: "#fff",
                                    border: "1px solid #E4E7E4", borderRadius: 5, overflow: "hidden" }}>
                        <div style={{ width: `${w}%`, height: "100%", background: c }} />
                      </div>
                      <span style={{ fontSize: 12, fontWeight: 600, color: c, width: 44, textAlign: "right" }}>
                        {pos ? "+" : "−"}{Math.abs(f.value)}
                      </span>
                    </div>
                  );
                })}
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