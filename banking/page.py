"""
Serbian Banking Sector — main Streamlit page.
Called from app.py when the Banking Sector tab is active.
"""

import streamlit as st
import pandas as pd
import numpy as np

from banking.data_loader import load_data, get_bank_list, get_quarter_list
from banking.calculations import (
    enrich, sector_totals, market_share, rank_banks, concentration,
    yoy_growth, cagr, peer_table, PEER_METRICS, ITEM_CHOICES,
)
from banking.charts import (
    ranking_bar, market_share_stacked, trend_line, growth_chart,
    rank_bump, composition_bar, scatter_quadrant, concentration_chart,
    multi_bank_line, COLORS, _fmt_rsd,
)
from dashboard.styles import kpi_card


# ── Data loading (cached) ────────────────────────────────────────────

@st.cache_data(ttl=3600)
def _load():
    df = load_data()
    df = enrich(df)
    sec = sector_totals(df)
    return df, sec


def render(theme="light"):
    """Main entry point — renders the full banking page."""
    df, sec = _load()
    banks = get_bank_list(df)
    quarters = get_quarter_list(df)
    latest_q = quarters[-1] if quarters else "2025Q4"

    # ── Bank selector row ────────────────────────────────────────────
    sel1, sel2, sel3 = st.columns([2, 1, 2])
    with sel1:
        selected_bank = st.selectbox(
            "Select Bank", banks,
            index=banks.index("Intesa") if "Intesa" in banks else 0,
            key="bk_bank",
        )
    with sel2:
        selected_q = st.selectbox(
            "Quarter", quarters[::-1], index=0, key="bk_quarter",
        )

    snap = df[df["DateLabel"] == selected_q]
    bank_snap = snap[snap["Bank"] == selected_bank]
    sec_snap = sec[sec["DateLabel"] == selected_q]

    if bank_snap.empty:
        st.warning(f"No data for {selected_bank} in {selected_q}")
        return
    bk = bank_snap.iloc[0]
    sk = sec_snap.iloc[0] if not sec_snap.empty else None

    # ── Section 1: Sector Overview ──────────────────────────────────
    st.markdown('<div class="section-header">Sector Overview</div>',
                unsafe_allow_html=True)
    _render_sector_overview(df, sec, snap, sk, selected_q)

    st.markdown("---")

    # ── Section 2: Bank KPIs ────────────────────────────────────────
    st.markdown(f'<div class="section-header">{selected_bank} — Key Metrics ({selected_q})</div>',
                unsafe_allow_html=True)
    _render_bank_kpis(bk, sk, selected_q)

    st.markdown("---")

    # ── Section 3: Market Position ──────────────────────────────────
    st.markdown('<div class="section-header">Market Position</div>',
                unsafe_allow_html=True)
    _render_market_position(df, snap, selected_bank, selected_q)

    st.markdown("---")

    # ── Section 4: Growth ───────────────────────────────────────────
    st.markdown('<div class="section-header">Growth Analysis</div>',
                unsafe_allow_html=True)
    _render_growth(df, selected_bank, selected_q)

    st.markdown("---")

    # ── Section 5: Profitability & Efficiency ───────────────────────
    st.markdown('<div class="section-header">Profitability & Efficiency</div>',
                unsafe_allow_html=True)
    _render_profitability(df, sec, snap, selected_bank, selected_q)

    st.markdown("---")

    # ── Section 6: Balance Sheet Structure ──────────────────────────
    st.markdown('<div class="section-header">Balance Sheet & Funding Structure</div>',
                unsafe_allow_html=True)
    _render_balance_sheet(df, snap, selected_bank, selected_q)

    st.markdown("---")

    # ── Section 7: Loans & Deposits ─────────────────────────────────
    st.markdown('<div class="section-header">Loans & Deposits Benchmarking</div>',
                unsafe_allow_html=True)
    _render_loans_deposits(df, sec, selected_bank, selected_q)

    st.markdown("---")

    # ── Section 8: Peer Comparison Table ────────────────────────────
    st.markdown('<div class="section-header">Peer Comparison Table</div>',
                unsafe_allow_html=True)
    _render_peer_table(df, selected_bank, selected_q, theme)

    st.markdown("---")

    # ── Section 9: Strategic Positioning ────────────────────────────
    st.markdown('<div class="section-header">Strategic Positioning</div>',
                unsafe_allow_html=True)
    _render_strategic(df, snap, sec, selected_bank, selected_q)

    st.markdown("---")

    # ── Section 10: Dynamic Item Analysis ───────────────────────────
    st.markdown('<div class="section-header">Item Deep Dive</div>',
                unsafe_allow_html=True)
    _render_item_analysis(df, sec, selected_bank, selected_q)


# ====================================================================
# SECTION RENDERERS
# ====================================================================

def _render_sector_overview(df, sec, snap, sk, quarter):
    """Sector KPIs + concentration + trend."""
    if sk is None:
        return

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(kpi_card("Sector Assets", sk["TA"],
                             unit="RSD 000", css_class="kpi-neutral",
                             sub_text=quarter), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("Sector Loans", sk["Loans_Clients"],
                             unit="RSD 000", css_class="kpi-neutral",
                             sub_text=quarter), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("Sector Deposits", sk["Dep_Clients"],
                             unit="RSD 000", css_class="kpi-neutral",
                             sub_text=quarter), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card("Sector Equity", sk["TotalCapital"],
                             unit="RSD 000", css_class="kpi-neutral",
                             sub_text=quarter), unsafe_allow_html=True)
    with k5:
        pbt = sk["PBT"]
        st.markdown(kpi_card("Sector PBT", pbt,
                             unit="RSD 000",
                             css_class="kpi-positive" if pbt > 0 else "kpi-negative",
                             sub_text=quarter), unsafe_allow_html=True)

    # Sector ratio KPIs
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.metric("Sector ROA (ann.)", f"{sk['ROA']:.2%}")
    with r2:
        st.metric("Sector ROE (ann.)", f"{sk['ROE']:.2%}")
    with r3:
        st.metric("Sector NIM (ann.)", f"{sk['NIM']:.2%}")
    with r4:
        st.metric("Sector C/I", f"{sk['CIR']:.1%}")

    # Concentration + sector trends
    c1, c2 = st.columns(2)
    with c1:
        conc5 = concentration(snap, "TA", 5)
        conc_hist = concentration(df, "TA", 5)
        fig = concentration_chart(conc_hist, "Top-5 Asset Concentration")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = trend_line(sec, "SECTOR", "ROA", "Sector ROA Trend",
                         fmt_pct=True)
        st.plotly_chart(fig, use_container_width=True)


def _render_bank_kpis(bk, sk, quarter):
    """Selected bank KPI cards."""
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(kpi_card("Total Assets", bk["TA"],
                             unit="RSD 000", css_class="kpi-neutral",
                             sub_text=quarter), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("Customer Loans", bk["Loans_Clients"],
                             unit="RSD 000", css_class="kpi-neutral",
                             sub_text=quarter), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("Customer Deposits", bk["Dep_Clients"],
                             unit="RSD 000", css_class="kpi-neutral",
                             sub_text=quarter), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card("Equity", bk["TotalCapital"],
                             unit="RSD 000", css_class="kpi-neutral",
                             sub_text=quarter), unsafe_allow_html=True)
    with k5:
        pbt = bk["PBT"]
        st.markdown(kpi_card("Profit (PBT)", pbt,
                             unit="RSD 000",
                             css_class="kpi-positive" if pbt > 0 else "kpi-negative",
                             sub_text=quarter), unsafe_allow_html=True)

    # Ratio row
    r1, r2, r3, r4, r5, r6 = st.columns(6)
    with r1:
        st.metric("ROA (ann.)", f"{bk['ROA']:.2%}")
    with r2:
        st.metric("ROE (ann.)", f"{bk['ROE']:.2%}")
    with r3:
        st.metric("NIM (ann.)", f"{bk['NIM']:.2%}")
    with r4:
        st.metric("C/I Ratio", f"{bk['CIR']:.1%}")
    with r5:
        st.metric("Loan-to-Deposit", f"{bk['LtD']:.1%}")
    with r6:
        st.metric("Capital Ratio", f"{bk['CapR']:.1%}")


def _render_market_position(df, snap, bank, quarter):
    """Rankings + market share."""
    c1, c2 = st.columns(2)
    with c1:
        fig = ranking_bar(snap, "TA", f"Asset Ranking ({quarter})",
                          selected_bank=bank, fmt_func=_fmt_rsd)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = ranking_bar(snap, "PBT", f"PBT Ranking ({quarter})",
                          selected_bank=bank, fmt_func=_fmt_rsd)
        st.plotly_chart(fig, use_container_width=True)

    # Rank bumps
    c3, c4 = st.columns(2)
    with c3:
        rk = rank_banks(df, "TA")
        fig = rank_bump(rk, bank, "Asset Rank Over Time")
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        ms = market_share(df, "TA")
        fig = market_share_stacked(ms, "Asset Market Share", selected_bank=bank)
        st.plotly_chart(fig, use_container_width=True)


def _render_growth(df, bank, quarter):
    """Growth analysis for key items."""
    items = [
        ("TA",            "Total Assets"),
        ("Loans_Clients", "Customer Loans"),
        ("Dep_Clients",   "Customer Deposits"),
        ("TotalCapital",  "Equity"),
        ("PBT",           "Profit Before Tax"),
        ("NII",           "Net Interest Income"),
    ]
    cols = st.columns(3)
    for i, (col_name, label) in enumerate(items):
        with cols[i % 3]:
            g = yoy_growth(df, col_name)
            fig = growth_chart(g, bank, f"{label} Growth")
            st.plotly_chart(fig, use_container_width=True)


def _render_profitability(df, sec, snap, bank, quarter):
    """Profitability & efficiency charts."""
    c1, c2 = st.columns(2)
    with c1:
        fig = trend_line(df, bank, "ROA", f"{bank} ROA vs Sector",
                         sector_df=sec, fmt_pct=True)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = trend_line(df, bank, "ROE", f"{bank} ROE vs Sector",
                         sector_df=sec, fmt_pct=True)
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        fig = trend_line(df, bank, "NIM", f"{bank} NIM vs Sector",
                         sector_df=sec, fmt_pct=True)
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        fig = trend_line(df, bank, "CIR", f"{bank} C/I Ratio vs Sector",
                         sector_df=sec, fmt_pct=True)
        st.plotly_chart(fig, use_container_width=True)

    # Revenue mix
    c5, c6 = st.columns(2)
    with c5:
        fig = trend_line(df, bank, "NIIR", f"NII Share of Revenue",
                         sector_df=sec, fmt_pct=True)
        st.plotly_chart(fig, use_container_width=True)
    with c6:
        fig = trend_line(df, bank, "CoR", f"Cost of Risk",
                         sector_df=sec, fmt_pct=True)
        st.plotly_chart(fig, use_container_width=True)


def _render_balance_sheet(df, snap, bank, quarter):
    """Balance sheet composition comparison."""
    asset_comp = [
        ("CashTA",  "Cash & CB",   COLORS["teal"]),
        ("SecTA",   "Securities",  COLORS["purple"]),
        ("LoanTA",  "Loans",       COLORS["cyan"]),
    ]
    c1, c2 = st.columns(2)
    with c1:
        fig = composition_bar(snap, asset_comp,
                              f"Asset Composition ({quarter})", bank)
        st.plotly_chart(fig, use_container_width=True)

    liab_comp = [
        ("DepTA",    "Deposits",  COLORS["teal"]),
        ("EquityTA", "Equity",    COLORS["purple"]),
    ]
    with c2:
        fig = composition_bar(snap, liab_comp,
                              f"Funding Structure ({quarter})", bank)
        st.plotly_chart(fig, use_container_width=True)

    # Historical trend of key BS ratios
    c3, c4 = st.columns(2)
    with c3:
        fig = trend_line(df, bank, "LoanTA", "Loans / Assets Trend", fmt_pct=True)
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        fig = trend_line(df, bank, "DepTA", "Deposits / Assets Trend", fmt_pct=True)
        st.plotly_chart(fig, use_container_width=True)


def _render_loans_deposits(df, sec, bank, quarter):
    """Loans & deposits benchmarking."""
    c1, c2 = st.columns(2)
    with c1:
        ms_loans = market_share(df, "Loans_Clients")
        fig = market_share_stacked(ms_loans, "Loan Market Share", selected_bank=bank)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        ms_deps = market_share(df, "Dep_Clients")
        fig = market_share_stacked(ms_deps, "Deposit Market Share", selected_bank=bank)
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        fig = trend_line(df, bank, "LtD", f"{bank} Loan-to-Deposit",
                         sector_df=sec, fmt_pct=True)
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        g = yoy_growth(df, "Dep_Clients")
        fig = growth_chart(g, bank, "Deposit Growth")
        st.plotly_chart(fig, use_container_width=True)


def _render_peer_table(df, bank, quarter, theme):
    """Comprehensive peer comparison table."""
    pt = peer_table(df, bank, quarter, PEER_METRICS)
    if pt.empty:
        st.info("No peer data available")
        return

    # Build a styled dataframe
    display = pt[["Metric", "Selected", "Sector Avg", "Sector Med", "Rank", "Best", "Pctile"]].copy()

    # Format numbers
    for _, row in pt.iterrows():
        idx = display[display["Metric"] == row["Metric"]].index[0]
        fmt = row["_fmt"]
        for c in ["Selected", "Sector Avg", "Sector Med", "Best"]:
            val = display.at[idx, c]
            if "%" in fmt:
                display.at[idx, c] = f"{val:.2%}"
            elif "x" in fmt:
                display.at[idx, c] = f"{val:.1f}x"
            else:
                display.at[idx, c] = f"{val:.4f}"

    display["Rank"] = display["Rank"].astype(str) + f" / {len(df[df['DateLabel']==quarter])}"
    display["Pctile"] = pt["Pctile"].astype(str) + "%"

    # Style
    s = display.style
    if theme == "light":
        s = s.set_properties(**{
            "background-color": "#FFFFFF", "color": "#1E293B",
        }).set_table_styles([
            {"selector": "th", "props": [
                ("background-color", "#F1F5F9"), ("color", "#475569"),
                ("font-weight", "600"),
            ]},
        ])
    s = s.hide(axis="index")
    st.dataframe(s, use_container_width=True, height=520)


def _render_strategic(df, snap, sec, bank, quarter):
    """Strategic positioning scatter plots + summary."""
    c1, c2 = st.columns(2)
    with c1:
        fig = scatter_quadrant(
            snap, "CapR", "ROE", "Capital Ratio", "ROE",
            f"ROE vs Capital Ratio ({quarter})", selected_bank=bank,
        )
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = scatter_quadrant(
            snap, "CIR", "ROA", "Cost/Income", "ROA",
            f"ROA vs Efficiency ({quarter})", selected_bank=bank,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Strategic summary
    bk = snap[snap["Bank"] == bank].iloc[0]
    sk = sec[sec["DateLabel"] == quarter]
    if sk.empty:
        return
    sk = sk.iloc[0]

    st.markdown(f'<div class="section-header">{bank} — Strategic Summary</div>',
                unsafe_allow_html=True)

    insights = []
    # Growth vs sector
    g_ta = yoy_growth(df, "TA")
    bk_growth = g_ta[(g_ta["Bank"] == bank) & (g_ta["DateLabel"] == quarter)]
    sec_growth = g_ta.groupby("DateLabel")["pct_change"].mean()
    if not bk_growth.empty:
        bg = bk_growth.iloc[0]["pct_change"]
        sg = sec_growth.get(quarter, 0)
        if bg > sg:
            insights.append(f"Growing **faster** than sector ({bg:+.1%} vs {sg:+.1%})")
        else:
            insights.append(f"Growing **slower** than sector ({bg:+.1%} vs {sg:+.1%})")

    # Profitability
    if bk["ROA"] > sk["ROA"]:
        insights.append(f"ROA **above** sector average ({bk['ROA']:.2%} vs {sk['ROA']:.2%})")
    else:
        insights.append(f"ROA **below** sector average ({bk['ROA']:.2%} vs {sk['ROA']:.2%})")

    # Efficiency
    if bk["CIR"] < sk["CIR"]:
        insights.append(f"**More efficient** than sector (C/I: {bk['CIR']:.1%} vs {sk['CIR']:.1%})")
    else:
        insights.append(f"**Less efficient** than sector (C/I: {bk['CIR']:.1%} vs {sk['CIR']:.1%})")

    # Funding
    if bk["DepTA"] > sk["DepTA"]:
        insights.append(f"**Stronger** deposit franchise ({bk['DepTA']:.1%} of assets)")
    else:
        insights.append(f"**Weaker** deposit franchise ({bk['DepTA']:.1%} vs sector {sk['DepTA']:.1%})")

    # LtD
    if bk["LtD"] < 1.0:
        insights.append(f"Loan-to-deposit ratio healthy at {bk['LtD']:.1%}")
    else:
        insights.append(f"Loan-to-deposit ratio elevated at {bk['LtD']:.1%}")

    # Market share
    ms = market_share(snap, "TA")
    bk_ms = ms[ms["Bank"] == bank]
    if not bk_ms.empty:
        share = bk_ms.iloc[0]["share"]
        rk = rank_banks(snap, "TA")
        bk_rk = rk[rk["Bank"] == bank]["rank"].iloc[0] if not rk[rk["Bank"] == bank].empty else "?"
        insights.append(f"Market share: **{share:.1%}** (rank #{bk_rk} by assets)")

    for ins in insights:
        st.markdown(f"- {ins}")


def _render_item_analysis(df, sec, bank, quarter):
    """Dynamic item deep-dive: user picks any BS/PL item and gets full analysis."""
    item_options = {label: (col, item_type) for col, label, item_type in ITEM_CHOICES}
    selected_label = st.selectbox(
        "Select item to analyze",
        list(item_options.keys()),
        index=0,
        key="bk_item",
    )
    col_name, item_type = item_options[selected_label]
    is_pl = item_type == "PL"

    snap = df[df["DateLabel"] == quarter]
    bank_data = df[df["Bank"] == bank].sort_values("DateLabel")

    st.markdown(f'<div class="section-header">{selected_label} — Deep Dive</div>',
                unsafe_allow_html=True)

    # KPI row for selected item
    bk_val = bank_data[bank_data["DateLabel"] == quarter][col_name].iloc[0] if not bank_data[bank_data["DateLabel"] == quarter].empty else 0
    sector_val = snap[col_name].sum()
    share = bk_val / sector_val if sector_val else 0
    rk_df = rank_banks(snap, col_name, ascending=False)
    bk_rank = rk_df[rk_df["Bank"] == bank]["rank"].iloc[0] if not rk_df[rk_df["Bank"] == bank].empty else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(f"{bank}: {selected_label}", f"{bk_val:,.0f}")
    with k2:
        st.metric("Market Share", f"{share:.1%}")
    with k3:
        st.metric("Rank", f"#{int(bk_rank)} / {len(snap)}")
    with k4:
        # YoY growth
        g = yoy_growth(df, col_name)
        bk_g = g[(g["Bank"] == bank) & (g["DateLabel"] == quarter)]
        if not bk_g.empty:
            st.metric("YoY Growth", f"{bk_g.iloc[0]['pct_change']:+.1%}")
        else:
            st.metric("YoY Growth", "N/A")

    # Charts row 1: Trend + Ranking
    c1, c2 = st.columns(2)
    with c1:
        sec_item = sec[["DateLabel", col_name]].copy()
        fig = trend_line(df, bank, col_name, f"{selected_label} — Trend",
                         sector_df=None)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = ranking_bar(snap, col_name, f"{selected_label} — Ranking ({quarter})",
                          selected_bank=bank, fmt_func=_fmt_rsd)
        st.plotly_chart(fig, use_container_width=True)

    # Charts row 2: Market share + Rank movement
    c3, c4 = st.columns(2)
    with c3:
        ms = market_share(df, col_name)
        fig = market_share_stacked(ms, f"{selected_label} — Market Share",
                                   selected_bank=bank)
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        rk_all = rank_banks(df, col_name)
        fig = rank_bump(rk_all, bank, f"{selected_label} — Rank Movement")
        st.plotly_chart(fig, use_container_width=True)

    # Charts row 3: Growth + Concentration
    c5, c6 = st.columns(2)
    with c5:
        g_all = yoy_growth(df, col_name)
        fig = growth_chart(g_all, bank, f"{selected_label} — YoY Growth")
        st.plotly_chart(fig, use_container_width=True)
    with c6:
        conc = concentration(df, col_name, 5)
        fig = concentration_chart(conc, f"{selected_label} — Top 5 Concentration")
        st.plotly_chart(fig, use_container_width=True)

    # If BS item, show as % of total assets
    if not is_pl and col_name != "TA":
        ratio_col = col_name + "_pct"
        temp = df.copy()
        temp[ratio_col] = np.where(temp["TA"] != 0, temp[col_name] / temp["TA"], 0)
        st.markdown(f"**{selected_label} as % of Total Assets**")
        c7, c8 = st.columns(2)
        with c7:
            fig = trend_line(temp, bank, ratio_col,
                             f"{selected_label} / Assets — Trend", fmt_pct=True)
            st.plotly_chart(fig, use_container_width=True)
        with c8:
            # Peer snapshot
            snap_temp = temp[temp["DateLabel"] == quarter]
            fig = ranking_bar(snap_temp, ratio_col,
                              f"{selected_label} / Assets ({quarter})",
                              selected_bank=bank,
                              fmt_func=lambda v: f"{v:.1%}")
            st.plotly_chart(fig, use_container_width=True)

    # Top gainers / losers table
    st.markdown(f"**Top Gainers & Losers in {selected_label} (YoY)**")
    g_latest = g_all[g_all["DateLabel"] == quarter].copy()
    if not g_latest.empty:
        g_latest = g_latest.sort_values("abs_change", ascending=False)
        display_g = g_latest[["Bank", "value", "prev_value", "abs_change", "pct_change"]].copy()
        display_g.columns = ["Bank", f"{selected_label} ({quarter})", "Previous", "Abs Change", "YoY %"]
        display_g["YoY %"] = display_g["YoY %"].apply(lambda x: f"{x:+.1%}")
        display_g[f"{selected_label} ({quarter})"] = display_g[f"{selected_label} ({quarter})"].apply(lambda x: f"{x:,.0f}")
        display_g["Previous"] = display_g["Previous"].apply(lambda x: f"{x:,.0f}")
        display_g["Abs Change"] = display_g["Abs Change"].apply(lambda x: f"{x:+,.0f}")
        st.dataframe(display_g.reset_index(drop=True), use_container_width=True, height=400)
