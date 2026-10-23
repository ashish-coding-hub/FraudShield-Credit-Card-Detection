import pandas as pd
import joblib

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    average_precision_score,
    roc_auc_score
)

# 1. Load dataset
df = pd.read_csv("creditcard.csv")

# 2. Features and target
X = df.drop("Class", axis=1)
y = df["Class"]

# 3. Train-test split
x_train, x_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 4. Final Random Forest model
rf_final =RandomForestClassifier( n_estimators=100,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)
# 5. Cross-validation on training data 

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

cv_scores = cross_val_score(
    rf_final,
    x_train,
    y_train,
    cv=cv,
    scoring="average_precision",
    n_jobs=1
)

print("CV PR-AUC Scores:", cv_scores)
print("Mean CV PR-AUC:", cv_scores.mean())

# 6. Train final model on full training set
rf_final.fit(x_train, y_train)

# 7. Fixed threshold
threshold = 0.3

# 8. Test evaluation
test_scores = rf_final.predict_proba(x_test)[:, 1]
y_test_pred=(test_scores>=threshold).astype(int)
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_test_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_test_pred, zero_division=0))

print("Test PR-AUC:", average_precision_score(y_test, test_scores))
print("Test ROC-AUC:", roc_auc_score(y_test, test_scores))

# 9. Save final model and threshold
# 9. Save final model, features and threshold
joblib.dump(rf_final, "fraud_model.pkl", compress=3)
joblib.dump(list(X.columns), "fraud_features.pkl")
joblib.dump(threshold, "fraud_threshold.pkl")

print("\nFinal Random Forest model saved!")
print("Threshold saved:", threshold)
