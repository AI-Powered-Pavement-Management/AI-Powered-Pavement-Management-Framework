import { useState } from "react";

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

function mockPredict(data) {
  let pci = 100;
  pci -= (parseFloat(data.Age) || 0) * 1.5;
  pci -= (parseFloat(data.MIRI) || 0) * 8;
  return Math.max(0, Math.min(100, Math.round(pci)));
}
function band(pci) {
  if (pci >= 70) return { label: "Good", color: "#2E7D46", bg: "#E7F1E9" };
  if (pci >= 40) return { label: "Fair", color: "#C77D12", bg: "#FBF1E1" };
  return { label: "Poor", color: "#C0392B", bg: "#F8E9E7" };
}

const S = {
  page: { minHeight: "100vh", padding: "40px 24px" },
  card: { maxWidth: 880, margin: "0 auto", background: "#fff",
          border: "1px solid #E4E7E4", borderRadius: 14, padding: "28px 32px" },
  h1: { fontSize: 22, margin: 0, textAlign: "left" },
  sub: { color: "#5A6672", margin: "4px 0 20px", textAlign: "left" },
  group: { marginBottom: 20 },
  gTitle: { fontSize: 12, fontWeight: 600, color: "#5A6672",
            textTransform: "uppercase", letterSpacing: "0.05em",
            margin: "0 0 10px", textAlign: "left" },
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(180px,1fr))", gap: 12 },
  label: { display: "block", fontSize: 12, color: "#5A6672", marginBottom: 4, textAlign: "left" },
  input: { width: "100%", height: 38, padding: "0 11px",
           border: "1px solid #D4D8D4", borderRadius: 8, fontSize: 14, background: "#FAFBFA" },
  predict: { width: "100%", height: 44, marginTop: 8, background: "#2E5E8C",
             color: "#fff", border: "none", borderRadius: 9, fontSize: 15,
             fontWeight: 600, cursor: "pointer" },
};

export default function App() {
  const [values, setValues] = useState({});
  const [result, setResult] = useState(null);
  const setField = (k, v) => setValues({ ...values, [k]: v });
  const b = result !== null ? band(result) : null;

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

        <button style={S.predict} onClick={() => setResult(mockPredict(values))}>
          Predict PCI
        </button>

        {result !== null && (
        <div style={{ marginTop: 20, padding: 18, background: b.bg, borderRadius: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ fontSize: 36, fontWeight: 700, color: b.color }}>{result}</div>
            <div>
              <div style={{ fontWeight: 600, color: b.color }}>{b.label} condition</div>
              <div style={{ fontSize: 12, color: "#5A6672" }}>Mock result — real model connects on Day 6</div>
            </div>
            <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
              <button style={{ height: 38, padding: "0 16px", border: "1px solid #2E7D46",
                              color: "#2E7D46", background: "#fff", borderRadius: 8, cursor: "pointer" }}>Approve</button>
              <button style={{ height: 38, padding: "0 16px", border: "1px solid #C0392B",
                              color: "#C0392B", background: "#fff", borderRadius: 8, cursor: "pointer" }}>Reject</button>
            </div>
          </div>

          {/* WHY section — mock SHAP factors, replaced by real API values on Day 6 */}
          <div style={{ marginTop: 16, borderTop: "1px solid rgba(0,0,0,0.08)", paddingTop: 14 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: "#5A6672", marginBottom: 10 }}>
              Why — top contributing factors
            </div>
            {[
              { name: "Low IRI (smooth)", value: 9.1 },
              { name: "Thick AC layer", value: 5.4 },
              { name: "Age of section", value: -6.2 },
            ].map((f) => {
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
        </div>
      )}
      </div>
    </div>
  );
}