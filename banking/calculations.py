"""
Banking sector calculations: ratios, rankings, market share, concentration.

Methodology (aligned with controlling / CEO_Dashboard_v4):
- ROA = PBT (annualized) / Avg Assets
- ROE = PBT (annualized) / Avg Equity
- NIM = NII (annualized) / Avg Assets
- C/I = Total OPEX / Total Revenues (managerial)
- Total Revenues = TotNetOpInc - LLP_Net + OtherInc  (excl. loan-loss provisions)
- Total OPEX = TotNetOpInc + OtherInc - PBT  (residual = XIII + XIV + XV.2)
- Annualization: Q1×4, Q2×2, Q3×(4/3), Q4×1  (YTD cumulative P&L)
- Average balances: multi-point quarterly progression
  Q1: point-in-time, Q2: (YE+Q1+Q2)/3 approx, etc.
  The CEO file provides AvgTA and AvgCapital pre-calculated.

Items that ARE annualized: ROA, ROE, NIM, Rev/Assets, OPEX/Assets, CoR
Items NOT annualized: C/I (flow/flow cancels), CapR, LiqR, LtD, Leverage
"""

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Core derived columns
# ---------------------------------------------------------------------------

def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Add all calculated columns to the main dataset. Mutates in-place."""
    df = df.copy()

    # Ensure we have required columns; fill missing with 0
    for col in ("LLP_Net", "OtherInc", "OtherExp", "Trading_Net",
                "AvgTA", "AvgCapital", "TotNetOpInc"):
        if col not in df.columns:
            df[col] = 0

    # ----- Revenue & OPEX (managerial) -----
    # Total Revenues = TotNetOpInc - LLP_Net + OtherInc
    df["TotalRev"] = df["TotNetOpInc"] - df["LLP_Net"] + df["OtherInc"]
    # Total OPEX = TotalRev - PBT  (residual: everything between revenue and PBT)
    df["TotalOPEX"] = df["TotalRev"] - df["PBT"]

    # ----- Annualized P&L -----
    ann = df["AnnF"]
    df["PBT_ann"] = df["PBT"] * ann
    df["NII_ann"] = df["NII"] * ann
    df["TotalRev_ann"] = df["TotalRev"] * ann
    df["TotalOPEX_ann"] = df["TotalOPEX"] * ann
    df["PAT_ann"] = df["PAT"] * ann
    df["IntIncome_ann"] = df["IntIncome"] * ann
    df["IntExpense_ann"] = df["IntExpense"] * ann
    df["LLP_Net_ann"] = df["LLP_Net"] * ann

    # ----- Avg balances (use pre-calculated if available) -----
    if df["AvgTA"].sum() == 0:
        df["AvgTA"] = df["TA"]  # fallback: point-in-time
    if df["AvgCapital"].sum() == 0:
        df["AvgCapital"] = df["TotalCapital"]

    # ----- Ratios -----
    df["ROA"] = _safe_div(df["PBT_ann"], df["AvgTA"])
    df["ROE"] = _safe_div(df["PBT_ann"], df["AvgCapital"])
    df["NIM"] = _safe_div(df["NII_ann"], df["AvgTA"])
    df["CIR"] = _safe_div(df["TotalOPEX"], df["TotalRev"])  # flow/flow, no annualization
    df["RevTA"] = _safe_div(df["TotalRev_ann"], df["AvgTA"])
    df["OpExTA"] = _safe_div(df["TotalOPEX_ann"], df["AvgTA"])
    df["CoR"] = _safe_div(df["LLP_Net_ann"], df["AvgTA"])
    df["Leverage"] = _safe_div(df["TA"], df["TotalCapital"])
    df["CapR"] = _safe_div(df["TotalCapital"], df["TA"])
    df["LtD"] = _safe_div(df["Loans_Clients"], df["Dep_Clients"])
    df["DepTA"] = _safe_div(df["Dep_Clients"], df["TA"])
    df["LoanTA"] = _safe_div(df["Loans_Clients"], df["TA"])
    df["SecTA"] = _safe_div(df["Securities"], df["TA"])
    df["CashTA"] = _safe_div(df["Cash_CB"], df["TA"])
    df["EquityTA"] = _safe_div(df["TotalCapital"], df["TA"])
    df["PBTM"] = _safe_div(df["PBT"], df["TotalRev"])  # flow/flow
    df["NIIR"] = _safe_div(df["NII"], df["TotalRev"])  # NII share of revenue
    df["FeeR"] = _safe_div(df["NetFeeInc"], df["TotalRev"])  # Fee share of revenue

    return df


def _safe_div(num, den):
    """Element-wise division, returns 0 where denominator is 0."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(den != 0, num / den, 0)


# ---------------------------------------------------------------------------
# Sector aggregates
# ---------------------------------------------------------------------------

def sector_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Sum across all banks per quarter for additive items."""
    additive = [
        "TA", "Cash_CB", "Pledged", "Securities", "Loans_Banks", "Loans_Clients",
        "Intangible", "PPE", "InvProp", "TotalCapital", "TotalLiab",
        "Dep_Banks", "Dep_Clients",
        "IntIncome", "IntExpense", "NII", "FeeIncome", "FeeExpense", "NetFeeInc",
        "Trading_Net", "LLP_Net", "TotNetOpInc", "OtherInc", "OtherExp",
        "PBT", "PAT", "TotalRev", "TotalOPEX",
        "AvgTA", "AvgCapital",
    ]
    cols = [c for c in additive if c in df.columns]
    grp = df.groupby("DateLabel")[cols].sum().reset_index()
    grp["Bank"] = "SECTOR"
    grp["AnnF"] = grp["DateLabel"].str[-1].astype(int).map({1: 4, 2: 2, 3: 4/3, 4: 1})
    # Recompute ratios for sector
    grp = enrich(grp)
    return grp


def market_share(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Market share of each bank for a given column, per quarter.
    Returns df with columns: Bank, DateLabel, value, sector_total, share.
    """
    totals = df.groupby("DateLabel")[col].sum().rename("sector_total")
    out = df[["Bank", "DateLabel", col]].merge(totals, on="DateLabel")
    out["share"] = _safe_div(out[col].values, out["sector_total"].values)
    out = out.rename(columns={col: "value"})
    return out


def rank_banks(df: pd.DataFrame, col: str, ascending: bool = False) -> pd.DataFrame:
    """Rank banks per quarter for a given column.
    Returns df with columns: Bank, DateLabel, value, rank.
    """
    out = df[["Bank", "DateLabel", col]].copy()
    out["rank"] = out.groupby("DateLabel")[col].rank(
        ascending=ascending, method="min"
    ).astype(int)
    out = out.rename(columns={col: "value"})
    return out


def concentration(df: pd.DataFrame, col: str, top_n: int = 5) -> pd.DataFrame:
    """Top-N concentration per quarter.
    Returns: DateLabel, top_n_sum, sector_total, top_n_share.
    """
    rows = []
    for ql, grp in df.groupby("DateLabel"):
        total = grp[col].sum()
        top = grp.nlargest(top_n, col)[col].sum()
        rows.append({
            "DateLabel": ql,
            "top_sum": top,
            "sector_total": total,
            "top_share": top / total if total else 0,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Growth calculations
# ---------------------------------------------------------------------------

def yoy_growth(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Year-over-year growth per bank (same quarter comparison).
    Returns: Bank, DateLabel, value, prev_value, abs_change, pct_change.
    """
    d = df[["Bank", "DateLabel", "Date", col]].copy()
    d["year"] = d["Date"].dt.year
    d["q"] = d["Date"].dt.quarter
    d = d.sort_values(["Bank", "year", "q"])
    d["prev"] = d.groupby(["Bank", "q"])[col].shift(1)
    d["abs_change"] = d[col] - d["prev"]
    d["pct_change"] = _safe_div(d["abs_change"].values, np.abs(d["prev"].values))
    d = d.dropna(subset=["prev"])
    d = d.rename(columns={col: "value", "prev": "prev_value"})
    return d[["Bank", "DateLabel", "value", "prev_value", "abs_change", "pct_change"]]


def cagr(start_val: float, end_val: float, years: float) -> float:
    """Compound annual growth rate."""
    if start_val <= 0 or end_val <= 0 or years <= 0:
        return 0
    return (end_val / start_val) ** (1 / years) - 1


# ---------------------------------------------------------------------------
# Peer comparison helpers
# ---------------------------------------------------------------------------

def peer_table(df: pd.DataFrame, bank: str, quarter: str,
               metrics: list) -> pd.DataFrame:
    """Build a peer comparison table for one bank vs sector.

    Args:
        df: enriched full dataset
        bank: selected bank name
        quarter: e.g. '2025Q4'
        metrics: list of (column_name, display_label, format_str, higher_is_better)

    Returns DataFrame with columns:
        Metric, Selected, Sector Avg, Sector Med, Rank, Best, Pctile
    """
    snap = df[df["DateLabel"] == quarter].copy()
    if snap.empty:
        return pd.DataFrame()

    bank_row = snap[snap["Bank"] == bank]
    if bank_row.empty:
        return pd.DataFrame()
    bank_row = bank_row.iloc[0]

    n_banks = len(snap)
    rows = []
    for col, label, fmt, higher_better in metrics:
        if col not in snap.columns:
            continue
        vals = snap[col]
        selected = bank_row[col]
        avg = vals.mean()
        med = vals.median()
        if higher_better:
            rk = int((vals >= selected).sum())
            best = vals.max()
        else:
            rk = int((vals <= selected).sum())
            best = vals.min()
        pctile = round((n_banks - rk) / max(n_banks - 1, 1) * 100)
        rows.append({
            "Metric": label,
            "Selected": selected,
            "Sector Avg": avg,
            "Sector Med": med,
            "Rank": rk,
            "Best": best,
            "Pctile": pctile,
            "_col": col,
            "_fmt": fmt,
            "_hib": higher_better,
        })
    return pd.DataFrame(rows)


# Standard metrics for peer table
PEER_METRICS = [
    ("ROA",     "ROA (PBT, ann.)",       "{:.2%}", True),
    ("ROE",     "ROE (PBT, ann.)",       "{:.2%}", True),
    ("NIM",     "NIM (ann.)",            "{:.2%}", True),
    ("CIR",     "Cost / Income",         "{:.1%}", False),
    ("RevTA",   "Revenue / Avg Assets",  "{:.2%}", True),
    ("OpExTA",  "OPEX / Avg Assets",     "{:.2%}", False),
    ("CoR",     "Cost of Risk",          "{:.2%}", False),
    ("PBTM",    "PBT Margin",            "{:.1%}", True),
    ("LtD",     "Loan-to-Deposit",       "{:.1%}", False),
    ("CapR",    "Capital Ratio",         "{:.1%}", True),
    ("Leverage","Leverage (TA/Eq)",      "{:.1f}x", False),
    ("DepTA",   "Deposits / Assets",     "{:.1%}", True),
    ("LoanTA",  "Loans / Assets",        "{:.1%}", True),
    ("SecTA",   "Securities / Assets",   "{:.1%}", True),
]


# Standard items for market share / ranking / item analysis
ITEM_CHOICES = [
    ("TA",            "Total Assets",       "BS"),
    ("Loans_Clients", "Customer Loans",     "BS"),
    ("Dep_Clients",   "Customer Deposits",  "BS"),
    ("Securities",    "Securities",         "BS"),
    ("TotalCapital",  "Equity",             "BS"),
    ("Cash_CB",       "Cash & CB Balances", "BS"),
    ("Loans_Banks",   "Interbank Loans",    "BS"),
    ("NII",           "Net Interest Income","PL"),
    ("NetFeeInc",     "Net Fee Income",     "PL"),
    ("TotNetOpInc",   "Total Net Op. Income","PL"),
    ("PBT",           "Profit Before Tax",  "PL"),
    ("PAT",           "Profit After Tax",   "PL"),
    ("TotalOPEX",     "Total OPEX",         "PL"),
    ("IntIncome",     "Interest Income",    "PL"),
    ("IntExpense",    "Interest Expense",   "PL"),
    ("TotalRev",      "Total Revenue (Mgr)","PL"),
    ("LLP_Net",       "Loan Loss Provisions","PL"),
    ("Trading_Net",   "Trading Result",     "PL"),
    ("OtherInc",      "Other Income",       "PL"),
]
