import pandas as pd
import joblib

# Load model + encoders
model = joblib.load("ml_model/eco_model.pkl")
material_enc = joblib.load("ml_model/encoders/material_encoder.pkl")
transport_enc = joblib.load("ml_model/encoders/transport_encoder.pkl")

# Load your dummy data
df = pd.read_csv("ml_model/dummy_data.csv")

# Encode and predict
df["material_enc"] = material_enc.transform(df["material"])
df["transport_enc"] = transport_enc.transform(df["transport"])

X = df[["material_enc", "weight", "transport_enc"]]
y_pred = model.predict(X)

print("✅ Predictions:")
print(y_pred)
