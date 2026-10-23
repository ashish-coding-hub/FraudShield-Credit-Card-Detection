import os
import secrets
import joblib
import numpy as np
import pandas as pd

from flask import (
    Flask, render_template, request, make_response,
    session, redirect, url_for
)
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Set a stable secret key in the environment for production.
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "fraudshield-local-development-key-change-me"
)

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "fraudshield_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

FEATURES = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]
THRESHOLD = 0.3
MAX_CSV_ROWS = 20000
MAX_DISPLAY_ROWS = 500

# Load your existing trained model
model = joblib.load(os.path.join(BASE_DIR, "fraud_model.pkl"))

threshold_path = os.path.join(BASE_DIR, "fraud_threshold.pkl")
if os.path.exists(threshold_path):
    THRESHOLD = float(joblib.load(threshold_path))


def render_page(
    form_data=None,
    result=None,
    error=None,
    upload_error=None,
    batch_results=None,
    batch_summary=None,
    batch_filename=None,
    download_ready=False,
):
    return render_template(
        "index.html",
        features=FEATURES,
        form_data=form_data or {},
        result=result,
        error=error,
        upload_error=upload_error,
        threshold=THRESHOLD,
        max_rows=MAX_CSV_ROWS,
        batch_results=batch_results,
        batch_summary=batch_summary,
        batch_filename=batch_filename,
        download_ready=download_ready,
    )


def remove_previous_download():
    token = session.get("download_token")

    # token_hex contains only letters and digits
    if token and token.isalnum():
        path = os.path.join(DOWNLOAD_DIR, token + ".csv")
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError:
            app.logger.warning("Could not remove previous download.")


def validate_csv(uploaded_file):
    if uploaded_file is None or not uploaded_file.filename:
        raise ValueError("Please select a CSV file.")

    if not uploaded_file.filename.lower().endswith(".csv"):
        raise ValueError("Please upload a CSV file only.")

    df = pd.read_csv(uploaded_file, nrows=MAX_CSV_ROWS + 1)

    if df.empty:
        raise ValueError("The uploaded CSV is empty.")

    if len(df) > MAX_CSV_ROWS:
        raise ValueError(f"Maximum {MAX_CSV_ROWS:,} rows are allowed.")

    missing = [column for column in FEATURES if column not in df.columns]
    if missing:
        raise ValueError("Missing columns: " + ", ".join(missing))

    data = df[FEATURES].copy()

    for column in FEATURES:
        data[column] = pd.to_numeric(data[column], errors="raise")

    if not np.isfinite(data.to_numpy(dtype=float)).all():
        raise ValueError("CSV contains missing or invalid numeric values.")

    if (data["Time"] < 0).any() or (data["Amount"] < 0).any():
        raise ValueError("Time and Amount cannot be negative.")

    return data


def make_predictions(data):
    scores = model.predict_proba(data[FEATURES])[:, 1]

    output = data[FEATURES].copy()
    output["Fraud_Score_Percent"] = np.round(scores * 100, 2)
    output["Prediction"] = np.where(
        scores >= THRESHOLD,
        "Likely Fraud",
        "Looks Legitimate",
    )

    return output, scores


@app.route("/", methods=["GET", "POST"])
def index():
    form_data = {}
    result = None
    error = None

    if request.method == "POST":
        try:
            values = {}

            for feature in FEATURES:
                raw_value = request.form.get(feature, "").strip()

                if not raw_value:
                    raise ValueError(f"{feature} is required.")

                value = float(raw_value)

                if not np.isfinite(value):
                    raise ValueError(f"{feature} must be a valid number.")

                values[feature] = value
                form_data[feature] = raw_value

            if values["Time"] < 0 or values["Amount"] < 0:
                raise ValueError("Time and Amount cannot be negative.")

            data = pd.DataFrame([values], columns=FEATURES)
            probability = float(model.predict_proba(data)[0, 1])

            result = {
                "label": (
                    "Likely Fraud"
                    if probability >= THRESHOLD
                    else "Looks Legitimate"
                ),
                "score_percent": round(probability * 100, 2),
                "threshold_percent": round(THRESHOLD * 100, 2),
            }

        except (ValueError, TypeError) as exc:
            error = str(exc)
        except Exception:
            app.logger.exception("Single prediction failed")
            error = "Prediction failed. Check the model and input values."

    return render_page(form_data=form_data, result=result, error=error)


@app.route("/upload", methods=["POST"])
def upload():
    try:
        uploaded_file = request.files.get("file")
        original_name = secure_filename(
            uploaded_file.filename if uploaded_file else ""
        ) or "uploaded.csv"

        data = validate_csv(uploaded_file)
        output, scores = make_predictions(data)

        # Remove the previous CSV belonging to this browser session.
        remove_previous_download()

        # FIX: token_hex produces only letters and digits.
        # This works correctly with the alphanumeric validation in /download.
        token = secrets.token_hex(32)
        output_path = os.path.join(DOWNLOAD_DIR, token + ".csv")

        output.to_csv(output_path, index=False)
        session["download_token"] = token

        displayed_rows = output.head(MAX_DISPLAY_ROWS).to_dict(
            orient="records"
        )

        summary = {
            "total": int(len(output)),
            "fraud": int((output["Prediction"] == "Likely Fraud").sum()),
            "legitimate": int(
                (output["Prediction"] == "Looks Legitimate").sum()
            ),
            "average_score": round(float(scores.mean() * 100), 2),
            "shown": len(displayed_rows),
        }

        return render_page(
            batch_results=displayed_rows,
            batch_summary=summary,
            batch_filename=original_name,
            download_ready=True,
        )

    except (ValueError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        return render_page(upload_error=str(exc)), 400

    except Exception:
        app.logger.exception("CSV upload failed")
        return render_page(
            upload_error="CSV processing failed. Check the terminal for details."
        ), 500


@app.route("/download", methods=["GET"])
def download():
    token = session.get("download_token")

    if not token or not token.isalnum():
        return "Download session missing. Please upload the CSV again.", 400

    output_path = os.path.join(DOWNLOAD_DIR, token + ".csv")

    if not os.path.isfile(output_path):
        session.pop("download_token", None)
        return "Predictions file not found. Please upload the CSV again.", 404

    try:
        response = make_response()

        with open(output_path, "rb") as csv_file:
            response.set_data(csv_file.read())

        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = (
            'attachment; filename="fraud_predictions.csv"'
        )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"

        return response

    except OSError:
        app.logger.exception("CSV download failed")
        return "Unable to read the predictions file.", 500


@app.errorhandler(413)
def file_too_large(_error):
    return render_page(
        upload_error="CSV is larger than 5 MB. Please upload a smaller file."
    ), 413


if __name__ == "__main__":
    app.run(debug=True)