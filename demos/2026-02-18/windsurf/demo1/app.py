from __future__ import annotations

import os
import secrets
import uuid
from dataclasses import asdict
from typing import Dict, List, Optional

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from utils.data_processor import (
    DataProcessorError,
    EmptyCSVError,
    FilterCondition,
    InvalidCSVError,
    apply_filters,
    infer_column_types,
    load_csv,
    make_bar_chart,
    make_corr_heatmap,
    make_histogram,
    preview_table_html,
    stats_table_html,
)


MAX_UPLOAD_MB = 10

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(16))

# In-memory store: dataset_id -> {"df": pandas.DataFrame, "filtered_df": pandas.DataFrame, "filename": str}
_DATASETS: Dict[str, dict] = {}


def _get_dataset_id() -> Optional[str]:
    return session.get("dataset_id")


def _get_dataset():
    dataset_id = _get_dataset_id()
    if not dataset_id:
        return None
    return _DATASETS.get(dataset_id)


@app.errorhandler(413)
def file_too_large(_e):
    flash(f"File too large. Max size is {MAX_UPLOAD_MB}MB.", "danger")
    return redirect(url_for("index"))


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/upload")
def upload():
    if "file" not in request.files:
        flash("No file provided.", "danger")
        return redirect(url_for("index"))

    f = request.files["file"]
    if not f or not f.filename:
        flash("No file selected.", "danger")
        return redirect(url_for("index"))

    filename = f.filename
    if not filename.lower().endswith(".csv"):
        flash("Invalid file type. Only CSV files are allowed.", "danger")
        return redirect(url_for("index"))

    file_bytes = f.read()
    if not file_bytes:
        flash("Empty file.", "danger")
        return redirect(url_for("index"))

    try:
        df = load_csv(file_bytes)
    except (InvalidCSVError, EmptyCSVError) as e:
        flash(str(e), "danger")
        return redirect(url_for("index"))

    dataset_id = str(uuid.uuid4())
    session["dataset_id"] = dataset_id
    _DATASETS[dataset_id] = {"df": df, "filtered_df": df, "filename": filename}

    return redirect(url_for("dashboard"))


@app.get("/dashboard")
def dashboard():
    dataset = _get_dataset()
    if not dataset:
        flash("Please upload a CSV file first.", "warning")
        return redirect(url_for("index"))

    df = dataset["filtered_df"]
    numeric_cols, categorical_cols = infer_column_types(df)

    preview_html = preview_table_html(df)
    stats_html = stats_table_html(df)

    hist_fig = make_histogram(df, numeric_cols[0] if numeric_cols else None)
    bar_fig = make_bar_chart(df, categorical_cols[0] if categorical_cols else None)
    corr_fig = make_corr_heatmap(df)

    return render_template(
        "dashboard.html",
        filename=dataset.get("filename"),
        row_count=int(df.shape[0]),
        col_count=int(df.shape[1]),
        columns=df.columns.tolist(),
        numeric_columns=numeric_cols,
        categorical_columns=categorical_cols,
        preview_html=preview_html,
        stats_html=stats_html,
        hist_fig=hist_fig,
        bar_fig=bar_fig,
        corr_fig=corr_fig,
    )


@app.post("/api/apply_filters")
def api_apply_filters():
    dataset = _get_dataset()
    if not dataset:
        return jsonify({"error": "No dataset loaded."}), 400

    payload = request.get_json(silent=True) or {}
    conditions_payload = payload.get("conditions", [])

    conditions: List[FilterCondition] = []
    for c in conditions_payload:
        if not isinstance(c, dict):
            continue
        column = str(c.get("column", "")).strip()
        operator = str(c.get("operator", "")).strip()
        value = str(c.get("value", "")).strip()
        if not column or not operator:
            continue
        conditions.append(FilterCondition(column=column, operator=operator, value=value))

    df = dataset["df"]
    try:
        filtered_df = apply_filters(df, conditions)
    except DataProcessorError as e:
        return jsonify({"error": str(e)}), 400

    dataset["filtered_df"] = filtered_df

    numeric_cols, categorical_cols = infer_column_types(filtered_df)

    hist_col = payload.get("hist_column")
    bar_col = payload.get("bar_column")

    response = {
        "row_count": int(filtered_df.shape[0]),
        "preview_html": preview_table_html(filtered_df),
        "stats_html": stats_table_html(filtered_df),
        "hist_fig": make_histogram(filtered_df, str(hist_col) if hist_col else None),
        "bar_fig": make_bar_chart(filtered_df, str(bar_col) if bar_col else None),
        "corr_fig": make_corr_heatmap(filtered_df),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
    }

    return jsonify(response)


@app.get("/download")
def download():
    dataset = _get_dataset()
    if not dataset:
        flash("Please upload a CSV file first.", "warning")
        return redirect(url_for("index"))

    df = dataset["filtered_df"]
    filename = dataset.get("filename") or "data.csv"
    base, _ext = os.path.splitext(filename)
    out_name = f"{base}_filtered.csv"

    csv_bytes = df.to_csv(index=False).encode("utf-8")

    from io import BytesIO

    bio = BytesIO(csv_bytes)
    bio.seek(0)

    return send_file(
        bio,
        mimetype="text/csv",
        as_attachment=True,
        download_name=out_name,
    )


if __name__ == "__main__":
    app.run(debug=True)
