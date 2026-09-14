import pandas as pd
import numpy as np
import xgboost as xgb
import pickle
import os
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, r2_score

print("Loading dry.csv...")
df = pd.read_csv("data/dry.csv")
df.columns = df.columns.str.strip()

df["PCI"] = pd.to_numeric(df["PCI"], errors="coerce")
df = df[np.isfinite(df["PCI"])]
df = df.dropna(subset=["PCI"])

X = df.drop(columns=["PCI"])
X = X.select_dtypes(include=[np.number])
y = df["PCI"]

print(f"Features: {list(X.columns)}")
print(f"Rows: {len(X)}")

model = xgb.XGBRegressor(
    subsample=0.6, reg_lambda=5.0, reg_alpha=0,
    n_estimators=100, min_child_weight=5, max_depth=7,
    learning_rate=0.1, gamma=0.2, colsample_bytree=1.0,
    random_state=42, n_jobs=-1
)

print("\nRunning 5-fold cross-validation...")
kf = KFold(n_splits=5, shuffle=True, random_state=42)

for fold, (train_idx, test_idx) in enumerate(kf.split(X), 1):
    model.fit(X.iloc[train_idx], y.iloc[train_idx])
    y_pred = model.predict(X.iloc[test_idx])
    r2 = r2_score(y.iloc[test_idx], y_pred)
    print(f"  Fold {fold}: R2 = {r2:.4f}")

print("\nTraining final model on all data...")
model.fit(X, y)

os.makedirs("model", exist_ok=True)
save_data = {"model": model, "columns": list(X.columns)}

with open("model/model.pkl", "wb") as f:
    pickle.dump(save_data, f)

print("Model saved to model/model.pkl")
print(f"Columns saved: {list(X.columns)}")
print("\nDone! Now run: python day4_test_agent.py")