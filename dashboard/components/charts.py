"""
MedScribe Dashboard — Modular Plotly Chart Helpers
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

PLOTLY_DARK_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#0f172a",
    font=dict(family="Inter", color="#94a3b8"),
    xaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155"),
    yaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155"),
)

def build_horizontal_bar(data: list, title: str, color_scale: list):
    if not data:
        return None
    df = pd.DataFrame(data)
    fig = px.bar(
        df,
        x="count",
        y="name",
        orientation="h",
        color="count",
        color_continuous_scale=color_scale,
        labels={"name": "", "count": "Occurrences"},
    )
    fig.update_layout(**PLOTLY_DARK_THEME, coloraxis_showscale=False, height=350, margin=dict(l=0, r=20, t=20, b=20))
    fig.update_traces(marker_line_width=0)
    return fig
