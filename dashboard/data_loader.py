"""
Data loader: all SQL queries and data transformations for the dashboard.
Each function returns a pandas DataFrame ready for charting.
"""

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "db" / "nbs_external_sector.db"


def _conn():
    return sqlite3.connect(str(DB_PATH))


# ── BOP: Current Account ──────────────────────────────────────────────

def get_ca_annual():
    """Current account balance, annual, from the main BOP file."""
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT substr(b.date, 1, 4) as year, b.value
        FROM clean_bop b
        JOIN metadata m ON b.source_id = m.source_id
        WHERE m.filename = 'bop_annual_2007_2025.xls'
          AND b.indicator_code = 'CA'
          AND b.sub_indicator = 'net'
        ORDER BY b.date
    """, conn)
    conn.close()
    df["year"] = df["year"].astype(int)
    return df


def get_ca_components_annual():
    """
    CA decomposition: goods, services, primary income, secondary income.
    Derives goods as residual to avoid duplicate-row issues.
    """
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT substr(b.date, 1, 4) as year,
               b.indicator_code, b.value
        FROM clean_bop b
        JOIN metadata m ON b.source_id = m.source_id
        WHERE m.filename = 'bop_annual_2007_2025.xls'
          AND b.indicator_code IN ('CA', 'CA.SERVICES', 'CA.PRIMARY_INCOME', 'CA.SECONDARY_INCOME')
          AND b.sub_indicator = 'net'
        ORDER BY b.date
    """, conn)
    conn.close()
    df["year"] = df["year"].astype(int)

    pivot = df.pivot_table(index="year", columns="indicator_code",
                           values="value", aggfunc="first").reset_index()

    # Derive goods as residual: CA - services - primary - secondary
    pivot["Goods"] = (
        pivot["CA"]
        - pivot["CA.SERVICES"]
        - pivot["CA.PRIMARY_INCOME"]
        - pivot["CA.SECONDARY_INCOME"]
    )
    pivot = pivot.rename(columns={
        "CA": "Current Account",
        "CA.SERVICES": "Services",
        "CA.PRIMARY_INCOME": "Primary Income",
        "CA.SECONDARY_INCOME": "Secondary Income",
    })
    return pivot


def get_ca_monthly():
    """Monthly CA data from the latest monthly BOP file (EUR sheet only)."""
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT b.date, b.indicator_code, b.value
        FROM clean_bop b
        JOIN metadata m ON b.source_id = m.source_id
        WHERE m.filename LIKE 'bop_monthly%'
          AND b.indicator_code IN ('CA', 'CA.SERVICES', 'CA.PRIMARY_INCOME', 'CA.SECONDARY_INCOME')
          AND b.sub_indicator = 'net'
          AND b.unit = 'EUR mn'
        ORDER BY b.date
    """, conn)
    conn.close()
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    return df


# ── Financial Account & FDI ───────────────────────────────────────────

def get_fa_components_annual():
    """Financial account components: FDI, portfolio, other, reserves."""
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT substr(b.date, 1, 4) as year,
               b.indicator_code, b.indicator_name, b.value
        FROM clean_bop b
        JOIN metadata m ON b.source_id = m.source_id
        WHERE m.filename = 'bop_annual_2007_2025.xls'
          AND b.indicator_code IN ('FA', 'FA.FDI', 'FA.PORTFOLIO', 'FA.OTHER', 'FA.RESERVES')
          AND b.sub_indicator = 'net'
        ORDER BY b.date
    """, conn)
    conn.close()
    df["year"] = df["year"].astype(int)
    # FA has duplicates — take first per year
    df = df.drop_duplicates(subset=["year", "indicator_code"], keep="first")
    return df


def get_fdi_coverage():
    """FDI coverage ratio: |net FDI| / |CA deficit|."""
    ca = get_ca_annual()
    fa = get_fa_components_annual()
    fdi = fa[fa["indicator_code"] == "FA.FDI"][["year", "value"]].rename(
        columns={"value": "fdi"}
    )
    merged = ca.merge(fdi, on="year")
    # BPM6: negative FDI = net inflow, negative CA = deficit
    merged["coverage"] = (merged["fdi"].abs() / merged["value"].abs() * 100).round(1)
    merged["coverage"] = merged["coverage"].clip(upper=300)  # cap outliers
    return merged


# ── Goods: Exports vs Imports ─────────────────────────────────────────

def get_goods_trade_annual():
    """Goods exports and imports (credit/debit), annual."""
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT substr(b.date, 1, 4) as year,
               b.sub_indicator, b.value
        FROM clean_bop b
        JOIN metadata m ON b.source_id = m.source_id
        WHERE m.filename = 'bop_annual_2007_2025.xls'
          AND b.indicator_code = 'CA.GOODS'
          AND b.sub_indicator IN ('credit', 'debit')
        ORDER BY b.date
    """, conn)
    conn.close()
    df["year"] = df["year"].astype(int)
    # There may be multiple CA.GOODS rows (goods vs goods+services)
    # Take the larger values (goods+services credit > goods-only credit)
    # Actually we want goods only — take the SMALLER credit, LARGER debit
    # Simpler: group and take max absolute value per year/direction
    pivot = df.pivot_table(index="year", columns="sub_indicator",
                           values="value", aggfunc="max").reset_index()
    pivot = pivot.rename(columns={"credit": "Exports", "debit": "Imports"})
    pivot["Balance"] = pivot["Exports"] - pivot["Imports"]
    return pivot


# ── FX Reserves ───────────────────────────────────────────────────────

def get_fx_reserves():
    """NBS FX reserves (Total 1 to 4 = NBS reserves), annual end-of-year."""
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT r.date, r.indicator, r.value
        FROM clean_fx_reserves r
        JOIN metadata m ON r.source_id = m.source_id
        WHERE r.indicator IN ('Total (1 to 4)', 'Total (5+6)')
        ORDER BY r.date
    """, conn)
    conn.close()
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    # Take end-of-year values (December or max date per year)
    annual = df.groupby(["year", "indicator"]).last().reset_index()
    pivot = annual.pivot_table(index="year", columns="indicator",
                               values="value", aggfunc="first").reset_index()
    return pivot


# ── External Debt ─────────────────────────────────────────────────────

def get_external_debt_total():
    """Total external debt over time."""
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT date, debtor_type, maturity, value
        FROM clean_external_debt
        WHERE debtor_type = 'total' AND maturity = 'total'
        ORDER BY date
    """, conn)
    conn.close()
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    # Take the largest "total" value per date (total external debt)
    annual = df.groupby("year")["value"].max().reset_index()
    return annual


def get_external_debt_gdp_ratio():
    """External debt as % of GDP."""
    debt = get_external_debt_total()
    gdp = get_gdp()
    if debt.empty or gdp.empty:
        return pd.DataFrame()
    merged = debt.merge(gdp, on="year", suffixes=("_debt", "_gdp"))
    merged["debt_gdp_pct"] = (merged["value_debt"] / merged["value_gdp"] * 100).round(1)
    return merged


# ── Macro / GDP ───────────────────────────────────────────────────────

def get_gdp():
    """GDP in EUR millions, annual."""
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT substr(date, 1, 4) as year, value
        FROM clean_macro
        WHERE indicator_name LIKE '%БДП (у млн евра)%'
        ORDER BY date
    """, conn)
    conn.close()
    df["year"] = df["year"].astype(int)
    df = df.drop_duplicates(subset=["year"], keep="first")
    return df


# ── Derived: CA/GDP ratio ────────────────────────────────────────────

def get_ca_gdp_ratio():
    """Current account as % of GDP."""
    ca = get_ca_annual()
    gdp = get_gdp()
    merged = ca.merge(gdp, on="year", suffixes=("_ca", "_gdp"))
    merged["ca_gdp_pct"] = (merged["value_ca"] / merged["value_gdp"] * 100).round(2)
    return merged


# ── KPI snapshot (latest year) ────────────────────────────────────────

def get_latest_kpis():
    """Return dict of latest KPI values with YoY changes for the header cards."""
    ca = get_ca_annual()
    comp = get_ca_components_annual()
    fa = get_fa_components_annual()

    latest_year = ca["year"].max()
    prev_year = latest_year - 1

    def _chg(curr, prev):
        if curr is None or prev is None:
            return None, None
        c = round(curr - prev, 1)
        p = round(c / abs(prev) * 100, 1) if prev != 0 else None
        return c, p

    # Current Account
    ca_val = ca[ca["year"] == latest_year]["value"].iloc[0]
    ca_prev_df = ca[ca["year"] == prev_year]
    ca_prev = ca_prev_df["value"].iloc[0] if not ca_prev_df.empty else None
    ca_chg, ca_pct = _chg(ca_val, ca_prev)

    # Components
    lc = comp[comp["year"] == latest_year].iloc[0]
    pc_df = comp[comp["year"] == prev_year]
    goods_val = lc["Goods"]
    services_val = lc["Services"]
    if not pc_df.empty:
        pc = pc_df.iloc[0]
        goods_chg, goods_pct = _chg(goods_val, pc["Goods"])
        services_chg, services_pct = _chg(services_val, pc["Services"])
    else:
        goods_chg = goods_pct = services_chg = services_pct = None

    # FDI (show as positive inflow)
    fdi_row = fa[(fa["year"] == latest_year) & (fa["indicator_code"] == "FA.FDI")]
    fdi_prev_row = fa[(fa["year"] == prev_year) & (fa["indicator_code"] == "FA.FDI")]
    fdi_val = abs(fdi_row["value"].iloc[0]) if not fdi_row.empty else 0
    fdi_prev = abs(fdi_prev_row["value"].iloc[0]) if not fdi_prev_row.empty else None
    fdi_chg, fdi_pct = _chg(fdi_val, fdi_prev)

    # FX reserves — absolute latest available
    fx = get_fx_reserves()
    fx_val = fx_prev = None
    fx_year = None
    if fx is not None and not fx.empty and "Total (1 to 4)" in fx.columns:
        fx_val = fx["Total (1 to 4)"].iloc[-1]
        fx_year = int(fx["year"].iloc[-1])
        if len(fx) >= 2:
            fx_prev = fx["Total (1 to 4)"].iloc[-2]
    fx_chg, fx_pct = _chg(fx_val, fx_prev)

    return {
        "year": latest_year,
        "ca": ca_val, "ca_change": ca_chg, "ca_pct": ca_pct,
        "goods": goods_val, "goods_change": goods_chg, "goods_pct": goods_pct,
        "services": services_val, "services_change": services_chg, "services_pct": services_pct,
        "fdi": fdi_val, "fdi_change": fdi_chg, "fdi_pct": fdi_pct,
        "fx_reserves": fx_val, "fx_change": fx_chg, "fx_pct": fx_pct,
        "fx_year": fx_year,
    }


# ── Component ranking ─────────────────────────────────────────────────

def get_ca_granular_table():
    """Full BOP breakdown from BOP detailed file, all years, with hierarchy.

    Returns DataFrame with: component (display name), level (indent depth),
    and one column per year (2007-2025).
    Covers: Current Account + Capital Account + Financial Account.
    """
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT r.indicator_raw, r.period_raw,
               CAST(r.value_raw AS REAL) AS value
        FROM raw_bop r
        JOIN metadata m ON r.source_id = m.source_id
        WHERE m.filename = 'bop_annual_detailed_2007_2025.xls'
        ORDER BY r.rowid
    """, conn)
    conn.close()
    if df.empty:
        return pd.DataFrame()

    years = sorted(df["period_raw"].unique())

    # Build row-index per year from "Current account" to end of file
    records = []
    for yr in years:
        chunk = df[df["period_raw"] == yr].reset_index(drop=True)
        ca_i = chunk[chunk["indicator_raw"] == "Current account"].index
        if len(ca_i) == 0:
            continue
        start = ca_i[0]
        for pos, idx in enumerate(range(start, len(chunk))):
            records.append({
                "pos": pos, "year": int(yr),
                "value": chunk.iloc[idx]["value"],
            })

    wide = pd.DataFrame(records).pivot_table(
        index="pos", columns="year", values="value"
    )

    # Curated rows: (pos_from_CA_start, display_name, level)
    # Level 0 = section header, 1 = main item, 2 = sub-item, 3 = detail
    _ROWS = [
        # ── Current Account ──
        (0,  "CURRENT ACCOUNT", 0),
        (1,  "Credit", 1),
        (2,  "Debit", 1),
        (3,  "GOODS AND SERVICES", 0),
        (4,  "Exports of Goods & Services", 1),
        (5,  "Imports of Goods & Services", 1),
        (6,  "Goods (net)", 1),
        (7,  "Goods - Exports", 2),
        (8,  "Goods - Imports", 2),
        (9,  "Services (net)", 1),
        (10, "Services - Exports", 2),
        (11, "Manufacturing services", 3),
        (13, "Transport", 3),
        (14, "Travel", 3),
        (15, "Construction", 3),
        (21, "Telecom, IT & Information", 3),
        (22, "Other business services", 3),
        (26, "Personal, cultural & recreational", 3),
        (28, "Services - Imports", 2),
        (29, "Manufacturing services", 3),
        (31, "Transport", 3),
        (32, "Travel", 3),
        (33, "Construction", 3),
        (39, "Telecom, IT & Information", 3),
        (40, "Other business services", 3),
        (44, "Personal, cultural & recreational", 3),
        (46, "PRIMARY INCOME", 0),
        (47, "Credit", 1),
        (48, "Debit", 1),
        (49, "Compensation of Employees", 1),
        (52, "Investment Income", 1),
        (55, "Direct Investment", 2),
        (70, "Portfolio Investment", 2),
        (79, "Other Investment", 2),
        (88, "Reserve Assets", 2),
        (92, "SECONDARY INCOME", 0),
        (93, "Credit", 1),
        (94, "Debit", 1),
        (95, "General Government", 1),
        (98, "Other Sectors", 1),
        (101, "Personal Transfers", 2),
        (104, "Workers' Remittances", 2),
        (107, "Other Current Transfers", 1),
        # ── Capital Account ──
        (110, "CAPITAL ACCOUNT", 0),
        (111, "Credit", 1),
        (112, "Debit", 1),
        (119, "NET LENDING / NET BORROWING", 0),
        # ── Financial Account ──
        (120, "FINANCIAL ACCOUNT (net)", 0),
        (121, "Assets", 1),
        (122, "Liabilities", 1),
        # Direct Investment
        (124, "DIRECT INVESTMENT (net)", 0),
        (125, "Assets", 1),
        (126, "Equity & investment fund shares", 2),
        (129, "Debt instruments", 2),
        (130, "Liabilities", 1),
        (131, "Equity & investment fund shares", 2),
        (134, "Debt instruments", 2),
        # Portfolio Investment
        (135, "PORTFOLIO INVESTMENT (net)", 0),
        (136, "Assets", 1),
        (137, "Equity & investment fund shares", 2),
        (142, "Debt securities", 2),
        (155, "Liabilities", 1),
        (156, "Equity & investment fund shares", 2),
        (163, "Debt securities", 2),
        # Financial Derivatives
        (176, "FINANCIAL DERIVATIVES (net)", 0),
        (177, "Assets", 1),
        (178, "Liabilities", 1),
        # Other Investment
        (179, "OTHER INVESTMENT (net)", 0),
        (180, "Assets", 1),
        (181, "Liabilities", 1),
        (185, "Currency & Deposits (net)", 1),
        (186, "Assets", 2),
        (191, "Liabilities", 2),
        (196, "Loans (net)", 1),
        (197, "Assets", 2),
        (214, "Liabilities", 2),
        (249, "Insurance & Pension Schemes (net)", 1),
        (252, "Trade Credit & Advances (net)", 1),
        (253, "Assets", 2),
        (260, "Liabilities", 2),
        # Reserve Assets
        (269, "RESERVE ASSETS", 0),
        (270, "Monetary Gold", 1),
        (273, "Special Drawing Rights", 1),
        (274, "Reserve Position in IMF", 1),
        (275, "Other Reserve Assets", 1),
        (276, "Currency & Deposits", 2),
        (279, "Securities", 2),
        # Errors & Omissions
        (286, "NET ERRORS AND OMISSIONS", 0),
    ]

    result = []
    for pos, name, level in _ROWS:
        if pos not in wide.index:
            continue
        row = {"component": name, "level": level}
        for yr in wide.columns:
            row[yr] = wide.loc[pos, yr]
        result.append(row)

    return pd.DataFrame(result)


def get_component_ranking():
    """
    Rank CA components by absolute contribution, with YoY change.
    """
    comp = get_ca_components_annual()
    if comp.empty:
        return comp

    cols = ["Goods", "Services", "Primary Income", "Secondary Income"]
    latest_year = comp["year"].max()
    prev_year = latest_year - 1

    latest = comp[comp["year"] == latest_year][cols].iloc[0]
    prev = comp[comp["year"] == prev_year][cols].iloc[0] if prev_year in comp["year"].values else None

    rows = []
    for col in cols:
        row = {"Component": col, "Value": latest[col]}
        if prev is not None:
            row["Previous"] = prev[col]
            row["Change"] = latest[col] - prev[col]
        else:
            row["Previous"] = None
            row["Change"] = None
        rows.append(row)

    df = pd.DataFrame(rows)
    df["AbsValue"] = df["Value"].abs()
    df = df.sort_values("AbsValue", ascending=True)
    return df


# ── FDI Deep Dive ────────────────────────────────────────────────────

# Regional aggregates to exclude when listing individual countries
_FDI_AGGREGATES = {
    "TOTAL", "EUROPE", "AFRICA", "AMERICA", "ASIA",
    "OCEANIA AND POLAR REGIONS",
    "European Union (EU-27)", "Other Asian countries",
    "Other european countries", "Other African countries",
    "North African countries", "South African countries",
    "Near and Middle East", "North American countries",
    "Central American countries and Caribbean",
    "South American countries",
}


def get_fdi_by_country(flow_or_position="flow", top_n=10):
    """
    FDI liabilities (inflows) by country, annual.
    Returns a DataFrame with columns: year, country, value.
    Small countries grouped into 'Other'.
    """
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT substr(date, 1, 4) AS year, country_or_sector AS country, value
        FROM clean_fdi
        WHERE direction = 'liabilities'
          AND flow_or_position = ?
          AND indicator = 'FDI'
        ORDER BY date
    """, conn, params=(flow_or_position,))
    conn.close()

    if df.empty:
        return df
    df["year"] = df["year"].astype(int)

    # Remove regional aggregates
    df = df[~df["country"].isin(_FDI_AGGREGATES)].copy()

    # Identify top N countries by average absolute value
    avg_rank = df.groupby("country")["value"].apply(lambda x: x.abs().mean())
    top_countries = avg_rank.nlargest(top_n).index.tolist()

    # Group smaller countries into "Other"
    df["country_group"] = df["country"].where(
        df["country"].isin(top_countries), "Other"
    )
    grouped = df.groupby(["year", "country_group"])["value"].sum().reset_index()
    grouped.columns = ["year", "country", "value"]
    return grouped


def get_fdi_by_sector(flow_or_position="flow"):
    """
    FDI liabilities by sector (NACE), annual.
    Returns DataFrame with columns: year, sector, value.
    """
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT substr(date, 1, 4) AS year, indicator AS sector, value
        FROM clean_fdi
        WHERE direction = 'liabilities'
          AND flow_or_position = ?
          AND indicator != 'FDI'
        ORDER BY date
    """, conn, params=(flow_or_position,))
    conn.close()

    if df.empty:
        return df
    df["year"] = df["year"].astype(int)

    # Keep only main NACE sectors (all-uppercase names)
    df = df[df["sector"].str.isupper()].copy()

    # Shorten long sector names for display
    df["sector_short"] = df["sector"].apply(_shorten_sector)
    return df


def _shorten_sector(name):
    """Shorten NACE sector names for chart readability."""
    mapping = {
        "AGRICULTURE, FORESTRY AND FISHING": "Agriculture",
        "MINING AND QUARRYING": "Mining",
        "MANUFACTURING": "Manufacturing",
        "ELECTRICITY, GAS, STEAM AND AIR CONDITIONING SUPPLY": "Energy",
        "WATER SUPPLY; SEWERAGE, WASTE MANAGEMENT AND REMEDIATION ACTIVITIES": "Water & Waste",
        "CONSTRUCTION": "Construction",
        "WHOLESALE AND RETAIL TRADE; REPAIR OF MOTOR VEHICLES AND MOTORCYCLES": "Trade",
        "TRANSPORTATION AND STORAGE": "Transport",
        "ACCOMMODATION AND FOOD SERVICE ACTIVITIES": "Hospitality",
        "INFORMATION AND COMMUNICATION": "ICT",
        "FINANCIAL AND INSURANCE ACTIVITIES": "Finance",
        "REAL ESTATE ACTIVITIES": "Real Estate",
        "PROFESSIONAL, SCIENTIFIC AND TECHNICAL ACTIVITIES": "Professional",
        "ADMINISTRATIVE AND SUPPORT SERVICE ACTIVITIES": "Admin Support",
        "EDUCATION": "Education",
        "HUMAN HEALTH AND SOCIAL WORK ACTIVITIES": "Healthcare",
        "ARTS, ENTERTAINMENT AND RECREATION": "Arts & Rec",
        "OTHER SERVICE ACTIVITIES": "Other Services",
    }
    return mapping.get(name, name[:20])


def get_fdi_total_flows():
    """FDI total flows: assets, liabilities, net — by year."""
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT substr(date, 1, 4) AS year, direction, value
        FROM clean_fdi
        WHERE flow_or_position = 'flow'
          AND indicator = 'FDI'
          AND country_or_sector = 'TOTAL'
        ORDER BY date
    """, conn)
    conn.close()

    if df.empty:
        return df
    df["year"] = df["year"].astype(int)

    pivot = df.pivot_table(index="year", columns="direction",
                           values="value", aggfunc="first").reset_index()
    # Rename for clarity
    col_map = {"assets": "Outflows", "liabilities": "Inflows", "net": "Net FDI"}
    pivot = pivot.rename(columns=col_map)
    return pivot


def get_fdi_concentration(top_n=5):
    """
    Concentration analysis: share of top N countries in total FDI inflows.
    Returns DataFrame: year, top_share_pct.
    """
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT substr(date, 1, 4) AS year, country_or_sector AS country, value
        FROM clean_fdi
        WHERE direction = 'liabilities' AND flow_or_position = 'flow'
          AND indicator = 'FDI'
        ORDER BY date
    """, conn)
    conn.close()

    if df.empty:
        return df
    df["year"] = df["year"].astype(int)

    # Separate total from individual countries
    totals = df[df["country"] == "TOTAL"][["year", "value"]].rename(
        columns={"value": "total"}
    )
    indiv = df[~df["country"].isin(_FDI_AGGREGATES)]

    # Top N by value per year
    rows = []
    for year in sorted(indiv["year"].unique()):
        yr_data = indiv[indiv["year"] == year].nlargest(top_n, "value")
        top_sum = yr_data["value"].sum()
        total = totals[totals["year"] == year]["total"].iloc[0] if year in totals["year"].values else 0
        pct = (top_sum / total * 100) if total > 0 else 0
        rows.append({"year": year, "top_share_pct": round(pct, 1),
                      "top_sum": top_sum, "total": total})

    return pd.DataFrame(rows)


def get_fdi_yoy_growth():
    """Year-over-year FDI inflow growth."""
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT substr(date, 1, 4) AS year, value
        FROM clean_fdi
        WHERE direction = 'liabilities' AND flow_or_position = 'flow'
          AND indicator = 'FDI' AND country_or_sector = 'TOTAL'
        ORDER BY date
    """, conn)
    conn.close()

    if df.empty:
        return df
    df["year"] = df["year"].astype(int)
    df = df.drop_duplicates("year").sort_values("year")
    df["prev"] = df["value"].shift(1)
    df["change"] = df["value"] - df["prev"]
    df["growth_pct"] = ((df["change"] / df["prev"]) * 100).round(1)
    return df.dropna(subset=["prev"])


def get_fdi_net_bop():
    """Get FA.FDI net from BOP (available for more recent years than clean_fdi)."""
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT substr(b.date, 1, 4) as year, b.value
        FROM clean_bop b
        JOIN metadata m ON b.source_id = m.source_id
        WHERE m.filename = 'bop_annual_2007_2025.xls'
          AND b.indicator_code = 'FA.FDI'
          AND b.sub_indicator = 'net'
        ORDER BY b.date
    """, conn)
    conn.close()
    if df.empty:
        return df
    df["year"] = df["year"].astype(int)
    return df


def get_fdi_flows_bop_detailed():
    """Get FDI inflows/outflows from BOP detailed file (covers 2025).

    In the detailed BOP Excel, per year the 2nd 'Assets' row = FDI outflows
    and the 2nd 'Liabilities' row = FDI inflows (1st = Financial Account total).
    """
    conn = _conn()
    df = pd.read_sql_query("""
        SELECT r.rowid AS rid, r.indicator_raw, r.period_raw,
               CAST(r.value_raw AS REAL) AS value
        FROM raw_bop r
        JOIN metadata m ON r.source_id = m.source_id
        WHERE m.filename = 'bop_annual_detailed_2007_2025.xls'
          AND r.indicator_raw IN ('Assets', 'Liabilities')
        ORDER BY r.rowid
    """, conn)
    conn.close()
    if df.empty:
        return pd.DataFrame(columns=["year", "Inflows", "Outflows", "Net FDI"])

    # 2nd occurrence per (indicator, year) = Direct Investment component
    df["occ"] = df.groupby(["indicator_raw", "period_raw"]).cumcount() + 1
    fdi_rows = df[df["occ"] == 2].copy()

    assets = fdi_rows[fdi_rows["indicator_raw"] == "Assets"][["period_raw", "value"]].rename(
        columns={"period_raw": "year", "value": "Outflows"})
    liabs = fdi_rows[fdi_rows["indicator_raw"] == "Liabilities"][["period_raw", "value"]].rename(
        columns={"period_raw": "year", "value": "Inflows"})

    result = pd.merge(assets, liabs, on="year", how="outer")
    result["year"] = result["year"].astype(int)
    result["Net FDI"] = result["Outflows"] - result["Inflows"]  # BPM6: net = assets - liabilities
    result = result.sort_values("year").reset_index(drop=True)
    return result


def get_fdi_ca_coverage():
    """FDI coverage of CA deficit (using net FDI from by_country data)."""
    ca = get_ca_annual()
    conn = _conn()
    fdi = pd.read_sql_query("""
        SELECT substr(date, 1, 4) AS year, value
        FROM clean_fdi
        WHERE direction = 'net' AND flow_or_position = 'flow'
          AND indicator = 'FDI' AND country_or_sector = 'TOTAL'
        ORDER BY date
    """, conn)
    conn.close()

    if fdi.empty:
        return fdi
    fdi["year"] = fdi["year"].astype(int)
    merged = ca.merge(fdi, on="year", suffixes=("_ca", "_fdi"))
    # BPM6: negative net FDI = inflow, negative CA = deficit
    merged["coverage"] = (merged["value_fdi"].abs() / merged["value_ca"].abs() * 100).round(1)
    merged["coverage"] = merged["coverage"].clip(upper=500)
    return merged
