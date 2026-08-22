import os
import joblib
import numpy as np
import pandas as pd

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

holdout_path = os.path.join(
    project_root, "data", "03_raw_holdout_lhs", "lhs_500_converged.csv"
)

model_dir = os.path.join(
    project_root, "models", "01_trained_models_all_5"
)

output_path = os.path.join(
    project_root, "data", "06_physical_checks",
    "sample_predictions_vs_actual.csv"
)

df = pd.read_csv(holdout_path)

features = [
    "pressure_atm",
    "requested_vapor_fraction",
    "benzene_feed_fraction",
    "stages",
    "feed_stage_fraction",
    "reflux_ratio",
    "bottoms_fraction"
]

targets = ["x_D_benzene", "x_B_benzene", "Q_C", "Q_R"]

X = df[features]

scaler_X = joblib.load(os.path.join(model_dir, "scaler_X.pkl"))
scaler_y = joblib.load(os.path.join(model_dir, "scaler_y.pkl"))

ann = joblib.load(os.path.join(model_dir, "ann.pkl"))
poly_model = joblib.load(
    os.path.join(model_dir, "polynomial_regression.pkl")
)
poly_features = joblib.load(
    os.path.join(model_dir, "poly_features.pkl")
)

X_scaled = scaler_X.transform(X)

ann_pred = scaler_y.inverse_transform(
    ann.predict(X_scaled)
)

poly_pred = scaler_y.inverse_transform(
    poly_model.predict(poly_features.transform(X_scaled))
)

predictions = pd.DataFrame(index=df.index)
predictions["x_D_benzene"] = ann_pred[:, 0]
predictions["x_B_benzene"] = ann_pred[:, 1]
predictions["Q_C"] = poly_pred[:, 2]
predictions["Q_R"] = poly_pred[:, 3]

sample_indices = np.linspace(0, len(df) - 1, 5, dtype=int)

rows = []

for sample, idx in enumerate(sample_indices, 1):
    for target in targets:
        actual = df.loc[idx, target]
        predicted = predictions.loc[idx, target]

        rows.append({
            "Sample": sample,
            "Holdout_Row": idx,
            "Target": target,
            "Actual": actual,
            "Predicted": predicted,
            "Absolute_Error": abs(actual - predicted)
        })

result = pd.DataFrame(rows)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_csv(output_path, index=False)

print(result.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
print(f"\nSaved to: {output_path}")