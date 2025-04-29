import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import label_binarize

# === Load dataset ===
script_dir = os.path.dirname(__file__)
project_root = os.path.dirname(script_dir)
csv_path = os.path.join(script_dir, "eco_dataset.csv")
column_names = ["title", "material", "weight", "transport", "recyclability", "true_eco_score", "co2_emissions", "origin"]
df = pd.read_csv(csv_path, header=None, names=column_names, quotechar='"')

# === Clean and filter ===
valid_scores = ["A+", "A", "B", "C", "D", "E", "F"]
df = df[df["true_eco_score"].isin(valid_scores)]
df["true_eco_score"] = df["true_eco_score"].str.upper().str.strip()
df = df[df["true_eco_score"].isin(valid_scores)]
df.dropna(subset=["material", "weight", "transport", "recyclability", "origin"], inplace=True)

for col in ["material", "transport", "recyclability", "origin"]:
    df[col] = df[col].astype(str).str.strip().str.title()

# === Fallback row ===
fallback_row = {
    "title": "Fallback",
    "material": "Other",
    "weight": 0.0,
    "transport": "Land",
    "recyclability": "Medium",
    "true_eco_score": "C",
    "co2_emissions": 0.0,
    "origin": "Other"
}
df = pd.concat([df, pd.DataFrame([fallback_row])], ignore_index=True)

# === Encode features ===
material_encoder = LabelEncoder()
transport_encoder = LabelEncoder()
recycle_encoder = LabelEncoder()
label_encoder = LabelEncoder()
origin_encoder = LabelEncoder()

df["material_encoded"] = material_encoder.fit_transform(df["material"])
df["transport_encoded"] = transport_encoder.fit_transform(df["transport"])
df["recycle_encoded"] = recycle_encoder.fit_transform(df["recyclability"])
df["origin_encoded"] = origin_encoder.fit_transform(df["origin"])
df["label_encoded"] = label_encoder.fit_transform(df["true_eco_score"])

# === Train ===
X = df[["material_encoded", "weight", "transport_encoded", "recycle_encoded", "origin_encoded"]]
y = df["label_encoded"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

print("✅ Accuracy:", model.score(X_test, y_test))
print(classification_report(y_test, model.predict(X_test)))

# === Save model and encoders ===
model_dir = os.path.join(project_root, "ml_model")
encoders_dir = os.path.join(model_dir, "encoders")
os.makedirs(encoders_dir, exist_ok=True)

joblib.dump(model, os.path.join(model_dir, "eco_model.pkl"))
joblib.dump(material_encoder, os.path.join(encoders_dir, "material_encoder.pkl"))
joblib.dump(transport_encoder, os.path.join(encoders_dir, "transport_encoder.pkl"))
joblib.dump(recycle_encoder, os.path.join(encoders_dir, "recycle_encoder.pkl"))
joblib.dump(origin_encoder, os.path.join(encoders_dir, "origin_encoder.pkl"))
joblib.dump(label_encoder, os.path.join(encoders_dir, "label_encoder.pkl"))

print("✅ Model + encoders saved!")

# === Feature Importance Chart ===
importances = model.feature_importances_
feature_names = ["material", "weight", "transport", "recyclability", "origin"]

plt.figure(figsize=(6, 4))
plt.barh(feature_names, importances)
plt.title("🔍 Feature Importance")
plt.tight_layout()
plt.savefig(os.path.join(model_dir, "feature_importance.png"))
plt.close()
print("✅ Saved feature importance chart.")

# === Confusion Matrix ===
y_pred = model.predict(X_test)
cm = confusion_matrix(y_test, y_pred)
labels = label_encoder.classes_

plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
plt.xlabel("Predicted")
plt.ylabel("True Label")
plt.title("📊 Confusion Matrix")
plt.tight_layout()
plt.savefig(os.path.join(model_dir, "confusion_matrix.png"))
plt.close()
print("✅ Saved confusion matrix.")

# === ROC Curve (One-vs-Rest) ===
y_test_bin = label_binarize(y_test, classes=range(len(labels)))
y_score = model.predict_proba(X_test)

fpr = dict()
tpr = dict()
roc_auc = dict()
for i in range(len(labels)):
    fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], y_score[:, i])
    roc_auc[i] = roc_auc_score(y_test_bin[:, i], y_score[:, i])

plt.figure(figsize=(6, 5))
for i in range(len(labels)):
    plt.plot(fpr[i], tpr[i], label=f"Class {labels[i]} (AUC = {roc_auc[i]:.2f})")

plt.plot([0, 1], [0, 1], 'k--')
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("📈 ROC Curve (One-vs-Rest)")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(model_dir, "roc_curve.png"))
plt.close()
print("✅ Saved ROC curve.")
