from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import json
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from pandas.errors import EmptyDataError


class DataProcessorError(Exception):
    pass


class InvalidCSVError(DataProcessorError):
    pass


class EmptyCSVError(DataProcessorError):
    pass


@dataclass
class FilterCondition:
    column: str
    operator: str
    value: str


def load_csv(file_bytes: bytes) -> pd.DataFrame:
    try:
        df = pd.read_csv(BytesIO(file_bytes))
    except EmptyDataError as e:
        raise EmptyCSVError("CSV file is empty.") from e
    except Exception as e:
        raise InvalidCSVError("Unable to read CSV file.") from e

    if df is None or df.shape[0] == 0 and df.shape[1] == 0:
        raise EmptyCSVError("CSV file is empty.")

    return df


def infer_column_types(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = [c for c in df.columns if c not in numeric_cols]
    return numeric_cols, categorical_cols


def preview_table_html(df: pd.DataFrame, max_rows: int = 100) -> str:
    preview = df.head(max_rows)
    return preview.to_html(
        classes=["table", "table-sm", "table-striped", "table-hover"],
        index=False,
        border=0,
    )


def stats_table_html(df: pd.DataFrame) -> str:
    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] == 0:
        # Keep UI consistent; provide empty table.
        return (
            "<div class='text-muted'>No numeric columns found for statistics.</div>"
        )

    desc = numeric.describe().T  # count, mean, std, min, 25%, 50%, 75%, max
    desc = desc.rename(columns={"50%": "median"})
    for col in ["count", "mean", "median", "std", "min", "max"]:
        if col not in desc.columns:
            desc[col] = pd.NA

    stats = desc[["count", "mean", "median", "std", "min", "max"]].copy()
    stats.index.name = "column"
    stats = stats.reset_index()

    return stats.to_html(
        classes=["table", "table-sm", "table-striped"],
        index=False,
        border=0,
    )


def get_unique_values(
    df: pd.DataFrame, column: str, limit: int = 200
) -> List[str]:
    if column not in df.columns:
        return []

    s = df[column].dropna()
    # Convert to string for safe transport / display
    uniques = s.astype(str).unique().tolist()
    uniques = sorted(uniques)[:limit]
    return uniques


def apply_filters(df: pd.DataFrame, conditions: List[FilterCondition]) -> pd.DataFrame:
    filtered = df
    for cond in conditions:
        if cond.column not in filtered.columns:
            continue

        op = cond.operator
        raw_val = cond.value

        series = filtered[cond.column]

        if op in {"eq", "neq"}:
            mask = series.astype(str) == str(raw_val)
            if op == "neq":
                mask = ~mask
            filtered = filtered[mask]
            continue

        if op in {"contains", "startswith", "endswith"}:
            s = series.astype(str)
            if op == "contains":
                mask = s.str.contains(str(raw_val), na=False, case=False)
            elif op == "startswith":
                mask = s.str.startswith(str(raw_val), na=False)
            else:
                mask = s.str.endswith(str(raw_val), na=False)
            filtered = filtered[mask]
            continue

        if op in {"gt", "gte", "lt", "lte"}:
            # Numeric comparisons; if conversion fails, raise a clear error.
            try:
                val = float(raw_val)
            except Exception as e:
                raise DataProcessorError(
                    f"Filter value '{raw_val}' is not numeric for operator '{op}'."
                ) from e

            numeric_series = pd.to_numeric(series, errors="coerce")
            if op == "gt":
                mask = numeric_series > val
            elif op == "gte":
                mask = numeric_series >= val
            elif op == "lt":
                mask = numeric_series < val
            else:
                mask = numeric_series <= val
            filtered = filtered[mask.fillna(False)]
            continue

    return filtered


def _plotly_fig_to_dict(fig: go.Figure) -> Dict[str, Any]:
    # Plotly figures can contain numpy arrays which Flask/Jinja JSON encoders won't serialize.
    # Round-trip via Plotly's JSON encoder to ensure a pure JSON-compatible structure.
    return json.loads(pio.to_json(fig))


def make_histogram(df: pd.DataFrame, column: Optional[str]) -> Dict[str, Any]:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        return {}

    col = column if column in numeric_cols else numeric_cols[0]
    fig = px.histogram(df, x=col, nbins=30, title=f"Histogram: {col}")
    fig.update_layout(margin=dict(l=30, r=30, t=50, b=30), height=420)
    return _plotly_fig_to_dict(fig)


def make_bar_chart(df: pd.DataFrame, column: Optional[str]) -> Dict[str, Any]:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = [c for c in df.columns if c not in numeric_cols]
    if not categorical_cols:
        return {}

    col = column if column in categorical_cols else categorical_cols[0]

    vc = df[col].astype(str).value_counts().head(20).reset_index()
    vc.columns = [col, "count"]
    fig = px.bar(vc, x=col, y="count", title=f"Top Values: {col}")
    fig.update_layout(margin=dict(l=30, r=30, t=50, b=30), height=420)
    fig.update_xaxes(tickangle=45)
    return _plotly_fig_to_dict(fig)


def make_corr_heatmap(df: pd.DataFrame) -> Dict[str, Any]:
    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        return {}

    corr = numeric.corr(numeric_only=True)
    fig = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(),
            y=corr.index.tolist(),
            colorscale="RdBu",
            zmin=-1,
            zmax=1,
            colorbar=dict(title="corr"),
        )
    )
    fig.update_layout(title="Correlation Heatmap", height=520, margin=dict(l=60, r=30, t=50, b=60))
    return _plotly_fig_to_dict(fig)
