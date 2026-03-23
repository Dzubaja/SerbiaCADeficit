"""
Plotly chart functions for the NBS dashboard.
Supports dark and light themes via set_theme().
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── Color palettes (dark & light) ────────────────────────────────

_DARK_COLORS = {
    "cyan": "#00D4FF",
    "purple": "#7C5CFC",
    "teal": "#06D6A0",
    "green": "#06D6A0",
    "red": "#FF6B8A",
    "magenta": "#FF006E",
    "gold": "#FBBF24",
    "orange": "#FB923C",
    "blue": "#3B82F6",
    "pink": "#EC4899",
    "light": "#E2E8F0",
    "muted": "#8B95A8",
    "dim": "#5A6478",
    "bg": "#060B18",
    "card": "#0F1629",
    "grid": "rgba(255, 255, 255, 0.04)",
    "grid_strong": "rgba(255, 255, 255, 0.08)",
    "hover_bg": "#0F1629",
    "hover_border": "rgba(255,255,255,0.1)",
}

_LIGHT_COLORS = {
    "cyan": "#0891B2",
    "purple": "#6D28D9",
    "teal": "#059669",
    "green": "#059669",
    "red": "#DC2626",
    "magenta": "#BE185D",
    "gold": "#D97706",
    "orange": "#EA580C",
    "blue": "#2563EB",
    "pink": "#DB2777",
    "light": "#1E293B",
    "muted": "#64748B",
    "dim": "#94A3B8",
    "bg": "#F1F5F9",
    "card": "#FFFFFF",
    "grid": "rgba(0, 0, 0, 0.06)",
    "grid_strong": "rgba(0, 0, 0, 0.12)",
    "hover_bg": "#FFFFFF",
    "hover_border": "rgba(0,0,0,0.1)",
}

# Active palette — mutated by set_theme()
COLORS = dict(_DARK_COLORS)

COMPONENT_COLORS = {
    "Goods": COLORS["red"],
    "Services": COLORS["teal"],
    "Primary Income": COLORS["orange"],
    "Secondary Income": COLORS["cyan"],
}

FA_COLORS = {
    "FA.FDI": COLORS["cyan"],
    "FA.PORTFOLIO": COLORS["purple"],
    "FA.OTHER": COLORS["orange"],
    "FA.RESERVES": COLORS["gold"],
}


def _rebuild_derived():
    """Update derived color dicts after theme change."""
    COMPONENT_COLORS.update({
        "Goods": COLORS["red"],
        "Services": COLORS["teal"],
        "Primary Income": COLORS["orange"],
        "Secondary Income": COLORS["cyan"],
    })
    FA_COLORS.update({
        "FA.FDI": COLORS["cyan"],
        "FA.PORTFOLIO": COLORS["purple"],
        "FA.OTHER": COLORS["orange"],
        "FA.RESERVES": COLORS["gold"],
    })


def set_theme(theme="dark"):
    """Switch the module's color palette between dark and light."""
    src = _DARK_COLORS if theme == "dark" else _LIGHT_COLORS
    COLORS.update(src)
    _rebuild_derived()


def _base_layout(title="", height=420, show_legend=True):
    """Standard premium dark layout for all charts."""
    return dict(
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(size=15, color=COLORS["light"], family="Inter, sans-serif"),
            x=0, xanchor="left",
            pad=dict(l=8, t=4),
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color=COLORS["muted"],
            size=11,
            family="Inter, sans-serif",
        ),
        height=height,
        margin=dict(l=56, r=24, t=96, b=48),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
            font=dict(size=11, color=COLORS["muted"]),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
        ) if show_legend else dict(visible=False),
        xaxis=dict(
            gridcolor=COLORS["grid"],
            zeroline=False,
            showline=True,
            linecolor=COLORS["grid_strong"],
            linewidth=1,
            tickfont=dict(size=11, color=COLORS["dim"]),
        ),
        yaxis=dict(
            gridcolor=COLORS["grid"],
            zeroline=True,
            zerolinecolor=COLORS["grid_strong"],
            zerolinewidth=1,
            showline=False,
            tickfont=dict(size=11, color=COLORS["dim"]),
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=COLORS["hover_bg"],
            bordercolor=COLORS["hover_border"],
            font=dict(size=12, color=COLORS["light"], family="Inter, sans-serif"),
        ),
        bargap=0.25,
    )


# ── Current Account ───────────────────────────────────────────────

def ca_trend_chart(ca_df, ca_gdp_df=None):
    """Line + bar chart: CA balance over time, optional CA/GDP line."""
    fig = go.Figure()

    # Bars with gradient-like effect (conditional colors)
    colors = [COLORS["teal"] if v >= 0 else COLORS["red"] for v in ca_df["value"]]
    opacities = [0.85 if v >= 0 else 0.85 for v in ca_df["value"]]

    fig.add_trace(go.Bar(
        x=ca_df["year"], y=ca_df["value"],
        marker=dict(
            color=colors,
            line=dict(width=0),
            cornerradius=4,
        ),
        name="CA Balance (EUR mn)",
        opacity=0.85,
        hovertemplate="%{x}: <b>%{y:,.0f}</b> EUR mn<extra></extra>",
    ))

    # CA/GDP ratio on secondary axis
    if ca_gdp_df is not None and not ca_gdp_df.empty:
        fig.add_trace(go.Scatter(
            x=ca_gdp_df["year"], y=ca_gdp_df["ca_gdp_pct"],
            mode="lines+markers", name="CA / GDP (%)",
            line=dict(color=COLORS["gold"], width=2.5, shape="spline"),
            marker=dict(size=6, color=COLORS["gold"],
                        line=dict(width=2, color=COLORS["bg"])),
            yaxis="y2",
            hovertemplate="%{x}: <b>%{y:.1f}%</b><extra></extra>",
        ))
        fig.update_layout(
            yaxis2=dict(
                title=dict(text="% of GDP",
                           font=dict(color=COLORS["gold"], size=12)),
                overlaying="y", side="right",
                gridcolor="rgba(0,0,0,0)",
                zeroline=True,
                zerolinecolor=COLORS["grid_strong"],
                tickfont=dict(color=COLORS["gold"], size=11),
            )
        )

    layout = _base_layout("Current Account Balance", height=440)
    fig.update_layout(**layout)
    fig.update_layout(yaxis_title=dict(text="EUR millions",
                      font=dict(size=12, color=COLORS["dim"])))
    return fig


def ca_components_stacked(comp_df):
    """Stacked bar chart: CA component breakdown by year."""
    fig = go.Figure()

    for component in ["Goods", "Services", "Primary Income", "Secondary Income"]:
        if component in comp_df.columns:
            fig.add_trace(go.Bar(
                x=comp_df["year"], y=comp_df[component],
                name=component,
                marker=dict(
                    color=COMPONENT_COLORS.get(component, COLORS["muted"]),
                    line=dict(width=0),
                    cornerradius=2,
                ),
                opacity=0.9,
                hovertemplate=f"{component}: " + "<b>%{y:,.0f}</b><extra></extra>",
            ))

    layout = _base_layout("CA Components Breakdown", height=440)
    fig.update_layout(**layout)
    fig.update_layout(barmode="relative",
                      yaxis_title=dict(text="EUR millions",
                      font=dict(size=12, color=COLORS["dim"])))
    return fig


def ca_waterfall(comp_df, year=None, ref_row=None):
    """Waterfall chart: CA decomposition for a specific year.

    Args:
        comp_df: Components DataFrame (year, Goods, Services, etc.)
        year: Year to show (default: latest)
        ref_row: Optional reference year row to show % change markers
    """
    if year is not None:
        row = comp_df[comp_df["year"] == year]
        if row.empty:
            row = comp_df.iloc[[-1]]
        row = row.iloc[0]
    else:
        row = comp_df.iloc[-1]
    year = int(row["year"])

    components = ["Goods", "Services", "Primary Income", "Secondary Income"]
    values = [row[c] for c in components]
    ca_val = row["Current Account"]

    fig = go.Figure(go.Waterfall(
        x=components + ["Current Account"],
        y=values + [ca_val],
        measure=["relative"] * 4 + ["total"],
        connector=dict(line=dict(color=COLORS["grid_strong"], width=1, dash="dot")),
        increasing=dict(marker=dict(color=COLORS["teal"],
                        line=dict(width=0))),
        decreasing=dict(marker=dict(color=COLORS["red"],
                        line=dict(width=0))),
        totals=dict(marker=dict(color=COLORS["cyan"],
                    line=dict(width=0))),
        textposition="outside",
        text=[f"{v:,.0f}" for v in values] + [f"{ca_val:,.0f}"],
        textfont=dict(size=11, color=COLORS["muted"],
                      family="Inter, sans-serif"),
    ))

    # % change markers relative to reference year
    if ref_row is not None:
        all_labels = components + ["Current Account"]
        all_values = values + [ca_val]
        pct_texts = []
        pct_y = []
        for i, comp in enumerate(all_labels):
            ref_val = ref_row[comp]
            cur_val = all_values[i]
            if ref_val != 0:
                pct = (cur_val - ref_val) / abs(ref_val) * 100
                pct_texts.append(f"{pct:+.0f}%")
            else:
                pct_texts.append("n/a")
            pct_y.append(cur_val)

        fig.add_trace(go.Scatter(
            x=all_labels, y=pct_y,
            mode="markers+text",
            marker=dict(size=10, color=COLORS["gold"],
                        line=dict(width=2, color=COLORS["bg"]),
                        symbol="circle"),
            text=pct_texts,
            textposition="top center",
            textfont=dict(size=10, color=COLORS["gold"],
                          family="Inter, sans-serif", weight=700),
            hovertemplate="%{x}: <b>%{text}</b> vs ref<extra></extra>",
            showlegend=False,
        ))

    show_legend = ref_row is not None
    layout = _base_layout(f"CA Waterfall ({year})",
                          height=420, show_legend=show_legend)
    fig.update_layout(**layout)
    fig.update_layout(yaxis_title=dict(text="EUR millions",
                      font=dict(size=12, color=COLORS["dim"])))
    return fig


# ── Trade ─────────────────────────────────────────────────────────

def trade_chart(trade_df):
    """Exports vs Imports bar chart with balance line."""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=trade_df["year"], y=trade_df["Exports"],
        name="Exports",
        marker=dict(color=COLORS["teal"], line=dict(width=0),
                    cornerradius=3),
        opacity=0.85,
        hovertemplate="Exports: <b>%{y:,.0f}</b><extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=trade_df["year"], y=-trade_df["Imports"],
        name="Imports",
        marker=dict(color=COLORS["red"], line=dict(width=0),
                    cornerradius=3),
        opacity=0.85,
        hovertemplate="Imports: <b>%{customdata:,.0f}</b><extra></extra>",
        customdata=trade_df["Imports"],
    ))
    fig.add_trace(go.Scatter(
        x=trade_df["year"], y=trade_df["Balance"],
        name="Trade Balance", mode="lines+markers",
        line=dict(color=COLORS["gold"], width=2.5, shape="spline"),
        marker=dict(size=7, color=COLORS["gold"],
                    line=dict(width=2, color=COLORS["bg"])),
        hovertemplate="Balance: <b>%{y:,.0f}</b><extra></extra>",
    ))

    layout = _base_layout("Goods Trade", height=420)
    fig.update_layout(**layout)
    fig.update_layout(barmode="relative",
                      yaxis_title=dict(text="EUR millions",
                      font=dict(size=12, color=COLORS["dim"])))
    return fig


# ── Financial Account ─────────────────────────────────────────────

def fa_components_chart(fa_df):
    """Financial account components line chart."""
    fig = go.Figure()

    name_map = {
        "FA.FDI": "FDI",
        "FA.PORTFOLIO": "Portfolio",
        "FA.OTHER": "Other Investment",
        "FA.RESERVES": "Reserves",
    }

    for code, name in name_map.items():
        sub = fa_df[fa_df["indicator_code"] == code]
        if not sub.empty:
            color = FA_COLORS.get(code, COLORS["muted"])
            fig.add_trace(go.Scatter(
                x=sub["year"], y=sub["value"].abs(),
                name=name, mode="lines+markers",
                line=dict(color=color, width=2.5, shape="spline"),
                marker=dict(size=6, color=color,
                            line=dict(width=2, color=COLORS["bg"])),
                hovertemplate=f"{name}: " + "<b>%{y:,.0f}</b><extra></extra>",
            ))

    layout = _base_layout("Financial Account Components (absolute)", height=420)
    fig.update_layout(**layout)
    fig.update_layout(yaxis_title=dict(text="EUR millions",
                      font=dict(size=12, color=COLORS["dim"])))
    return fig


def fdi_coverage_chart(cov_df):
    """FDI coverage ratio: bar chart with 100% reference line."""
    fig = go.Figure()

    colors = [COLORS["teal"] if v >= 100 else COLORS["gold"]
              for v in cov_df["coverage"]]

    fig.add_trace(go.Bar(
        x=cov_df["year"], y=cov_df["coverage"],
        marker=dict(color=colors, line=dict(width=0), cornerradius=4),
        name="FDI / CA Deficit (%)",
        text=[f"{v:.0f}%" for v in cov_df["coverage"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["muted"],
                      family="Inter, sans-serif"),
        opacity=0.9,
        hovertemplate="%{x}: <b>%{y:.1f}%</b><extra></extra>",
    ))

    fig.add_hline(
        y=100, line_dash="dash", line_color=COLORS["red"],
        line_width=1.5, opacity=0.6,
        annotation_text="100% coverage",
        annotation_position="top right",
        annotation_font=dict(size=10, color=COLORS["red"]),
    )

    layout = _base_layout("FDI Coverage of CA Deficit",
                          height=420, show_legend=False)
    fig.update_layout(**layout)
    fig.update_layout(
        yaxis_title=dict(text="%", font=dict(size=12, color=COLORS["dim"])),
        yaxis_range=[0, max(cov_df["coverage"].max() * 1.15, 110)],
    )
    return fig


# ── External Position ─────────────────────────────────────────────

def fx_reserves_chart(fx_df):
    """FX reserves trend with gradient fill."""
    fig = go.Figure()

    if "Total (1 to 4)" in fx_df.columns:
        fig.add_trace(go.Scatter(
            x=fx_df["year"], y=fx_df["Total (1 to 4)"],
            name="NBS Reserves", mode="lines+markers",
            line=dict(color=COLORS["cyan"], width=2.5, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(0, 212, 255, 0.08)",
            fillgradient=dict(
                type="vertical",
                colorscale=[
                    [0.0, "rgba(0, 212, 255, 0.0)"],
                    [1.0, "rgba(0, 212, 255, 0.15)"],
                ],
            ),
            marker=dict(size=5, color=COLORS["cyan"],
                        line=dict(width=2, color=COLORS["bg"])),
            hovertemplate="NBS: <b>%{y:,.0f}</b> EUR mn<extra></extra>",
        ))
    if "Total (5+6)" in fx_df.columns:
        fig.add_trace(go.Scatter(
            x=fx_df["year"], y=fx_df["Total (5+6)"],
            name="Total (NBS + Banks)", mode="lines+markers",
            line=dict(color=COLORS["purple"], width=2, shape="spline",
                      dash="dot"),
            marker=dict(size=5, color=COLORS["purple"],
                        line=dict(width=2, color=COLORS["bg"])),
            hovertemplate="Total: <b>%{y:,.0f}</b> EUR mn<extra></extra>",
        ))

    layout = _base_layout("Foreign Exchange Reserves", height=420)
    fig.update_layout(**layout)
    fig.update_layout(yaxis_title=dict(text="EUR millions",
                      font=dict(size=12, color=COLORS["dim"])))
    return fig


def external_debt_chart(debt_df, debt_gdp_df=None):
    """Total external debt trend with gradient fill + optional debt/GDP ratio."""
    if debt_df is None or debt_df.empty:
        return go.Figure().update_layout(
            **_base_layout("External Debt (no data)"))

    fig = go.Figure()

    # Main line: total external debt (EUR mn)
    fig.add_trace(go.Scatter(
        x=debt_df["year"], y=debt_df["value"],
        name="Total External Debt", mode="lines+markers+text",
        line=dict(color=COLORS["orange"], width=2.5, shape="spline"),
        fill="tozeroy",
        fillcolor="rgba(251, 146, 60, 0.06)",
        fillgradient=dict(
            type="vertical",
            colorscale=[
                [0.0, "rgba(251, 146, 60, 0.0)"],
                [1.0, "rgba(251, 146, 60, 0.12)"],
            ],
        ),
        marker=dict(size=5, color=COLORS["orange"],
                    line=dict(width=2, color=COLORS["bg"])),
        text=[f"{v/1000:,.0f}k" if v >= 10000 else f"{v:,.0f}"
              for i, v in enumerate(debt_df["value"])],
        textposition="top center",
        textfont=dict(size=9, color=COLORS["muted"]),
        cliponaxis=False,
        hovertemplate="Debt: <b>%{y:,.0f}</b> EUR mn<extra></extra>",
    ))

    # Secondary axis: Debt / GDP %
    if debt_gdp_df is not None and not debt_gdp_df.empty:
        fig.add_trace(go.Scatter(
            x=debt_gdp_df["year"], y=debt_gdp_df["debt_gdp_pct"],
            name="Debt / GDP (%)", mode="lines+markers+text",
            line=dict(color=COLORS["cyan"], width=2.5, shape="spline"),
            marker=dict(size=6, color=COLORS["cyan"],
                        line=dict(width=2, color=COLORS["bg"])),
            text=[f"{v:.0f}%" for v in debt_gdp_df["debt_gdp_pct"]],
            textposition="bottom center",
            textfont=dict(size=9, color=COLORS["cyan"]),
            yaxis="y2",
            hovertemplate="%{x}: <b>%{y:.1f}%</b> of GDP<extra></extra>",
        ))
        fig.update_layout(
            yaxis2=dict(
                title=dict(text="% of GDP",
                           font=dict(color=COLORS["cyan"], size=12)),
                overlaying="y", side="right",
                gridcolor="rgba(0,0,0,0)",
                zeroline=False,
                tickfont=dict(color=COLORS["cyan"], size=11),
                ticksuffix="%",
            )
        )

    layout = _base_layout("Total External Debt", height=440)
    fig.update_layout(**layout)
    fig.update_layout(yaxis_title=dict(text="EUR millions",
                      font=dict(size=12, color=COLORS["dim"])))
    return fig


# ── Rankings ──────────────────────────────────────────────────────

def component_ranking_chart(rank_df):
    """Horizontal bar chart: CA components ranked by absolute contribution."""
    if rank_df.empty:
        return go.Figure()

    bar_colors = [COLORS["teal"] if v > 0 else COLORS["red"]
                  for v in rank_df["Value"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=rank_df["Component"], x=rank_df["Value"],
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0),
                    cornerradius=4),
        text=[f"{v:,.0f}" for v in rank_df["Value"]],
        textposition="outside",
        textfont=dict(size=12, color=COLORS["muted"],
                      family="Inter, sans-serif"),
        opacity=0.9,
        hovertemplate="%{y}: <b>%{x:,.0f}</b> EUR mn<extra></extra>",
    ))

    layout = _base_layout("CA Components by Value",
                          height=320, show_legend=False)
    fig.update_layout(**layout)
    fig.update_layout(
        xaxis_title=dict(text="EUR millions",
                         font=dict(size=12, color=COLORS["dim"])),
        yaxis=dict(gridcolor="rgba(0,0,0,0)",
                   tickfont=dict(size=12, color=COLORS["light"])),
    )
    return fig


def yoy_change_chart(rank_df):
    """Year-over-year change for each component."""
    if rank_df.empty or rank_df["Change"].isna().all():
        return go.Figure()

    bar_colors = [COLORS["teal"] if v > 0 else COLORS["red"]
                  for v in rank_df["Change"].fillna(0)]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=rank_df["Component"], x=rank_df["Change"],
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0),
                    cornerradius=4),
        text=[f"{v:+,.0f}" if pd.notna(v) else "n/a"
              for v in rank_df["Change"]],
        textposition="outside",
        textfont=dict(size=12, color=COLORS["muted"],
                      family="Inter, sans-serif"),
        opacity=0.9,
        hovertemplate="%{y}: <b>%{x:+,.0f}</b> EUR mn<extra></extra>",
    ))

    layout = _base_layout("Year-over-Year Change",
                          height=320, show_legend=False)
    fig.update_layout(**layout)
    fig.update_layout(
        xaxis_title=dict(text="EUR millions change",
                         font=dict(size=12, color=COLORS["dim"])),
        yaxis=dict(gridcolor="rgba(0,0,0,0)",
                   tickfont=dict(size=12, color=COLORS["light"])),
    )
    return fig


# ── Multi-year component evolution ────────────────────────────────

def component_share_chart(comp_df):
    """Stacked area: share of each component in total CA (absolute values)."""
    cols = ["Goods", "Services", "Primary Income", "Secondary Income"]
    df = comp_df[["year"] + cols].copy()

    # Fill opacity variants for each color
    fill_colors = {
        "Goods": "rgba(255, 107, 138, 0.35)",
        "Services": "rgba(6, 214, 160, 0.35)",
        "Primary Income": "rgba(251, 146, 60, 0.35)",
        "Secondary Income": "rgba(0, 212, 255, 0.35)",
    }

    fig = go.Figure()
    for col in cols:
        fig.add_trace(go.Scatter(
            x=df["year"], y=df[col],
            name=col, mode="lines",
            line=dict(width=1.5,
                      color=COMPONENT_COLORS.get(col, COLORS["muted"]),
                      shape="spline"),
            stackgroup="one",
            fillcolor=fill_colors.get(col, "rgba(139, 149, 168, 0.2)"),
            hovertemplate=f"{col}: " + "<b>%{y:,.0f}</b><extra></extra>",
        ))

    layout = _base_layout("CA Components Evolution", height=420)
    fig.update_layout(**layout)
    fig.update_layout(yaxis_title=dict(text="EUR millions",
                      font=dict(size=12, color=COLORS["dim"])))
    return fig


# ── FDI Deep Dive ─────────────────────────────────────────────────

# Distinct colors for top FDI countries
_COUNTRY_PALETTE = [
    "#00D4FF", "#7C5CFC", "#06D6A0", "#FBBF24", "#FB923C",
    "#EC4899", "#3B82F6", "#14B8A6", "#F43F5E", "#A78BFA",
    "#8B95A8",  # "Other" — muted
]

# Distinct colors for sectors
_SECTOR_PALETTE = [
    "#00D4FF", "#06D6A0", "#FBBF24", "#FB923C", "#7C5CFC",
    "#EC4899", "#3B82F6", "#14B8A6", "#F43F5E", "#A78BFA",
    "#F97316", "#10B981", "#8B5CF6", "#EF4444", "#0EA5E9",
    "#D946EF", "#84CC16", "#64748B",
]


def fdi_total_flows_chart(flows_df):
    """Inflows vs Outflows bar chart with Net FDI line."""
    fig = go.Figure()

    if "Inflows" in flows_df.columns:
        fig.add_trace(go.Bar(
            x=flows_df["year"], y=flows_df["Inflows"],
            name="FDI Inflows",
            marker=dict(color=COLORS["teal"], cornerradius=3),
            opacity=0.85,
            hovertemplate="Inflows: <b>%{y:,.0f}</b> EUR mn<extra></extra>",
        ))
    if "Outflows" in flows_df.columns:
        fig.add_trace(go.Bar(
            x=flows_df["year"], y=-flows_df["Outflows"],
            name="FDI Outflows",
            marker=dict(color=COLORS["red"], cornerradius=3),
            opacity=0.7,
            hovertemplate="Outflows: <b>%{customdata:,.0f}</b><extra></extra>",
            customdata=flows_df["Outflows"],
        ))
    if "Net FDI" in flows_df.columns:
        fig.add_trace(go.Scatter(
            x=flows_df["year"], y=flows_df["Net FDI"].abs(),
            name="Net FDI (abs)", mode="lines+markers",
            line=dict(color=COLORS["gold"], width=2.5, shape="spline"),
            marker=dict(size=7, color=COLORS["gold"],
                        line=dict(width=2, color=COLORS["bg"])),
            hovertemplate="Net FDI: <b>%{y:,.0f}</b><extra></extra>",
        ))

    layout = _base_layout("FDI Flows: Inflows vs Outflows", height=440)
    fig.update_layout(**layout)
    fig.update_layout(barmode="relative",
                      yaxis_title=dict(text="EUR millions",
                      font=dict(size=12, color=COLORS["dim"])))
    return fig


def fdi_by_country_chart(country_df, title="FDI Inflows by Country"):
    """Stacked bar chart of FDI inflows by country over time."""
    if country_df.empty:
        return go.Figure().update_layout(**_base_layout(title))

    fig = go.Figure()
    countries = country_df.groupby("country")["value"].sum().sort_values(ascending=False)
    country_order = countries.index.tolist()

    # Put "Other" last
    if "Other" in country_order:
        country_order.remove("Other")
        country_order.append("Other")

    for i, country in enumerate(country_order):
        sub = country_df[country_df["country"] == country]
        color = _COUNTRY_PALETTE[i % len(_COUNTRY_PALETTE)]
        fig.add_trace(go.Bar(
            x=sub["year"], y=sub["value"],
            name=country,
            marker=dict(color=color, cornerradius=2),
            opacity=0.9 if country != "Other" else 0.6,
            hovertemplate=f"{country}: " + "<b>%{y:,.0f}</b><extra></extra>",
        ))

    layout = _base_layout(title, height=460, show_legend=True)
    fig.update_layout(**layout)
    fig.update_layout(
        barmode="stack",
        yaxis_title=dict(text="EUR millions",
                         font=dict(size=12, color=COLORS["dim"])),
        legend=dict(
            orientation="h", yanchor="top", y=-0.15,
            xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["muted"]),
        ),
        margin=dict(l=56, r=24, t=56, b=100),
    )
    return fig


def _sector_color_map(sector_df):
    """Build a consistent sector -> color mapping based on total value ranking."""
    if sector_df.empty:
        return {}
    totals = sector_df.groupby("sector_short")["value"].sum().sort_values(ascending=False)
    return {sector: _SECTOR_PALETTE[i % len(_SECTOR_PALETTE)]
            for i, sector in enumerate(totals.index)}


def fdi_by_sector_chart(sector_df, title="FDI Inflows by Sector"):
    """Stacked bar chart of FDI by sector over time."""
    if sector_df.empty:
        return go.Figure().update_layout(**_base_layout(title))

    fig = go.Figure()
    color_map = _sector_color_map(sector_df)
    sector_order = list(color_map.keys())

    for sector in sector_order:
        sub = sector_df[sector_df["sector_short"] == sector]
        fig.add_trace(go.Bar(
            x=sub["year"], y=sub["value"],
            name=sector,
            marker=dict(color=color_map[sector], cornerradius=2),
            opacity=0.9,
            hovertemplate=f"{sector}: " + "<b>%{y:,.0f}</b><extra></extra>",
        ))

    layout = _base_layout(title, height=460, show_legend=True)
    fig.update_layout(**layout)
    fig.update_layout(
        barmode="stack",
        yaxis_title=dict(text="EUR millions",
                         font=dict(size=12, color=COLORS["dim"])),
        legend=dict(
            orientation="h", yanchor="top", y=-0.15,
            xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["muted"]),
        ),
        margin=dict(l=56, r=24, t=56, b=100),
    )
    return fig


def fdi_concentration_chart(conc_df):
    """Top 5 share in total FDI over time."""
    if conc_df.empty:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=conc_df["year"], y=conc_df["top_share_pct"],
        name="Top 5 Share (%)", mode="lines+markers",
        line=dict(color=COLORS["purple"], width=2.5, shape="spline"),
        fill="tozeroy",
        fillcolor="rgba(124, 92, 252, 0.08)",
        marker=dict(size=7, color=COLORS["purple"],
                    line=dict(width=2, color=COLORS["bg"])),
        hovertemplate="%{x}: <b>%{y:.1f}%</b><extra></extra>",
    ))

    fig.add_hline(y=50, line_dash="dash", line_color=COLORS["dim"],
                  line_width=1, opacity=0.5,
                  annotation_text="50%", annotation_position="left",
                  annotation_font=dict(size=10, color=COLORS["dim"]))

    layout = _base_layout("FDI Concentration (Top 5 Countries)", height=360)
    fig.update_layout(**layout)
    fig.update_layout(
        yaxis_title=dict(text="% of total FDI inflows",
                         font=dict(size=12, color=COLORS["dim"])),
        yaxis_range=[0, 100],
    )
    return fig


def fdi_yoy_growth_chart(growth_df):
    """Year-over-year FDI inflow growth: bars for absolute, line for %."""
    if growth_df.empty:
        return go.Figure()

    fig = go.Figure()

    colors = [COLORS["teal"] if v >= 0 else COLORS["red"]
              for v in growth_df["change"]]
    fig.add_trace(go.Bar(
        x=growth_df["year"], y=growth_df["change"],
        name="Change (EUR mn)",
        marker=dict(color=colors, cornerradius=3),
        opacity=0.8,
        hovertemplate="Change: <b>%{y:+,.0f}</b> EUR mn<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=growth_df["year"], y=growth_df["growth_pct"],
        name="Growth (%)", mode="lines+markers",
        line=dict(color=COLORS["gold"], width=2.5, shape="spline"),
        marker=dict(size=6, color=COLORS["gold"],
                    line=dict(width=2, color=COLORS["bg"])),
        yaxis="y2",
        hovertemplate="Growth: <b>%{y:+.1f}%</b><extra></extra>",
    ))

    layout = _base_layout("FDI Inflow Growth (YoY)", height=380)
    fig.update_layout(**layout)
    fig.update_layout(
        yaxis_title=dict(text="EUR mn change",
                         font=dict(size=12, color=COLORS["dim"])),
        yaxis2=dict(
            title=dict(text="Growth %",
                       font=dict(color=COLORS["gold"], size=12)),
            overlaying="y", side="right",
            gridcolor="rgba(0,0,0,0)",
            tickfont=dict(color=COLORS["gold"], size=11),
            zeroline=True, zerolinecolor=COLORS["grid_strong"],
        ),
    )
    return fig


def fdi_ca_coverage_chart(cov_df):
    """FDI coverage of CA deficit with rolling average and FDI amounts."""
    if cov_df.empty:
        return go.Figure()

    fig = go.Figure()
    has_fdi = "Net FDI" in cov_df.columns

    colors = [COLORS["teal"] if v >= 100 else COLORS["gold"]
              for v in cov_df["coverage"]]

    # Bar labels: coverage % on top, FDI amount inside bar
    fig.add_trace(go.Bar(
        x=cov_df["year"], y=cov_df["coverage"],
        name="FDI / CA Deficit (%)",
        marker=dict(color=colors, cornerradius=4),
        opacity=0.85,
        text=[f"{v:.0f}%" for v in cov_df["coverage"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["muted"]),
        hovertemplate="%{x}: <b>%{y:.1f}%</b><extra></extra>",
    ))

    # Net FDI line on secondary Y axis
    if has_fdi:
        fig.add_trace(go.Scatter(
            x=cov_df["year"],
            y=cov_df["Net FDI"].abs(),
            name="Net FDI (EUR mn)",
            mode="lines+markers",
            yaxis="y2",
            line=dict(color=COLORS["purple"], width=2.5, shape="spline"),
            marker=dict(size=6, color=COLORS["purple"],
                        line=dict(width=2, color=COLORS["bg"])),
            hovertemplate="%{x}: <b>%{y:,.0f}</b> EUR mn<extra></extra>",
        ))

    fig.add_hline(y=100, line_dash="dash", line_color=COLORS["red"],
                  line_width=1.5, opacity=0.6,
                  annotation_text="100% coverage",
                  annotation_position="top right",
                  annotation_font=dict(size=10, color=COLORS["red"]))

    layout = _base_layout("FDI Coverage of CA Deficit", height=400,
                          show_legend=True)
    fig.update_layout(**layout)
    fig.update_layout(
        yaxis_title=dict(text="%",
                         font=dict(size=12, color=COLORS["dim"])),
        yaxis_range=[0, max(cov_df["coverage"].max() * 1.15, 120)],
        yaxis2=dict(
            title=dict(text="EUR millions",
                       font=dict(size=12, color=COLORS["dim"])),
            overlaying="y", side="right",
            showgrid=False,
            tickfont=dict(size=10, color=COLORS["muted"]),
            range=[0, cov_df["Net FDI"].abs().max() * 1.3]
            if has_fdi else None,
        ),
    )
    return fig


def fdi_sector_latest_chart(sector_df, year=None):
    """Horizontal bar: sector breakdown for a selected year."""
    if sector_df.empty:
        return go.Figure()

    color_map = _sector_color_map(sector_df)

    selected_year = year if year is not None else sector_df["year"].max()
    latest = sector_df[sector_df["year"] == selected_year].copy()
    latest = latest.sort_values("value", ascending=True)

    bar_colors = [color_map.get(s, COLORS["muted"]) for s in latest["sector_short"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=latest["sector_short"], x=latest["value"],
        orientation="h",
        marker=dict(color=bar_colors, cornerradius=4),
        text=[f"{v:,.0f}" for v in latest["value"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["muted"]),
        opacity=0.9,
        hovertemplate="%{y}: <b>%{x:,.0f}</b> EUR mn<extra></extra>",
    ))

    layout = _base_layout(f"FDI by Sector ({selected_year})",
                          height=500, show_legend=False)
    fig.update_layout(**layout)
    fig.update_layout(
        xaxis_title=dict(text="EUR millions",
                         font=dict(size=12, color=COLORS["dim"])),
        yaxis=dict(gridcolor="rgba(0,0,0,0)",
                   tickfont=dict(size=11, color=COLORS["light"])),
        margin=dict(l=110),
    )
    return fig
