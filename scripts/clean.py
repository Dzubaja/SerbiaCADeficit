"""
Clean raw tables → standardized clean tables.

Transformations:
  - Parse period strings into ISO dates
  - Convert values to float
  - Standardize indicator names and codes
  - Assign units (EUR mn, %, etc.)
"""

import re, sqlite3, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DB_PATH


# ── Period parsing ─────────────────────────────────────────────────────

MONTHS = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    "januar": "01", "februar": "02", "mart": "03", "april": "04",
    "maj": "05", "jun": "06", "jul": "07", "avgust": "08",
    "septembar": "09", "oktobar": "10", "novembar": "11", "decembar": "12",
}

QUARTERS = {"Q1": "03", "Q2": "06", "Q3": "09", "Q4": "12",
            "I": "03", "II": "06", "III": "09", "IV": "12"}


def parse_period(raw, default_freq="annual"):
    """
    Convert raw period string to (iso_date, frequency).
    Returns (None, None) if unparseable.
    """
    if not raw:
        return None, None
    s = str(raw).strip()

    # Full ISO date: 2025-01-31
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m:
        return s, _guess_freq(s, default_freq)

    # Pure year: 2007
    m = re.match(r"^(19|20)\d{2}$", s)
    if m:
        return f"{s}-01-01", "annual"

    # Year-month: 2025-03
    m = re.match(r"^(20\d{2})-(\d{2})$", s)
    if m:
        return f"{s}-01", "monthly"

    # Quarter: 2025-Q1, 2025-III
    m = re.match(r"^(20\d{2})-(Q[1-4]|I{1,3}V?)$", s, re.I)
    if m:
        year = m.group(1)
        q = m.group(2).upper()
        month = QUARTERS.get(q, "12")
        return f"{year}-{month}-01", "quarterly"

    # Month-year: Jan 2025
    m = re.match(r"^([A-Za-z]+)\s*(20\d{2})$", s)
    if m:
        mon_str = m.group(1).lower()[:3]
        mon = MONTHS.get(mon_str)
        if mon:
            return f"{m.group(2)}-{mon}-01", "monthly"

    return None, None


def _guess_freq(date_str, default):
    """Guess frequency from a date string."""
    if date_str.endswith("-01-01"):
        return "annual"
    return default


# ── Value parsing ──────────────────────────────────────────────────────

def parse_value(raw):
    """Convert raw value string to float or None."""
    if not raw or str(raw).strip() in ("", "nan", "None", "...", "-", "n/a", "n.a."):
        return None
    s = str(raw).strip()
    # Remove thousands separators and normalize decimal
    s = s.replace(" ", "").replace("\u00a0", "")
    # Handle European format: 1.234,56 → 1234.56
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


# ── BOP indicator code mapping ─────────────────────────────────────────

BOP_CODE_MAP = {
    # Current account
    "current account": ("CA", "Current Account", "net"),
    "goods": ("CA.GOODS", "Goods", "net"),
    "goods, credit": ("CA.GOODS", "Goods", "credit"),
    "goods, debit": ("CA.GOODS", "Goods", "debit"),
    "export": ("CA.GOODS", "Goods - Exports", "credit"),
    "exports": ("CA.GOODS", "Goods - Exports", "credit"),
    "exports of goods": ("CA.GOODS", "Goods - Exports", "credit"),
    "import": ("CA.GOODS", "Goods - Imports", "debit"),
    "imports": ("CA.GOODS", "Goods - Imports", "debit"),
    "imports of goods": ("CA.GOODS", "Goods - Imports", "debit"),
    "services": ("CA.SERVICES", "Services", "net"),
    "services, credit": ("CA.SERVICES", "Services", "credit"),
    "services, debit": ("CA.SERVICES", "Services", "debit"),
    "primary income": ("CA.PRIMARY_INCOME", "Primary Income", "net"),
    "primary income, credit": ("CA.PRIMARY_INCOME", "Primary Income", "credit"),
    "primary income, debit": ("CA.PRIMARY_INCOME", "Primary Income", "debit"),
    "secondary income": ("CA.SECONDARY_INCOME", "Secondary Income", "net"),
    "secondary income, credit": ("CA.SECONDARY_INCOME", "Secondary Income", "credit"),
    "secondary income, debit": ("CA.SECONDARY_INCOME", "Secondary Income", "debit"),
    "compensation of employees": ("CA.PRIMARY_INCOME.COMPENSATION", "Compensation of Employees", "net"),
    "investment income": ("CA.PRIMARY_INCOME.INVESTMENT", "Investment Income", "net"),
    "personal transfers": ("CA.SECONDARY_INCOME.PERSONAL", "Personal Transfers", "net"),
    "remittances": ("CA.SECONDARY_INCOME.REMITTANCES", "Remittances", "net"),

    # Capital account
    "capital account": ("KA", "Capital Account", "net"),

    # Financial account
    "financial account": ("FA", "Financial Account", "net"),
    "direct investment": ("FA.FDI", "Foreign Direct Investment", "net"),
    "direct investment, net": ("FA.FDI", "Foreign Direct Investment", "net"),
    "foreign direct investment": ("FA.FDI", "Foreign Direct Investment", "net"),
    "portfolio investment": ("FA.PORTFOLIO", "Portfolio Investment", "net"),
    "other investment": ("FA.OTHER", "Other Investment", "net"),
    "financial derivatives": ("FA.DERIVATIVES", "Financial Derivatives", "net"),
    "reserve assets": ("FA.RESERVES", "Reserve Assets", "net"),

    # Errors
    "errors and omissions": ("EO", "Errors and Omissions", "net"),
    "net errors and omissions": ("EO", "Errors and Omissions", "net"),
}


def map_bop_indicator(raw_indicator):
    """Map raw indicator text to (code, name, sub_indicator)."""
    if not raw_indicator:
        return None, None, None
    key = raw_indicator.strip().lower()
    # Remove leading numbers, dots, spaces
    key = re.sub(r"^\d+\.?\s*", "", key)
    key = re.sub(r"\s+", " ", key).strip()

    # Direct match
    if key in BOP_CODE_MAP:
        return BOP_CODE_MAP[key]

    # Partial matches
    for pattern, result in BOP_CODE_MAP.items():
        if pattern in key or key in pattern:
            return result

    # Fallback: use cleaned text as both code and name
    code = re.sub(r"[^a-z0-9_]", "_", key).upper()[:50]
    name = raw_indicator.strip()[:100]
    return code, name, "net"


# ── Cleaning functions per table ───────────────────────────────────────

def clean_bop(conn):
    """Clean raw_bop → clean_bop."""
    print("  Cleaning BOP...")
    conn.execute("DELETE FROM clean_bop")

    rows = conn.execute("""
        SELECT r.source_id, r.indicator_raw, r.period_raw, r.value_raw, r.unit_raw,
               m.frequency
        FROM raw_bop r
        JOIN metadata m ON r.source_id = m.source_id
    """).fetchall()

    inserts = []
    for source_id, ind_raw, period_raw, val_raw, unit_raw, freq in rows:
        date, frequency = parse_period(period_raw, freq or "annual")
        if not date:
            continue
        value = parse_value(val_raw)
        if value is None:
            continue
        code, name, sub = map_bop_indicator(ind_raw)
        if not code:
            continue
        unit = unit_raw if unit_raw and unit_raw != "nan" else "EUR mn"
        inserts.append((source_id, date, frequency, code, name, sub, value, unit))

    conn.executemany("""
        INSERT INTO clean_bop
        (source_id, date, frequency, indicator_code, indicator_name, sub_indicator, value, unit)
        VALUES (?,?,?,?,?,?,?,?)
    """, inserts)
    print(f"    ->{len(inserts)} clean BOP records")


def clean_services(conn):
    """Clean raw_services → clean_services."""
    print("  Cleaning services...")
    conn.execute("DELETE FROM clean_services")

    rows = conn.execute("""
        SELECT r.source_id, r.indicator_raw, r.country, r.period_raw, r.value_raw,
               r.unit_raw, m.frequency
        FROM raw_services r
        JOIN metadata m ON r.source_id = m.source_id
    """).fetchall()

    inserts = []
    for source_id, ind_raw, country, period_raw, val_raw, unit_raw, freq in rows:
        date, frequency = parse_period(period_raw, freq or "annual")
        if not date:
            continue
        value = parse_value(val_raw)
        if value is None:
            continue

        service_type = ind_raw.strip() if ind_raw else "Total"
        country = country.strip() if country and country != "nan" else None
        direction = "net"
        lower = (ind_raw or "").lower()
        if "credit" in lower or "export" in lower:
            direction = "credit"
        elif "debit" in lower or "import" in lower:
            direction = "debit"

        unit = unit_raw if unit_raw and unit_raw != "nan" else "EUR mn"
        inserts.append((source_id, date, frequency, service_type, country, direction, value, unit))

    conn.executemany("""
        INSERT INTO clean_services
        (source_id, date, frequency, service_type, country, direction, value, unit)
        VALUES (?,?,?,?,?,?,?,?)
    """, inserts)
    print(f"    ->{len(inserts)} clean services records")


def clean_fdi(conn):
    """Clean raw_fdi → clean_fdi."""
    print("  Cleaning FDI...")
    conn.execute("DELETE FROM clean_fdi")

    rows = conn.execute("""
        SELECT r.source_id, r.indicator_raw, r.country_or_sector, r.period_raw,
               r.value_raw, r.unit_raw, m.frequency, m.description, m.filename
        FROM raw_fdi r
        JOIN metadata m ON r.source_id = m.source_id
    """).fetchall()

    inserts = []
    for source_id, ind_raw, cs, period_raw, val_raw, unit_raw, freq, desc, fname in rows:
        date, frequency = parse_period(period_raw, freq or "annual")
        if not date or date < "1990-01-01":
            continue
        value = parse_value(val_raw)
        if value is None:
            continue

        flow_or_pos = "position" if "position" in (desc or "").lower() else "flow"
        fname = fname or ""
        ind_raw = (ind_raw or "").strip()
        cs_raw = (cs or "").strip()

        # ── by_country files: indicator_raw = direction label ──────────
        if "by_country" in fname:
            lower = ind_raw.lower()
            if lower == "net" or "net" in lower:
                direction = "net"
            elif "asset" in lower:
                direction = "assets"
            elif "liabilit" in lower:
                direction = "liabilities"
            else:
                direction = "net"
            indicator = "FDI"
            cs_clean = cs_raw if cs_raw and cs_raw != "nan" else None

        # ── by_activity files: indicator_raw = sector name ────────────
        else:
            direction = "liabilities"  # NBS activity files show inward FDI
            indicator = ind_raw if ind_raw and ind_raw != "nan" else "Unknown"
            # Skip sub-items ("of which:" prefix)
            if indicator.lower().startswith("of which"):
                continue
            # Skip total/aggregate rows
            if indicator.lower().startswith("total"):
                continue
            if indicator.lower().startswith("not allocated"):
                continue
            cs_clean = cs_raw if cs_raw and cs_raw != "nan" else None

        unit = unit_raw if unit_raw and unit_raw != "nan" else "EUR mn"
        inserts.append((source_id, date, frequency, flow_or_pos, indicator, cs_clean, direction, value, unit))

    conn.executemany("""
        INSERT INTO clean_fdi
        (source_id, date, frequency, flow_or_position, indicator, country_or_sector, direction, value, unit)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, inserts)
    print(f"    ->{len(inserts)} clean FDI records")


def clean_external_debt(conn):
    """Clean raw_external_debt → clean_external_debt."""
    print("  Cleaning external debt...")
    conn.execute("DELETE FROM clean_external_debt")

    rows = conn.execute("""
        SELECT r.source_id, r.indicator_raw, r.period_raw, r.value_raw,
               r.unit_raw, m.frequency, m.filename
        FROM raw_external_debt r
        JOIN metadata m ON r.source_id = m.source_id
    """).fetchall()

    inserts = []
    for source_id, ind_raw, period_raw, val_raw, unit_raw, freq, fname in rows:
        date, frequency = parse_period(period_raw, freq or "quarterly")
        if not date:
            continue
        value = parse_value(val_raw)
        if value is None:
            continue

        ind = (ind_raw or "").strip()
        debtor_type = _classify_debtor(ind)
        creditor_type = _classify_creditor(ind, fname)
        maturity = "long_term" if "long" in ind.lower() else (
            "short_term" if "short" in ind.lower() else "total"
        )
        unit = unit_raw if unit_raw and unit_raw != "nan" else "EUR mn"
        inserts.append((source_id, date, frequency, debtor_type, creditor_type, maturity, value, unit))

    conn.executemany("""
        INSERT INTO clean_external_debt
        (source_id, date, frequency, debtor_type, creditor_type, maturity, value, unit)
        VALUES (?,?,?,?,?,?,?,?)
    """, inserts)
    print(f"    ->{len(inserts)} clean external debt records")


def _classify_debtor(indicator):
    lower = indicator.lower()
    if "public" in lower or "government" in lower or "state" in lower:
        return "public_sector"
    if "private" in lower or "enterprise" in lower:
        return "private_sector"
    if "bank" in lower:
        return "banks"
    if "nbs" in lower or "central bank" in lower or "national bank" in lower:
        return "nbs"
    return "total"


def _classify_creditor(indicator, filename):
    if "creditor" in (filename or "").lower():
        return indicator[:100]
    return "total"


def clean_iip(conn):
    """Clean raw_iip → clean_iip."""
    print("  Cleaning IIP...")
    conn.execute("DELETE FROM clean_iip")

    rows = conn.execute("""
        SELECT r.source_id, r.indicator_raw, r.period_raw, r.value_raw,
               r.unit_raw, m.frequency
        FROM raw_iip r
        JOIN metadata m ON r.source_id = m.source_id
    """).fetchall()

    inserts = []
    for source_id, ind_raw, period_raw, val_raw, unit_raw, freq in rows:
        date, frequency = parse_period(period_raw, freq or "quarterly")
        if not date:
            continue
        value = parse_value(val_raw)
        if value is None:
            continue

        indicator = (ind_raw or "").strip()
        direction = "net"
        lower = indicator.lower()
        if "asset" in lower:
            direction = "assets"
        elif "liabilit" in lower:
            direction = "liabilities"

        unit = unit_raw if unit_raw and unit_raw != "nan" else "EUR mn"
        inserts.append((source_id, date, frequency, indicator, direction, value, unit))

    conn.executemany("""
        INSERT INTO clean_iip
        (source_id, date, frequency, indicator, direction, value, unit)
        VALUES (?,?,?,?,?,?,?)
    """, inserts)
    print(f"    ->{len(inserts)} clean IIP records")


def clean_fx_reserves(conn):
    """Clean raw_fx_reserves → clean_fx_reserves."""
    print("  Cleaning FX reserves...")
    conn.execute("DELETE FROM clean_fx_reserves")

    rows = conn.execute("""
        SELECT r.source_id, r.indicator_raw, r.period_raw, r.value_raw,
               r.unit_raw, m.frequency
        FROM raw_fx_reserves r
        JOIN metadata m ON r.source_id = m.source_id
    """).fetchall()

    inserts = []
    for source_id, ind_raw, period_raw, val_raw, unit_raw, freq in rows:
        date, frequency = parse_period(period_raw, freq or "monthly")
        if not date or date < "1990-01-01":
            continue
        value = parse_value(val_raw)
        if value is None:
            continue

        indicator = (ind_raw or "").strip()
        unit = unit_raw if unit_raw and unit_raw != "nan" else "EUR mn"
        inserts.append((source_id, date, frequency, indicator, value, unit))

    conn.executemany("""
        INSERT INTO clean_fx_reserves
        (source_id, date, frequency, indicator, value, unit)
        VALUES (?,?,?,?,?,?)
    """, inserts)
    print(f"    ->{len(inserts)} clean FX reserves records")


def clean_fx_rates(conn):
    """Clean raw_fx_rates → clean_fx_rates."""
    print("  Cleaning FX rates...")
    conn.execute("DELETE FROM clean_fx_rates")

    rows = conn.execute("""
        SELECT r.source_id, r.currency, r.period_raw, r.value_raw,
               r.unit_raw, m.frequency
        FROM raw_fx_rates r
        JOIN metadata m ON r.source_id = m.source_id
    """).fetchall()

    inserts = []
    for source_id, currency, period_raw, val_raw, unit_raw, freq in rows:
        date, frequency = parse_period(period_raw, freq or "daily")
        if not date or date < "1990-01-01":
            continue
        value = parse_value(val_raw)
        if value is None:
            continue

        currency = (currency or "").strip()
        # Clean up currency codes: remove (100), newlines, etc.
        currency = re.sub(r"\s*\(\d+\)\s*", "", currency)
        currency = re.sub(r"\s+", " ", currency).strip().upper()[:10]
        # Skip non-currency entries
        if not currency or currency.startswith("COL_"):
            continue
        rate_type = "middle"
        unit = "RSD per unit"
        inserts.append((source_id, date, frequency, currency, rate_type, value, unit))

    conn.executemany("""
        INSERT INTO clean_fx_rates
        (source_id, date, frequency, currency, rate_type, value, unit)
        VALUES (?,?,?,?,?,?,?)
    """, inserts)
    print(f"    ->{len(inserts)} clean FX rates records")


def clean_macro(conn):
    """Clean raw_macro → clean_macro."""
    print("  Cleaning macro indicators...")
    conn.execute("DELETE FROM clean_macro")

    rows = conn.execute("""
        SELECT r.source_id, r.indicator_raw, r.period_raw, r.value_raw,
               r.unit_raw, m.frequency
        FROM raw_macro r
        JOIN metadata m ON r.source_id = m.source_id
    """).fetchall()

    inserts = []
    for source_id, ind_raw, period_raw, val_raw, unit_raw, freq in rows:
        date, frequency = parse_period(period_raw, freq or "annual")
        if not date or date < "1990-01-01":
            continue
        value = parse_value(val_raw)
        if value is None:
            continue

        indicator = (ind_raw or "").strip()
        if not indicator:
            continue
        # Generate code: keep Cyrillic and Latin chars, replace rest with _
        code = re.sub(r"[^\w]", "_", indicator, flags=re.UNICODE)
        code = re.sub(r"_+", "_", code).strip("_")[:80]
        unit = unit_raw if unit_raw and unit_raw != "nan" else ""
        inserts.append((source_id, date, frequency, code, indicator, value, unit))

    conn.executemany("""
        INSERT INTO clean_macro
        (source_id, date, frequency, indicator_code, indicator_name, value, unit)
        VALUES (?,?,?,?,?,?,?)
    """, inserts)
    print(f"    ->{len(inserts)} clean macro records")


# ── Main ───────────────────────────────────────────────────────────────

def clean_all():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    clean_bop(conn)
    clean_services(conn)
    clean_fdi(conn)
    clean_external_debt(conn)
    clean_iip(conn)
    clean_fx_reserves(conn)
    clean_fx_rates(conn)
    clean_macro(conn)

    conn.commit()
    conn.close()
    print("\nCleaning complete.")


if __name__ == "__main__":
    clean_all()
