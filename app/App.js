import { useState } from "react";
import { ScrollView, View, Text, TextInput, TouchableOpacity, StyleSheet } from "react-native";

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

const WHY = [
  { name: "Low IRI (smooth)", value: 9.1 },
  { name: "Thick AC layer", value: 5.4 },
  { name: "Age of section", value: -6.2 },
];

export default function App() {
  const [values, setValues] = useState({});
  const [result, setResult] = useState(null);
  const setField = (k, v) => setValues({ ...values, [k]: v });
  const b = result !== null ? band(result) : null;

  return (
    <ScrollView
      style={styles.page}
      contentContainerStyle={{ padding: 20, paddingTop: 50, maxWidth: 480, width: "100%", alignSelf: "center" }}
    >
      <Text style={styles.h1}>Predict PCI</Text>
      <Text style={styles.sub}>Enter section data, then predict</Text>

      {GROUPS.map((g) => (
        <View key={g.title} style={{ marginBottom: 14 }}>
          <Text style={styles.gTitle}>{g.title}</Text>
          {g.fields.map(([key, label]) => (
            <View key={key} style={{ marginBottom: 8 }}>
              <Text style={styles.label}>{label}</Text>
              <TextInput
                style={styles.input}
                keyboardType="numeric"
                value={values[key] || ""}
                onChangeText={(v) => setField(key, v)}
              />
            </View>
          ))}
        </View>
      ))}

      <TouchableOpacity style={styles.btn} onPress={() => setResult(mockPredict(values))}>
        <Text style={styles.btnText}>Predict PCI</Text>
      </TouchableOpacity>

      {result !== null && (
        <View style={[styles.result, { backgroundColor: b.bg }]}>
          <Text style={[styles.score, { color: b.color }]}>{result}</Text>
          <Text style={[styles.verdict, { color: b.color }]}>{b.label} condition</Text>
          <Text style={styles.note}>Mock result — real model connects on Day 6</Text>

          {/* WHY section — mock SHAP factors, replaced by real API on Day 6 */}
          <View style={styles.why}>
            <Text style={styles.whyTitle}>Why — top contributing factors</Text>
            {WHY.map((f) => {
              const pos = f.value >= 0;
              const c = pos ? "#2E7D46" : "#C0392B";
              const w = Math.min(100, Math.abs(f.value) * 8);
              return (
                <View key={f.name} style={styles.whyRow}>
                  <Text style={styles.whyName}>{f.name}</Text>
                  <View style={styles.whyBar}>
                    <View style={{ width: `${w}%`, height: "100%", backgroundColor: c }} />
                  </View>
                  <Text style={[styles.whyVal, { color: c }]}>
                    {pos ? "+" : "−"}{Math.abs(f.value)}
                  </Text>
                </View>
              );
            })}
          </View>

          <View style={styles.decide}>
            <TouchableOpacity style={[styles.dBtn, { borderColor: "#2E7D46" }]}>
              <Text style={styles.dText}>Approve</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.dBtn, { borderColor: "#C0392B" }]}>
              <Text style={[styles.dText, { color: "#C0392B" }]}>Reject</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: "#F4F6F4" },
  h1: { fontSize: 22, fontWeight: "700", color: "#1B2430" },
  sub: { color: "#5A6672", marginBottom: 16 },
  gTitle: { fontSize: 12, fontWeight: "600", color: "#5A6672", marginBottom: 8, textTransform: "uppercase" },
  label: { fontSize: 12, color: "#5A6672", marginBottom: 3 },
  input: { height: 40, borderWidth: 1, borderColor: "#D4D8D4", borderRadius: 8,
           paddingHorizontal: 11, backgroundColor: "#fff", fontSize: 14 },
  btn: { height: 46, backgroundColor: "#2E5E8C", borderRadius: 9,
         alignItems: "center", justifyContent: "center", marginTop: 6 },
  btnText: { color: "#fff", fontSize: 15, fontWeight: "600" },

  result: { marginTop: 18, padding: 16, borderRadius: 12, alignItems: "center" },
  score: { fontSize: 40, fontWeight: "700" },
  verdict: { fontSize: 15, fontWeight: "600" },
  note: { fontSize: 11, color: "#5A6672", marginTop: 2, textAlign: "center" },

  why: { width: "100%", marginTop: 14, borderTopWidth: 1, borderTopColor: "rgba(0,0,0,0.08)", paddingTop: 12 },
  whyTitle: { fontSize: 12, fontWeight: "600", color: "#5A6672", marginBottom: 10 },
  whyRow: { flexDirection: "row", alignItems: "center", marginBottom: 8 },
  whyName: { fontSize: 12, color: "#5A6672", width: 120 },
  whyBar: { flex: 1, height: 14, backgroundColor: "#fff", borderWidth: 1, borderColor: "#E4E7E4",
            borderRadius: 5, overflow: "hidden", marginHorizontal: 8 },
  whyVal: { fontSize: 12, fontWeight: "600", width: 40, textAlign: "right" },

  decide: { flexDirection: "row", marginTop: 16, gap: 10, width: "100%" },
  dBtn: { flex: 1, minHeight: 44, borderWidth: 1, borderRadius: 8,
          alignItems: "center", justifyContent: "center", backgroundColor: "#fff", paddingHorizontal: 12 },
  dText: { color: "#2E7D46", fontWeight: "600", fontSize: 14, lineHeight: 20, textAlign: "center" },
});