import sqlite3
import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_anomalies():

    connection = sqlite3.connect("bills.db")

    data = pd.read_sql_query(
        "SELECT id, total_amount FROM bills WHERE total_amount IS NOT NULL",
        connection
    )

    connection.close()

    data["total_amount"] = pd.to_numeric(
        data["total_amount"],
        errors="coerce"
    )

    data = data.dropna(subset=["total_amount"])

    if len(data) < 2:
        data["anomaly"] = []
        return data

    model = IsolationForest(
        contamination=0.2,
        n_estimators=200,
        random_state=42
    )

    data["anomaly"] = model.fit_predict(
        data[["total_amount"]]
    )

    return data