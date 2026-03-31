"""
Plotly chart functions for the banking sector dashboard.
Reuses the existing theme system from dashboard.charts (COLORS, set_theme).
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Import shared theme from existing dashboard
from dashboard.charts import COLORS, _base_layout


# ── Helpers ──────────────────────────────────────────────────────────

def _fmt_rsd(val, suffix=""):
    """Format large RSD thousands values into readable form."""
    if abs(val) >= 1e9:
        return f"{val/1e9:,.1f}B{suffix}"
    if abs(val) >= 1e6:
        return f"{val/1e6:,.0f}M{suffix}"
    if abs(val) >= 1e3:
        return f"{val/1e3:,.0f}K{suffix}"
    return f"{val:,.0f}{suffix}"


# ── Ranking bar chart ────────────────────────────────────────────────

def ranking_bar(df, col, title, selected_bank=None, fmt_func=None, n_show=19):
    """Horizontal bar chart ranking banks by a column.
    df must have columns: Bank, <col>.
    """
    d = df.nlargest(n_show, col).sort_values(col, ascending=True)
    colors = []
    for b in d["Bank"]:
        if b == selected_bank:
            colors.append(COLORS["cyan"])
        else:
            colors.append(COLORS["muted"])

    texts = [fmt_func(v) if fmt_func else f"{v:,.0f}" for v in d[col]]

    fig = go.Figure(go.Bar(
        y=d["Bank"], x=d[col],
        orientation="h",
        marker=dict(color=colors, cornerradius=3),
        text=texts,
        textposition="outside",
        textfont=dict(size=10, color=COLORS["dim"]),
        hovertemplate="%{y}: <b>%{x:,.0f}</b><extra></extra>",
    ))
    layout = _base_layout(title, height=max(360, n_show * 24), show_legend=False)
    fig.update_layout(**layout)
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(tickfont=dict(size=11, color=COLORS["light"])),
        margin=dict(l=120, r=60, t=56, b=24),
    )
    return fig


# ── Market share stacked bar ────────────────────────────────────────

def market_share_stacked(ms_df, title, selected_bank=None, top_n=8):
    """Stacked bar: market share over time, top_n + Other."""
    # Identify top banks by latest share
    latest_ql = ms_df["DateLabel"].max()
    latest = ms_df[ms_df["DateLabel"] == latest_ql]
    top_banks = latest.nlargest(top_n, "share")["Bank"].tolist()

    # Group others
    d = ms_df.copy()
    d["BankGroup"] = d["Bank"].where(d["Bank"].isin(top_banks), "Other")
    grp = d.groupby(["DateLabel", "BankGroup"])["share"].sum().reset_index()

    fig = go.Figure()
    order = top_banks + (["Other"] if "Other" in grp["BankGroup"].values else [])

    palette = [
        COLORS["cyan"], COLORS["purple"], COLORS["teal"], COLORS["gold"],
        COLORS["orange"], COLORS["blue"], COLORS["pink"], COLORS["red"],
        COLORS["muted"],
    ]

    for i, bank in enumerate(order):
        sub = grp[grp["BankGroup"] == bank].sort_values("DateLabel")
        color = palette[i % len(palette)]
        if bank == selected_bank:
            color = COLORS["cyan"]
        fig.add_trace(go.Bar(
            x=sub["DateLabel"], y=sub["share"],
            name=bank,
            marker=dict(color=color, cornerradius=2),
            opacity=0.9 if bank != "Other" else 0.5,
            hovertemplate=f"{bank}: " + "<b>%{y:.1%}</b><extra></extra>",
        ))

    layout = _base_layout(title, height=420, show_legend=True)
    fig.update_layout(**layout)
    fig.update_layout(
        barmode="stack",
        yaxis=dict(tickformat=".0%"),
        yaxis_title=dict(text="Market Share", font=dict(size=12, color=COLORS["dim"])),
        legend=dict(
            orientation="h", yanchor="top", y=-0.15,
            xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["muted"]),
        ),
        margin=dict(l=56, r=24, t=56, b=100),
    )
    return fig


# ── Trend line chart ─────────────────────────────────────────────────

def trend_line(df, bank, col, title, sector_df=None, fmt_pct=False):
    """Line chart: bank vs sector for a metric over time."""
    bank_d = df[df["Bank"] == bank].sort_values("DateLabel")

    fig = go.Figure()
    y_bank = bank_d[col]
    fig.add_trace(go.Scatter(
        x=bank_d["DateLabel"], y=y_bank,
        name=bank, mode="lines+markers",
        line=dict(color=COLORS["cyan"], width=2.5, shape="spline"),
        marker=dict(size=5, color=COLORS["cyan"],
                    line=dict(width=2, color=COLORS["bg"])),
        hovertemplate="%{x}: <b>%{y:.2%}</b><extra></extra>" if fmt_pct
        else "%{x}: <b>%{y:,.0f}</b><extra></extra>",
    ))

    if sector_df is not None:
        sec = sector_df.sort_values("DateLabel")
        fig.add_trace(go.Scatter(
            x=sec["DateLabel"], y=sec[col],
            name="Sector", mode="lines",
            line=dict(color=COLORS["dim"], width=2, dash="dot", shape="spline"),
            hovertemplate="%{x}: <b>%{y:.2%}</b><extra></extra>" if fmt_pct
            else "%{x}: <b>%{y:,.0f}</b><extra></extra>",
        ))

    layout = _base_layout(title, height=380)
    fig.update_layout(**layout)
    if fmt_pct:
        fig.update_layout(yaxis=dict(tickformat=".1%"))
    return fig


# ── Dual-axis bar + line ─────────────────────────────────────────────

def growth_chart(growth_df, bank, title):
    """Bar (absolute change) + line (% change) for a bank's growth."""
    d = growth_df[growth_df["Bank"] == bank].sort_values("DateLabel")
    if d.empty:
        return go.Figure().update_layout(**_base_layout(title))

    colors = [COLORS["teal"] if v >= 0 else COLORS["red"] for v in d["abs_change"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=d["DateLabel"], y=d["abs_change"],
        name="Abs. Change",
        marker=dict(color=colors, cornerradius=3),
        opacity=0.8,
        hovertemplate="Change: <b>%{y:+,.0f}</b><extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=d["DateLabel"], y=d["pct_change"],
        name="YoY %", mode="lines+markers",
        yaxis="y2",
        line=dict(color=COLORS["gold"], width=2.5, shape="spline"),
        marker=dict(size=5, color=COLORS["gold"],
                    line=dict(width=2, color=COLORS["bg"])),
        hovertemplate="YoY: <b>%{y:+.1%}</b><extra></extra>",
    ))

    layout = _base_layout(title, height=380)
    fig.update_layout(**layout)
    fig.update_layout(
        yaxis2=dict(
            title=dict(text="YoY %", font=dict(color=COLORS["gold"], size=12)),
            overlaying="y", side="right", showgrid=False,
            tickformat=".0%",
            tickfont=dict(color=COLORS["gold"], size=10),
        ),
    )
    return fig


# ── Bump / rank chart ────────────────────────────────────────────────

def rank_bump(rank_df, bank, title, n_banks=19):
    """Bump chart showing rank over time for selected bank + peers."""
    fig = go.Figure()

    # All other banks in muted
    for b in rank_df["Bank"].unique():
        sub = rank_df[rank_df["Bank"] == b].sort_values("DateLabel")
        if b == bank:
            continue
        fig.add_trace(go.Scatter(
            x=sub["DateLabel"], y=sub["rank"],
            mode="lines",
            line=dict(color=COLORS["grid_strong"], width=1),
            showlegend=False, hoverinfo="skip",
        ))

    # Selected bank highlighted
    bsub = rank_df[rank_df["Bank"] == bank].sort_values("DateLabel")
    fig.add_trace(go.Scatter(
        x=bsub["DateLabel"], y=bsub["rank"],
        name=bank, mode="lines+markers",
        line=dict(color=COLORS["cyan"], width=3, shape="spline"),
        marker=dict(size=7, color=COLORS["cyan"],
                    line=dict(width=2, color=COLORS["bg"])),
        hovertemplate=f"{bank}: Rank " + "<b>#%{y}</b><extra></extra>",
    ))

    layout = _base_layout(title, height=380)
    fig.update_layout(**layout)
    fig.update_layout(
        yaxis=dict(autorange="reversed", dtick=1,
                   title=dict(text="Rank", font=dict(size=12, color=COLORS["dim"]))),
    )
    return fig


# ── Stacked bar (balance sheet composition) ──────────────────────────

def composition_bar(snap_df, components, title, selected_bank=None):
    """Stacked horizontal bar showing % composition per bank.
    components: list of (col, label, color).
    snap_df: single-quarter data.
    """
    d = snap_df.sort_values("TA", ascending=True)

    fig = go.Figure()
    for col, label, color in components:
        vals = d[col] if col in d.columns else 0
        fig.add_trace(go.Bar(
            y=d["Bank"], x=vals,
            name=label, orientation="h",
            marker=dict(color=color, cornerradius=2),
            hovertemplate=f"{label}: " + "<b>%{x:.1%}</b><extra></extra>",
        ))

    layout = _base_layout(title, height=max(360, len(d) * 26), show_legend=True)
    fig.update_layout(**layout)
    fig.update_layout(
        barmode="stack",
        xaxis=dict(tickformat=".0%", range=[0, 1]),
        yaxis=dict(tickfont=dict(size=11, color=COLORS["light"])),
        legend=dict(
            orientation="h", yanchor="top", y=-0.08,
            xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["muted"]),
        ),
        margin=dict(l=120, r=24, t=56, b=80),
    )
    return fig


# ── Scatter / quadrant chart ─────────────────────────────────────────

def scatter_quadrant(snap_df, x_col, y_col, x_label, y_label, title,
                     selected_bank=None, size_col="TA", fmt_pct=True):
    """Scatter plot with quadrant lines at medians."""
    fig = go.Figure()

    sizes = snap_df[size_col] / snap_df[size_col].max() * 40 + 8

    colors = [COLORS["cyan"] if b == selected_bank else COLORS["purple"]
              for b in snap_df["Bank"]]
    opacities = [1.0 if b == selected_bank else 0.6 for b in snap_df["Bank"]]

    fig.add_trace(go.Scatter(
        x=snap_df[x_col], y=snap_df[y_col],
        mode="markers+text",
        marker=dict(size=sizes, color=colors, opacity=opacities,
                    line=dict(width=1, color=COLORS["bg"])),
        text=snap_df["Bank"],
        textposition="top center",
        textfont=dict(size=9, color=COLORS["muted"]),
        hovertemplate=(
            "%{text}<br>" +
            f"{x_label}: " + "<b>%{x:.1%}</b><br>" +
            f"{y_label}: " + "<b>%{y:.1%}</b><extra></extra>"
        ) if fmt_pct else (
            "%{text}<br>" +
            f"{x_label}: " + "<b>%{x:.2f}</b><br>" +
            f"{y_label}: " + "<b>%{y:.2f}</b><extra></extra>"
        ),
    ))

    # Median lines
    x_med = snap_df[x_col].median()
    y_med = snap_df[y_col].median()
    fig.add_hline(y=y_med, line_dash="dash", line_color=COLORS["dim"],
                  line_width=1, opacity=0.5)
    fig.add_vline(x=x_med, line_dash="dash", line_color=COLORS["dim"],
                  line_width=1, opacity=0.5)

    layout = _base_layout(title, height=440, show_legend=False)
    fig.update_layout(**layout)
    if fmt_pct:
        fig.update_layout(
            xaxis=dict(tickformat=".1%",
                       title=dict(text=x_label, font=dict(size=12, color=COLORS["dim"]))),
            yaxis=dict(tickformat=".1%",
                       title=dict(text=y_label, font=dict(size=12, color=COLORS["dim"]))),
        )
    return fig


# ── Concentration chart ──────────────────────────────────────────────

def concentration_chart(conc_df, title="Sector Concentration"):
    """Top-5 / Top-10 share over time."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=conc_df["DateLabel"], y=conc_df["top_share"],
        name="Top 5 Share", mode="lines+markers",
        line=dict(color=COLORS["purple"], width=2.5, shape="spline"),
        fill="tozeroy",
        fillcolor="rgba(124, 92, 252, 0.08)",
        marker=dict(size=5, color=COLORS["purple"],
                    line=dict(width=2, color=COLORS["bg"])),
        hovertemplate="%{x}: <b>%{y:.1%}</b><extra></extra>",
    ))
    fig.add_hline(y=0.5, line_dash="dash", line_color=COLORS["dim"],
                  line_width=1, opacity=0.5)

    layout = _base_layout(title, height=360)
    fig.update_layout(**layout)
    fig.update_layout(yaxis=dict(tickformat=".0%", range=[0, 1]))
    return fig


# ── Multi-bank line comparison ───────────────────────────────────────

def multi_bank_line(df, banks, col, title, fmt_pct=False):
    """Line chart comparing multiple banks on one metric."""
    palette = [
        COLORS["cyan"], COLORS["purple"], COLORS["teal"], COLORS["gold"],
        COLORS["orange"], COLORS["blue"], COLORS["pink"], COLORS["red"],
    ]
    fig = go.Figure()
    for i, bank in enumerate(banks):
        sub = df[df["Bank"] == bank].sort_values("DateLabel")
        fig.add_trace(go.Scatter(
            x=sub["DateLabel"], y=sub[col],
            name=bank, mode="lines+markers",
            line=dict(color=palette[i % len(palette)], width=2, shape="spline"),
            marker=dict(size=4),
            hovertemplate=f"{bank}: " + ("<b>%{y:.2%}</b>" if fmt_pct else "<b>%{y:,.0f}</b>") + "<extra></extra>",
        ))
    layout = _base_layout(title, height=400)
    fig.update_layout(**layout)
    if fmt_pct:
        fig.update_layout(yaxis=dict(tickformat=".1%"))
    return fig
