"""
Serbia External Sector Dashboard
─────────────────────────────────
Interactive dashboard built on NBS public data.
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
from dashboard.data_loader import (
    get_ca_annual, get_ca_components_annual, get_ca_gdp_ratio,
    get_fa_components_annual, get_fdi_coverage, get_goods_trade_annual,
    get_fx_reserves, get_external_debt_total, get_external_debt_gdp_ratio,
    get_latest_kpis,
    get_component_ranking, get_ca_granular_table,
    get_fdi_by_country, get_fdi_by_sector, get_fdi_total_flows,
    get_fdi_concentration, get_fdi_yoy_growth, get_fdi_ca_coverage,
    get_fdi_net_bop, get_fdi_flows_bop_detailed,
)
from dashboard.charts import (
    ca_trend_chart, ca_components_stacked, ca_waterfall,
    trade_chart, fa_components_chart, fdi_coverage_chart,
    fx_reserves_chart, external_debt_chart,
    component_ranking_chart, yoy_change_chart,  # kept for potential future use
    fdi_total_flows_chart, fdi_by_country_chart, fdi_by_sector_chart,
    fdi_concentration_chart, fdi_yoy_growth_chart, fdi_ca_coverage_chart,
    fdi_sector_latest_chart,
    set_theme, COLORS,
)
from dashboard.styles import get_css, kpi_card

# ── Page config ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Serbia External Sector",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Theme toggle ──────────────────────────────────────────────────────
theme = "dark" if st.session_state.get("dark_mode", False) else "light"
set_theme(theme)
st.markdown(
    '<meta name="viewport" content="width=device-width, initial-scale=1.0, '
    'maximum-scale=1.0, user-scalable=no">',
    unsafe_allow_html=True,
)
st.markdown(get_css(theme), unsafe_allow_html=True)


def _style_df(df, fmt="{:,.0f}"):
    """Apply theme-appropriate styling to a DataFrame."""
    s = df.style.format(fmt)
    if theme == "light":
        s = s.set_properties(**{
            "background-color": "#FFFFFF",
            "color": "#1E293B",
        }).set_table_styles([
            {"selector": "th", "props": [
                ("background-color", "#F1F5F9"),
                ("color", "#475569"),
                ("font-weight", "600"),
            ]},
        ])
    return s


# ── Load data (cached) ────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_all():
    return {
        "kpis": get_latest_kpis(),
        "ca": get_ca_annual(),
        "comp": get_ca_components_annual(),
        "ca_gdp": get_ca_gdp_ratio(),
        "fa": get_fa_components_annual(),
        "fdi_cov": get_fdi_coverage(),
        "trade": get_goods_trade_annual(),
        "fx": get_fx_reserves(),
        "debt": get_external_debt_total(),
        "debt_gdp": get_external_debt_gdp_ratio(),
        "ranking": get_component_ranking(),
        "fdi_flows": get_fdi_total_flows(),
        "fdi_sectors": get_fdi_by_sector(),
        "fdi_conc": get_fdi_concentration(),
        "fdi_growth": get_fdi_yoy_growth(),
        "fdi_ca_cov": get_fdi_ca_coverage(),
        "fdi_net_bop": get_fdi_net_bop(),
        "fdi_flows_bop": get_fdi_flows_bop_detailed(),
        "ca_granular": get_ca_granular_table(),
    }


data = load_all()
kpis = data["kpis"]


# ── Header ─────────────────────────────────────────────────────────────

col_title, col_toggle, col_info = st.columns([3, 0.5, 1])
with col_title:
    st.markdown(
        '<p class="dash-title">Serbia External Sector Dashboard</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="dash-subtitle">'
        'National Bank of Serbia &nbsp;&middot;&nbsp; '
        'Balance of Payments & External Position</p>',
        unsafe_allow_html=True,
    )
with col_toggle:
    st.toggle("Dark mode", value=False, key="dark_mode")
with col_info:
    accent = COLORS["cyan"]
    st.markdown(
        f'<p class="dash-subtitle" style="text-align:right; margin-top:8px;">'
        f'Latest data: <b style="color:{accent};">{kpis["year"]}</b><br>'
        f'Source: NBS (BPM6)</p>',
        unsafe_allow_html=True,
    )

st.markdown("<div style='margin-top: 0.3rem'></div>", unsafe_allow_html=True)

# No year filter — use full data range
ca_f = data["ca"]
comp_f = data["comp"]
ca_gdp_f = data["ca_gdp"]
fa_f = data["fa"]
trade_f = data["trade"]
cov_f = data["fdi_cov"]


# ── KPI helper (rendered inside each tab so tabs appear above) ────────

def _render_kpis():
    """Render the 5 top-level KPI cards."""
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(kpi_card(
            "Current Account", kpis["ca"],
            css_class="kpi-negative" if kpis["ca"] < 0 else "kpi-positive",
            sub_text=str(kpis["year"]),
            change=kpis.get("ca_change"), change_pct=kpis.get("ca_pct"),
        ), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card(
            "Trade Balance", kpis["goods"],
            css_class="kpi-negative" if kpis["goods"] < 0 else "kpi-positive",
            sub_text=str(kpis["year"]),
            change=kpis.get("goods_change"), change_pct=kpis.get("goods_pct"),
        ), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card(
            "Services Surplus", kpis["services"],
            css_class="kpi-positive" if kpis["services"] > 0 else "kpi-negative",
            sub_text=str(kpis["year"]),
            change=kpis.get("services_change"), change_pct=kpis.get("services_pct"),
        ), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card(
            "FDI Net Inflow", kpis["fdi"],
            css_class="kpi-neutral",
            sub_text=str(kpis["year"]),
            change=kpis.get("fdi_change"), change_pct=kpis.get("fdi_pct"),
        ), unsafe_allow_html=True)
    with k5:
        fx_sub = str(kpis.get("fx_year", "latest"))
        st.markdown(kpi_card(
            "NBS FX Reserves", kpis["fx_reserves"],
            css_class="kpi-neutral",
            sub_text=fx_sub,
            change=kpis.get("fx_change"), change_pct=kpis.get("fx_pct"),
        ), unsafe_allow_html=True)


# ── Tabs (above KPIs) ────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "  Current Account  ",
    "  Trade & Financing  ",
    "  FDI Deep Dive  ",
    "  External Position  ",
    "  Component Rankings  ",
])


# ── Tab 1: Current Account ────────────────────────────────────────────

with tab1:
    _render_kpis()
    c1, c2 = st.columns(2)
    with c1:
        fig_ca = ca_trend_chart(ca_f, ca_gdp_f)
        st.plotly_chart(fig_ca, use_container_width=True)
    with c2:
        fig_stack = ca_components_stacked(comp_f)
        st.plotly_chart(fig_stack, use_container_width=True)

    # Waterfall comparison: two years side by side
    available_years = sorted(comp_f["year"].unique(), reverse=True)
    if len(available_years) >= 2:
        wc1, wc2 = st.columns(2)
        with wc1:
            wf_year1 = st.selectbox("Left year", available_years,
                                     index=1, key="wf_year1")
        with wc2:
            wf_year2 = st.selectbox("Right year (% change vs left)",
                                     available_years, index=0, key="wf_year2")

        ref_row = comp_f[comp_f["year"] == wf_year1].iloc[0]

        c3, c4 = st.columns(2)
        with c3:
            fig_water1 = ca_waterfall(comp_f, year=wf_year1)
            st.plotly_chart(fig_water1, use_container_width=True)
        with c4:
            fig_water2 = ca_waterfall(comp_f, year=wf_year2, ref_row=ref_row)
            st.plotly_chart(fig_water2, use_container_width=True)
    else:
        fig_water = ca_waterfall(comp_f)
        st.plotly_chart(fig_water, use_container_width=True)


# ── Tab 2: Trade & Financing ──────────────────────────────────────────

with tab2:
    _render_kpis()
    c1, c2 = st.columns(2)
    with c1:
        fig_trade = trade_chart(trade_f)
        st.plotly_chart(fig_trade, use_container_width=True)
    with c2:
        fig_cov = fdi_coverage_chart(cov_f)
        st.plotly_chart(fig_cov, use_container_width=True)

    st.markdown('<div class="section-header">Financial Account Breakdown</div>',
                unsafe_allow_html=True)
    fig_fa = fa_components_chart(fa_f)
    st.plotly_chart(fig_fa, use_container_width=True)


# ── Tab 4: External Position ──────────────────────────────────────────

with tab4:
    _render_kpis()
    c1, c2 = st.columns(2)
    with c1:
        if data["fx"] is not None and not data["fx"].empty:
            fig_fx = fx_reserves_chart(data["fx"])
            st.plotly_chart(fig_fx, use_container_width=True)
        else:
            st.info("FX reserves data not available")
    with c2:
        fig_debt = external_debt_chart(data["debt"], data["debt_gdp"])
        st.plotly_chart(fig_debt, use_container_width=True)

    # Key ratios
    st.markdown('<div class="section-header">Key Vulnerability Indicators</div>',
                unsafe_allow_html=True)

    if not ca_gdp_f.empty:
        latest = ca_gdp_f.iloc[-1]
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.metric("CA / GDP", f"{latest['ca_gdp_pct']:.1f}%")
        with r2:
            fx_latest = data["fx"]
            if fx_latest is not None and "Total (1 to 4)" in fx_latest.columns:
                val = fx_latest["Total (1 to 4)"].iloc[-1]
                st.metric("NBS Reserves", f"{val:,.0f} EUR mn")
        with r3:
            debt_latest = data["debt"]
            if debt_latest is not None and not debt_latest.empty:
                val = debt_latest["value"].iloc[-1]
                st.metric("Total Ext. Debt", f"{val:,.0f} EUR mn")
        with r4:
            cov_latest = data["fdi_cov"]
            if not cov_latest.empty:
                val = cov_latest["coverage"].iloc[-1]
                st.metric("FDI Coverage", f"{val:.0f}%")


# ── Tab 5: BOP Granular Breakdown ────────────────────────────────────

with tab5:
    _render_kpis()
    ca_gran = data["ca_granular"]
    if not ca_gran.empty:
        # Available year columns (int)
        year_cols = sorted([c for c in ca_gran.columns if isinstance(c, int)])

        # Year comparison selectors
        st.markdown('<div class="section-header">'
                    'Balance of Payments — Granular Breakdown (EUR mn)</div>',
                    unsafe_allow_html=True)

        gc1, gc2, _ = st.columns([1, 1, 2])
        with gc1:
            yoy_from = st.selectbox("Compare FROM", year_cols[::-1],
                                     index=1, key="gran_from")
        with gc2:
            yoy_to = st.selectbox("Compare TO", year_cols[::-1],
                                   index=0, key="gran_to")

        # Build display table
        display = ca_gran[["component", "level"] + year_cols].copy()

        # Compute change columns
        if yoy_from in year_cols and yoy_to in year_cols:
            display["YoY Δ abs"] = display[yoy_to] - display[yoy_from]
            display["YoY Δ %"] = display.apply(
                lambda r: round((r[yoy_to] - r[yoy_from]) / abs(r[yoy_from]) * 100, 1)
                if r[yoy_from] != 0 else None, axis=1
            )

        # Format component names with indentation
        def _fmt_component(row):
            indent = "\u2003" * row["level"]  # em-space for indent
            return indent + row["component"]

        display["Component"] = display.apply(_fmt_component, axis=1)

        # Reorder columns
        show_cols = ["Component"] + year_cols
        if "YoY Δ abs" in display.columns:
            show_cols += ["YoY Δ abs", "YoY Δ %"]

        final = display[show_cols].copy()
        final = final.reset_index(drop=True)
        levels = display["level"].values

        # ── Build HTML table with frozen first column ──
        is_light = theme == "light"
        bg = "#FFFFFF" if is_light else "#0F1629"
        bg2 = "#F1F5F9" if is_light else "#131A2E"
        txt = "#1E293B" if is_light else "#E2E8F0"
        hdr_bg = "#E2E8F0" if is_light else "#1A2237"
        hdr_txt = "#475569" if is_light else "#94A3B8"
        border = "#E2E8F0" if is_light else "rgba(255,255,255,0.06)"
        pos_clr = "#059669" if is_light else "#06D6A0"
        neg_clr = "#DC2626" if is_light else "#FF6B8A"

        css = f"""
        <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: transparent; }}
        html, body {{ height: 100%; overflow: hidden; background: {bg}; }}
        .gran-wrap {{
            overflow: auto; height: 100%;
            border-radius: 8px; border: 1px solid {border};
            background: {bg};
        }}
        .gran-tbl {{
            border-collapse: separate; border-spacing: 0;
            width: max-content; min-width: 100%;
            font-family: Inter, sans-serif; font-size: 0.8rem;
        }}
        .gran-tbl th {{
            position: sticky; top: 0; z-index: 3;
            background: {hdr_bg}; color: {hdr_txt};
            padding: 8px 12px; text-align: right; white-space: nowrap;
            font-weight: 600; font-size: 0.75rem;
            border-bottom: 2px solid {border};
        }}
        .gran-tbl th:first-child {{
            text-align: left; position: sticky; left: 0; z-index: 5;
            min-width: 270px; background: {hdr_bg};
            border-right: 2px solid {border};
        }}
        .gran-tbl td {{
            padding: 6px 12px; text-align: right; white-space: nowrap;
            border-bottom: 1px solid {border}; color: {txt};
        }}
        .gran-tbl td:first-child {{
            text-align: left; position: sticky; left: 0; z-index: 2;
            background: {bg}; min-width: 270px;
            border-right: 2px solid {border};
        }}
        .gran-tbl tr:hover td {{ background: {bg2}; }}
        .gran-tbl tr:hover td:first-child {{ background: {bg2}; }}
        .lv0 td {{ font-weight: 800; font-size: 0.85rem; background: {bg2} !important; }}
        .lv1 td {{ font-weight: 600; font-size: 0.82rem; }}
        .lv2 td {{ font-weight: 500; font-size: 0.8rem; }}
        .lv3 td {{ font-weight: 400; font-size: 0.78rem; opacity: 0.85; }}
        .clr-pos {{ color: {pos_clr} !important; }}
        .clr-neg {{ color: {neg_clr} !important; }}
        </style>
        """

        # Build rows
        rows_html = []
        for idx in range(len(final)):
            lvl = int(levels[idx])
            cells = []
            for col in show_cols:
                val = final.iloc[idx][col]
                if col == "Component":
                    cells.append(f"<td>{val}</td>")
                elif col == "YoY Δ abs":
                    cls = ""
                    if pd.notna(val):
                        cls = "clr-pos" if val > 0 else ("clr-neg" if val < 0 else "")
                        txt_v = f"{val:+,.0f}"
                    else:
                        txt_v = "—"
                    cells.append(f'<td class="{cls}">{txt_v}</td>')
                elif col == "YoY Δ %":
                    abs_val = final.iloc[idx].get("YoY Δ abs", 0)
                    cls = ""
                    if pd.notna(abs_val):
                        cls = "clr-pos" if abs_val > 0 else ("clr-neg" if abs_val < 0 else "")
                    txt_v = f"{val:+.1f}%" if pd.notna(val) else "—"
                    cells.append(f'<td class="{cls}">{txt_v}</td>')
                else:
                    txt_v = f"{val:,.0f}" if pd.notna(val) else "—"
                    cells.append(f"<td>{txt_v}</td>")
            rows_html.append(f'<tr class="lv{lvl}">{"".join(cells)}</tr>')

        hdr_cells = "".join(f"<th>{c}</th>" for c in show_cols)

        table_html = (
            f'<!DOCTYPE html><html><head>{css}</head><body>'
            f'<div class="gran-wrap" id="gw">'
            f'<table class="gran-tbl"><thead><tr>{hdr_cells}</tr></thead>'
            f'<tbody>{"".join(rows_html)}</tbody></table></div>'
            f'<script>'
            f'var el=document.getElementById("gw");'
            f'if(el){{el.scrollLeft=el.scrollWidth;}}'
            f'</script></body></html>'
        )
        import streamlit.components.v1 as components
        components.html(table_html, height=750, scrolling=False)


# ── Tab 3: FDI Deep Dive ─────────────────────────────────────────────

with tab3:
    _render_kpis()
    st.markdown('<div class="section-header">FDI Overview</div>',
                unsafe_allow_html=True)

    # FDI KPI cards — use BOP detailed (covers 2025) with clean_fdi fallback
    fdi_flows = data["fdi_flows"]          # from clean_fdi (up to 2024)
    fdi_bop = data["fdi_flows_bop"]        # from BOP detailed (up to 2025)

    def _yoy(curr, prev):
        if curr is None or prev is None or prev == 0:
            return None, None
        c = round(curr - prev, 1)
        return c, round(c / abs(prev) * 100, 1)

    # Pick latest available source for inflows/outflows
    if not fdi_bop.empty:
        bop_latest = fdi_bop.iloc[-1]
        bop_prev = fdi_bop.iloc[-2] if len(fdi_bop) >= 2 else None
        fdi_year = int(bop_latest["year"])

        in_val = bop_latest["Inflows"]
        out_val = bop_latest["Outflows"]
        net_curr = abs(bop_latest["Net FDI"])

        in_chg, in_pct = _yoy(in_val, bop_prev["Inflows"] if bop_prev is not None else None)
        out_chg, out_pct = _yoy(out_val, bop_prev["Outflows"] if bop_prev is not None else None)
        net_prev_val = abs(bop_prev["Net FDI"]) if bop_prev is not None else None
        net_chg, net_pct = _yoy(net_curr, net_prev_val)
    elif not fdi_flows.empty:
        latest_fdi = fdi_flows.iloc[-1]
        prev_fdi = fdi_flows.iloc[-2] if len(fdi_flows) >= 2 else None
        fdi_year = int(latest_fdi["year"])

        in_val = latest_fdi.get("Inflows", 0)
        out_val = latest_fdi.get("Outflows", 0)
        net_curr = abs(latest_fdi.get("Net FDI", 0))

        in_chg, in_pct = _yoy(in_val, prev_fdi.get("Inflows") if prev_fdi is not None else None)
        out_chg, out_pct = _yoy(out_val, prev_fdi.get("Outflows") if prev_fdi is not None else None)
        net_prev_val = abs(prev_fdi.get("Net FDI", 0)) if prev_fdi is not None else None
        net_chg, net_pct = _yoy(net_curr, net_prev_val)
    else:
        fdi_year = None

    if fdi_year is not None:
        # CA coverage
        ca_data = data["ca"]
        ca_for_cov = ca_data[ca_data["year"] == fdi_year]
        if not ca_for_cov.empty and ca_for_cov["value"].iloc[0] != 0:
            cov_val = round(net_curr / abs(ca_for_cov["value"].iloc[0]) * 100, 1)
            ca_prev_cov = ca_data[ca_data["year"] == fdi_year - 1]
            if not ca_prev_cov.empty and net_prev_val is not None:
                cov_prev = round(net_prev_val / abs(ca_prev_cov["value"].iloc[0]) * 100, 1)
            else:
                cov_prev = None
        else:
            fdi_ca = data["fdi_ca_cov"]
            cov_val = fdi_ca.iloc[-1]["coverage"] if not fdi_ca.empty else None
            cov_prev = fdi_ca.iloc[-2]["coverage"] if not fdi_ca.empty and len(fdi_ca) >= 2 else None

        cov_chg = round(cov_val - cov_prev, 1) if cov_val is not None and cov_prev is not None else None

        fk1, fk2, fk3, fk4 = st.columns(4)
        with fk1:
            st.markdown(kpi_card(
                "FDI Inflows", in_val,
                css_class="kpi-positive", sub_text=str(fdi_year),
                change=in_chg, change_pct=in_pct,
            ), unsafe_allow_html=True)
        with fk2:
            st.markdown(kpi_card(
                "FDI Outflows", out_val,
                css_class="kpi-negative", sub_text=str(fdi_year),
                change=out_chg, change_pct=out_pct,
            ), unsafe_allow_html=True)
        with fk3:
            st.markdown(kpi_card(
                "Net FDI", net_curr,
                css_class="kpi-neutral", sub_text=str(fdi_year),
                change=net_chg, change_pct=net_pct,
            ), unsafe_allow_html=True)
        with fk4:
            if cov_val is not None:
                st.markdown(kpi_card(
                    "CA Coverage", cov_val, unit="%",
                    css_class="kpi-positive" if cov_val >= 100 else "kpi-negative",
                    sub_text=str(fdi_year),
                    change=cov_chg,
                ), unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 0.8rem'></div>", unsafe_allow_html=True)

    # ── Sub-tabs for FDI views ──────────────────────────────────────
    fdi_tab1, fdi_tab2, fdi_tab3 = st.tabs([
        "  By Country  ",
        "  By Sector  ",
        "  Analytics  ",
    ])

    # ── FDI by Country ──────────────────────────────────────────────
    with fdi_tab1:
        # Filters
        fc1, fc2 = st.columns([1, 3])
        with fc1:
            top_n = st.selectbox(
                "Show top N countries",
                [5, 10, 15, 20],
                index=1,
                key="fdi_top_n",
            )

        fdi_country = get_fdi_by_country(top_n=top_n)

        c1, c2 = st.columns([2, 1])
        with c1:
            fig = fdi_by_country_chart(fdi_country)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig_conc = fdi_concentration_chart(data["fdi_conc"])
            st.plotly_chart(fig_conc, use_container_width=True)

        # Country table — all countries, no top_n grouping
        st.markdown('<div class="section-header">FDI Inflows by Country (EUR mn)</div>',
                    unsafe_allow_html=True)
        fdi_country_all = get_fdi_by_country(top_n=999)
        if not fdi_country_all.empty:
            pivot = fdi_country_all.pivot_table(
                index="country", columns="year", values="value", aggfunc="sum"
            ).round(0)
            pivot["Total"] = pivot.sum(axis=1)
            pivot = pivot[pivot["Total"].abs() > 0]
            pivot = pivot.sort_values("Total", ascending=False)
            st.dataframe(_style_df(pivot), use_container_width=True, height=450)

    # ── FDI by Sector ───────────────────────────────────────────────
    with fdi_tab2:
        sector_df = data["fdi_sectors"]
        sector_f = sector_df

        # Year selector — sits in the right-column area, inline before charts
        if not sector_f.empty:
            sector_years = sorted(sector_f["year"].unique(), reverse=True)
            _lpad, _rpad, _sel = st.columns([5, 2, 1])
            with _sel:
                sel_year = st.selectbox("Year", sector_years, index=0,
                                        key="fdi_sector_year", label_visibility="collapsed")
        else:
            sel_year = None

        c1, c2 = st.columns(2)
        with c1:
            fig = fdi_by_sector_chart(sector_f)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            if sel_year is not None:
                fig = fdi_sector_latest_chart(sector_f, year=sel_year)
            else:
                fig = fdi_sector_latest_chart(sector_f)
            st.plotly_chart(fig, use_container_width=True)

        # Sector table
        st.markdown('<div class="section-header">FDI by Sector Over Time (EUR mn)</div>',
                    unsafe_allow_html=True)
        if not sector_f.empty:
            pivot = sector_f.pivot_table(
                index="sector_short", columns="year", values="value", aggfunc="sum"
            ).round(0)
            pivot["Total"] = pivot.sum(axis=1)
            pivot = pivot.sort_values("Total", ascending=False)
            st.dataframe(_style_df(pivot), use_container_width=True, height=400)

    # ── FDI Analytics ───────────────────────────────────────────────
    with fdi_tab3:
        # Use BOP detailed (covers 2025) for all analytics charts
        fdi_analytics = data["fdi_flows_bop"] if not data["fdi_flows_bop"].empty else fdi_flows

        # Derive YoY growth from BOP data
        if not fdi_analytics.empty and "Inflows" in fdi_analytics.columns:
            _g = fdi_analytics[["year", "Inflows"]].copy()
            _g["prev"] = _g["Inflows"].shift(1)
            _g["change"] = _g["Inflows"] - _g["prev"]
            _g["growth_pct"] = ((_g["change"] / _g["prev"]) * 100).round(1)
            _g["value"] = _g["Inflows"]
            growth_bop = _g.dropna(subset=["prev"])
        else:
            growth_bop = data["fdi_growth"]

        # Derive CA coverage from BOP data
        if not fdi_analytics.empty and "Net FDI" in fdi_analytics.columns:
            ca_data = data["ca"]
            _c = fdi_analytics[["year", "Net FDI"]].merge(ca_data, on="year", suffixes=("_fdi", "_ca"))
            _c["coverage"] = (_c["Net FDI"].abs() / _c["value"].abs() * 100).round(1)
            _c["coverage"] = _c["coverage"].clip(upper=500)
            cov_bop = _c[["year", "coverage", "Net FDI"]]
        else:
            cov_bop = data["fdi_ca_cov"]

        c1, c2 = st.columns(2)
        with c1:
            fig = fdi_total_flows_chart(fdi_analytics)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = fdi_yoy_growth_chart(growth_bop)
            st.plotly_chart(fig, use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            fig = fdi_ca_coverage_chart(cov_bop)
            st.plotly_chart(fig, use_container_width=True)
        with c4:
            # Cumulative FDI inflows
            if not fdi_analytics.empty and "Inflows" in fdi_analytics.columns:
                import plotly.graph_objects as go
                from dashboard.charts import _base_layout
                cum = fdi_analytics[["year", "Inflows"]].copy()
                cum["Cumulative"] = cum["Inflows"].cumsum()
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=cum["year"], y=cum["Cumulative"],
                    name="Cumulative FDI", mode="lines+markers",
                    line=dict(color=COLORS["cyan"], width=2.5, shape="spline"),
                    fill="tozeroy",
                    fillcolor="rgba(0, 212, 255, 0.08)",
                    marker=dict(size=5, color=COLORS["cyan"],
                                line=dict(width=2, color=COLORS["bg"])),
                    hovertemplate="%{x}: <b>%{y:,.0f}</b> EUR mn<extra></extra>",
                ))
                fig.update_layout(**_base_layout("Cumulative FDI Inflows", height=400))
                fig.update_layout(yaxis_title=dict(text="EUR millions",
                                  font=dict(size=12, color=COLORS["dim"])))
                st.plotly_chart(fig, use_container_width=True)

        # Key insights
        st.markdown('<div class="section-header">Key FDI Metrics</div>',
                    unsafe_allow_html=True)

        if not fdi_analytics.empty and not growth_bop.empty:
            conc = data["fdi_conc"]

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                avg_inflow = fdi_analytics["Inflows"].mean()
                st.metric("Avg Annual Inflow", f"{avg_inflow:,.0f} EUR mn")
            with m2:
                latest_growth = growth_bop.iloc[-1]
                delta = f"{latest_growth['growth_pct']:+.1f}%"
                st.metric("Latest YoY Growth", delta)
            with m3:
                if not conc.empty:
                    st.metric("Top 5 Concentration", f"{conc.iloc[-1]['top_share_pct']:.0f}%")
            with m4:
                total_cum = fdi_analytics["Inflows"].sum()
                fdi_min_yr = int(fdi_analytics["year"].min())
                fdi_max_yr = int(fdi_analytics["year"].max())
                st.metric(f"Total FDI ({fdi_min_yr}-{fdi_max_yr})", f"{total_cum:,.0f} EUR mn")
