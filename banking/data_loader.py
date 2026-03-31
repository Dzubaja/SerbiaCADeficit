"""
Banking sector data loader.
Reads the pre-built Data sheet from CEO_Dashboard_v4.xlsx which already
contains mapped columns, annualization factors, and average balances.
Falls back to raw Banke.xlsx if CEO file is unavailable.
"""

import pandas as pd
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent  # project root (1. Contex folder)
CEO_PATH = _ROOT / "CEO_Dashboard_v4.xlsx"
BANKE_PATH = _ROOT / "Banke.xlsx"

# Bank short-name mapping (from CEO Dashboard Mapping sheet)
_BANK_SHORT = {
    "3 BANKA a.d. Novi Sad": "3 Banka",
    "Aik Bank akcionarsko društvo Beograd": "AIK",
    "API Bank akcionarsko društvo Beograd": "API",
    "Addiko Bank AD Beograd": "Addiko",
    "Adriatic Bank akcionarsko društvo Beograd": "Adriatic",
    "ALTA BANKA A.D. BEOGRAD": "Alta",
    "Bank of China Srbija akcionarsko društvo Beograd - Novi Beograd": "BoC",
    "Erste Bank A.D.- Novi Sad": "Erste",
    "Halkbank Akcionarsko društvo Beograd": "Halkbank",
    "Banca Intesa A.D.- Beograd": "Intesa",
    "MIRABANK AKCIONARSKO DRUSTVO BEOGRAD": "Mirabank",
    "NLB Komercijalna banka AD Beograd": "NLB Komercijalna",
    "OTP Banka Srbija a.d. Novi Sad": "OTP",
    "Banka Poštanska štedionica A.D.- Beograd": "Postanska",
    "ProCredit Bank A.D.- Beograd": "ProCredit",
    "Raiffeisen Banka A.D.- Beograd": "Raiffeisen",
    "Srpska banka A.D.- Beograd": "Srpska",
    "Unicredit Bank Srbija A.D.- Beograd": "UniCredit",
    "Yettel Bank ad Beograd": "Yettel",
}

# Balance sheet code → field name mapping (Banke.xlsx Oznaka → CEO Data column)
BS_MAP = {
    "A":       "TA",
    "A.I":     "Cash_CB",
    "A.II":    "Pledged",
    "A.IV":    "Securities",
    "A.V":     "Loans_Banks",
    "A.VI":    "Loans_Clients",
    "A.XI":    "Intangible",
    "A.XII":   "PPE",
    "A.XIII":  "InvProp",
    "PK.XX":   "TotalCapital",
    "PO":      "TotalLiab",
    "PO.II":   "Dep_Banks",
    "PO.III":  "Dep_Clients",
}

# Income statement code → field name mapping
# .1 = income/profit, .2 = expense/loss — we take net as .1 minus .2
PL_CODES = {
    "I.a":    "IntIncome",
    "I.b":    "IntExpense",
    "II.a":   "FeeIncome",
    "II.b":   "FeeExpense",
    "XVI.1":  "PBT",       # Profit before tax (dobitak)
    "XVI.2":  "PBT_loss",  # Loss before tax (gubitak)
    "XIX.1":  "PAT",       # Profit after tax
    "XIX.2":  "PAT_loss",
    "XII.1":  "TotNetOpInc",
    "XII.2":  "TotNetOpInc_loss",
    "XV.1":   "OtherInc",
    "XV.2":   "OtherExp",
}

# Net items from paired .1/.2 codes
NET_ITEMS = {
    "III":  "Trading_Net",
    "VIII": "LLP_Net",
}


def load_data() -> pd.DataFrame:
    """Load the main banking dataset. Returns a DataFrame with one row per bank-quarter."""
    if CEO_PATH.exists():
        return _load_from_ceo()
    return _load_from_raw()


def _load_from_ceo() -> pd.DataFrame:
    """Load pre-built Data sheet from CEO_Dashboard_v4.xlsx."""
    df = pd.read_excel(str(CEO_PATH), sheet_name="Data", header=0)
    df["Date"] = pd.to_datetime(df["Date"])
    # Ensure numeric
    num_cols = [c for c in df.columns if c not in ("Bank", "Date", "DateLabel")]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    # Derive extra fields
    df["NII"] = df["IntIncome"] - df["IntExpense"]
    df["NetFeeInc"] = df["FeeIncome"] - df["FeeExpense"]
    # Ensure DateLabel exists
    if "DateLabel" not in df.columns:
        df["DateLabel"] = df["Date"].dt.year.astype(str) + "Q" + df["Q"].astype(str)
    return df


def _load_from_raw() -> pd.DataFrame:
    """Build dataset from raw Banke.xlsx (fallback)."""
    raw = pd.read_excel(str(BANKE_PATH), sheet_name="Banke")
    raw.columns = ["BankFull", "Date", "Type", "Code", "Item", "Amount"]
    raw["Date"] = pd.to_datetime(raw["Date"])
    raw["Amount"] = pd.to_numeric(raw["Amount"], errors="coerce").fillna(0)

    # Map bank names
    raw["Bank"] = raw["BankFull"].map(_BANK_SHORT).fillna(raw["BankFull"])

    # Pivot: one row per bank-date, columns = field names
    records = []
    for (bank, date), grp in raw.groupby(["Bank", "Date"]):
        row = {"Bank": bank, "Date": date}
        code_vals = dict(zip(grp["Code"], grp["Amount"]))
        # BS items
        for code, field in BS_MAP.items():
            row[field] = code_vals.get(code, 0)
        # PL items
        for code, field in PL_CODES.items():
            row[field] = code_vals.get(code, 0)
        # Net paired items
        for prefix, field in NET_ITEMS.items():
            gain = code_vals.get(f"{prefix}.1", 0)
            loss = code_vals.get(f"{prefix}.2", 0)
            row[field] = gain - loss
        # Combine PBT
        row["PBT"] = row.get("PBT", 0) - row.get("PBT_loss", 0)
        row["PAT"] = row.get("PAT", 0) - row.get("PAT_loss", 0)
        row["TotNetOpInc"] = row.get("TotNetOpInc", 0) - row.get("TotNetOpInc_loss", 0)
        # NII, NetFeeInc
        row["NII"] = row.get("IntIncome", 0) - row.get("IntExpense", 0)
        row["NetFeeInc"] = row.get("FeeIncome", 0) - row.get("FeeExpense", 0)
        records.append(row)

    df = pd.DataFrame(records)
    df["Q"] = df["Date"].dt.quarter
    df["AnnF"] = df["Q"].map({1: 4, 2: 2, 3: 4/3, 4: 1})
    df["DateLabel"] = df["Date"].dt.year.astype(str) + "Q" + df["Q"].astype(str)
    df = df.sort_values(["Bank", "Date"]).reset_index(drop=True)
    return df


def get_bank_list(df: pd.DataFrame) -> list:
    """Sorted list of bank short names."""
    return sorted(df["Bank"].unique())


def get_quarter_list(df: pd.DataFrame) -> list:
    """Sorted list of quarter labels (e.g. '2019Q1' ... '2025Q4')."""
    return sorted(df["DateLabel"].unique())
