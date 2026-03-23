"""
Extract data from downloaded NBS Excel files into raw SQLite tables.

NBS Excel files are heterogeneous — each category needs its own parser.
This module provides a generic "long table" extractor that works for most
files, plus category-specific overrides where needed.
"""

import json, re, sqlite3, sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import SOURCES, RAW_EXCEL_DIR, DB_PATH


# ── Helpers ────────────────────────────────────────────────────────────

def get_or_create_source(conn, filename, url, category, desc, freq, meth):
    """Register a source file in metadata, return source_id."""
    row = conn.execute(
        "SELECT source_id FROM metadata WHERE filename = ?", (filename,)
    ).fetchone()
    if row:
        return row[0]

    filepath = RAW_EXCEL_DIR / filename
    size = filepath.stat().st_size if filepath.exists() else 0
    cur = conn.execute(
        """INSERT INTO metadata (filename, url, category, description,
           frequency, methodology, download_date, file_size_bytes)
           VALUES (?,?,?,?,?,?,?,?)""",
        (filename, url, category, desc, freq, meth,
         datetime.now().isoformat(), size),
    )
    return cur.lastrowid


def update_sheets_parsed(conn, source_id, sheets):
    conn.execute(
        "UPDATE metadata SET sheets_parsed = ? WHERE source_id = ?",
        (json.dumps(sheets), source_id),
    )


def safe_read_excel(filepath, sheet=0, header=None):
    """Read an Excel file, trying xlrd for .xls and openpyxl for .xlsx."""
    ext = filepath.suffix.lower()
    engine = "xlrd" if ext == ".xls" else "openpyxl"
    try:
        return pd.read_excel(filepath, sheet_name=sheet, header=header, engine=engine)
    except Exception as e:
        print(f"    WARN: Could not read {filepath.name} sheet={sheet}: {e}")
        return None


def get_sheet_names(filepath):
    """Return list of sheet names."""
    ext = filepath.suffix.lower()
    engine = "xlrd" if ext == ".xls" else "openpyxl"
    try:
        xls = pd.ExcelFile(filepath, engine=engine)
        return xls.sheet_names
    except Exception:
        return []


# ── Generic extractor (indicator × period matrix) ─────────────────────

def extract_matrix(filepath, source_id, conn, table_name,
                   indicator_col=0, data_start_col=1, data_start_row=None,
                   unit="EUR mn", extra_cols=None):
    """
    Extract a typical NBS matrix: rows = indicators, columns = periods.

    Parameters:
        indicator_col: column index for the indicator label
        data_start_col: first column index with numeric data
        data_start_row: first data row (auto-detected if None)
        extra_cols: dict mapping extra column name → column index
    """
    sheets = get_sheet_names(filepath)
    parsed_sheets = []

    for sheet_name in sheets:
        df = safe_read_excel(filepath, sheet=sheet_name)
        if df is None or df.empty:
            continue

        # Auto-detect header row: first row where most cells look like years/dates
        header_row = _find_header_row(df)
        if header_row is None:
            continue

        periods = []
        for col_idx in range(data_start_col, len(df.columns)):
            val = df.iloc[header_row, col_idx]
            period_str = _normalize_period(val)
            if period_str:
                periods.append((col_idx, period_str))

        if not periods:
            continue

        start_row = header_row + 1 if data_start_row is None else data_start_row
        rows_to_insert = []

        for row_idx in range(start_row, len(df)):
            indicator = str(df.iloc[row_idx, indicator_col]).strip()
            if not indicator or indicator == "nan":
                continue

            extras = {}
            if extra_cols:
                for name, cidx in extra_cols.items():
                    extras[name] = str(df.iloc[row_idx, cidx]).strip()

            for col_idx, period_str in periods:
                val = df.iloc[row_idx, col_idx]
                val_str = str(val).strip() if pd.notna(val) else ""

                base = (source_id, sheet_name, row_idx, indicator, period_str, val_str, unit)

                if table_name == "raw_services":
                    country = extras.get("country", "")
                    rows_to_insert.append(base[:4] + (country,) + base[4:])
                elif table_name == "raw_fdi":
                    cs = extras.get("country_or_sector", "")
                    rows_to_insert.append(base[:4] + (cs,) + base[4:])
                elif table_name == "raw_fx_rates":
                    currency = extras.get("currency", indicator)
                    rows_to_insert.append(
                        (source_id, sheet_name, row_idx, currency, period_str, val_str, unit)
                    )
                else:
                    rows_to_insert.append(base)

        if rows_to_insert:
            placeholders = ",".join(["?"] * len(rows_to_insert[0]))
            col_map = {
                "raw_bop": "(source_id, sheet_name, row_index, indicator_raw, period_raw, value_raw, unit_raw)",
                "raw_services": "(source_id, sheet_name, row_index, indicator_raw, country, period_raw, value_raw, unit_raw)",
                "raw_fdi": "(source_id, sheet_name, row_index, indicator_raw, country_or_sector, period_raw, value_raw, unit_raw)",
                "raw_external_debt": "(source_id, sheet_name, row_index, indicator_raw, period_raw, value_raw, unit_raw)",
                "raw_iip": "(source_id, sheet_name, row_index, indicator_raw, period_raw, value_raw, unit_raw)",
                "raw_fx_reserves": "(source_id, sheet_name, row_index, indicator_raw, period_raw, value_raw, unit_raw)",
                "raw_fx_rates": "(source_id, sheet_name, row_index, currency, period_raw, value_raw, unit_raw)",
                "raw_macro": "(source_id, sheet_name, row_index, indicator_raw, period_raw, value_raw, unit_raw)",
            }
            cols = col_map.get(table_name, col_map["raw_bop"])
            conn.executemany(
                f"INSERT INTO {table_name} {cols} VALUES ({placeholders})",
                rows_to_insert,
            )
            parsed_sheets.append(sheet_name)
            print(f"    Sheet '{sheet_name}': {len(rows_to_insert)} cells")

    return parsed_sheets


def _find_header_row(df, max_scan=20):
    """
    Find the row that contains period headers (years or month names).
    Only counts year-like values from column 1 onward to avoid matching
    transposed data where years are in column 0.
    """
    for i in range(min(max_scan, len(df))):
        year_count = 0
        for j, val in enumerate(df.iloc[i]):
            # Skip column 0 — in transposed files, column 0 has years as row keys,
            # not as column headers
            if j == 0:
                continue
            # Check for datetime objects
            if isinstance(val, datetime):
                year_count += 1
                continue
            try:
                ts = pd.Timestamp(val)
                if not pd.isna(ts) and ts.year >= 1990:
                    year_count += 1
                    continue
            except Exception:
                pass
            s = str(val).strip()
            # Check for year-like values (handle float years like "2007.0")
            if re.match(r"^(19|20)\d{2}(\.0)?$", s):
                year_count += 1
            # Check for year with dot: "2007."
            elif re.match(r"^(19|20)\d{2}\.$", s):
                year_count += 1
            # Check for month-year patterns
            elif re.match(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|I|II|III|IV|Q[1-4])", s, re.I):
                year_count += 1
            # Check for embedded dates like "УКУПНО\n31.12.2010."
            elif re.search(r"\d{1,2}\.\d{1,2}\.(19|20)\d{2}", s):
                year_count += 1
        if year_count >= 2:
            return i
    return None


def _normalize_period(val):
    """Convert a cell value to a period string."""
    if pd.isna(val):
        return None
    s = str(val).strip()

    # Pure year: 2007, 2025, 2007.0, 2007.
    if re.match(r"^(19|20)\d{2}(\.0?)?$", s):
        return re.sub(r"\.0?$", "", s)

    # Quarter: Q1 2025, I/2025, etc.
    m = re.match(r"^(Q[1-4]|I{1,3}V?)\s*[/.]?\s*(20\d{2})$", s, re.I)
    if m:
        return f"{m.group(2)}-{m.group(1).upper()}"

    # Month name: Jan 2025, January 2025
    m = re.match(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s*[./]?\s*(20\d{2})$", s, re.I)
    if m:
        months = {"jan":"01","feb":"02","mar":"03","apr":"04","may":"05","jun":"06",
                   "jul":"07","aug":"08","sep":"09","oct":"10","nov":"11","dec":"12"}
        mon = months.get(m.group(1)[:3].lower(), "01")
        return f"{m.group(2)}-{mon}"

    # Date-like: 2025-01-31
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m:
        return s

    # European date: 31.12.2010. or 31.12.2010
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})\.?", s)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"

    # Datetime object
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")

    # Try pandas Timestamp
    try:
        ts = pd.Timestamp(val)
        if not pd.isna(ts):
            return ts.strftime("%Y-%m-%d")
    except Exception:
        pass

    return None


# ── Category dispatchers ──────────────────────────────────────────────

TABLE_MAP = {
    "bop": "raw_bop",
    "services": "raw_services",
    "tourism": "raw_services",       # tourism is a subset of services
    "fdi": "raw_fdi",
    "external_debt": "raw_external_debt",
    "iip": "raw_iip",
    "fx_reserves": "raw_fx_reserves",
    "fx_rates": "raw_fx_rates",
    "macro": "raw_macro",
}


def _detect_layout(filepath, df):
    """
    Auto-detect column layout by inspecting the first data rows.
    Returns (indicator_col, data_start_col).
    """
    if len(df.columns) < 2:
        return 0, 1

    # Check if col 0 has item codes (like "1", "1.1", "1.A")
    code_count = 0
    empty_count = 0
    for i in range(min(20, len(df))):
        val = str(df.iloc[i, 0]).strip()
        if re.match(r"^[\d]+\.?[A-Za-z]?\.?\d*$", val):
            code_count += 1
        if val in ("", "nan", "None") or pd.isna(df.iloc[i, 0]):
            empty_count += 1

    if code_count >= 3:
        return 1, 2  # indicator in col 1, data from col 2

    # If col 0 is mostly empty and col 1 has text, use col 1
    if empty_count >= 15 and len(df.columns) >= 3:
        text_count = 0
        for i in range(min(20, len(df))):
            val = str(df.iloc[i, 1]).strip()
            if val and val != "nan" and len(val) > 3:
                text_count += 1
        if text_count >= 3:
            return 1, 2

    return 0, 1


def _extract_fdi_grouped(filepath, source_id, conn):
    """
    Extract FDI by_country files with grouped sub-columns per year.
    Layout: col 0 = country, then (Assets, Liabilities, Net) repeated per year.
    """
    sheets = get_sheet_names(filepath)
    parsed = []

    for sheet_name in sheets:
        df = safe_read_excel(filepath, sheet=sheet_name)
        if df is None or df.empty:
            continue

        # Find the row containing year headers (in cols 1+)
        year_row = None
        year_cols = []
        for i in range(min(15, len(df))):
            found = []
            for j in range(1, len(df.columns)):
                s = str(df.iloc[i, j]).strip()
                if re.match(r"^(19|20)\d{2}(\.0)?$", s):
                    found.append((j, s.replace(".0", "")))
            if len(found) >= 3:
                year_row = i
                year_cols = found
                break

        if year_row is None:
            continue

        # Sub-column count = gap between consecutive years
        sub_count = year_cols[1][0] - year_cols[0][0]

        # Read sub-header labels from the row below the years
        sub_row = year_row + 1
        sub_labels = []
        for k in range(sub_count):
            col = year_cols[0][0] + k
            if col < len(df.columns) and sub_row < len(df):
                raw_label = str(df.iloc[sub_row, col]).strip()
                low = raw_label.lower()
                # Check "net" before "asset" because the Net header
                # is "FDI, net (=assets - liabilities)" which contains "asset"
                if "net" in low:
                    sub_labels.append("Net")
                elif "asset" in low:
                    sub_labels.append("Assets")
                elif "liabilit" in low:
                    sub_labels.append("Liabilities")
                else:
                    sub_labels.append(raw_label or f"col_{k}")
            else:
                sub_labels.append(f"col_{k}")

        # Build column mapping: col_idx → (year, direction_label)
        col_map = {}
        for yc, yr in year_cols:
            for k, label in enumerate(sub_labels):
                col_map[yc + k] = (yr, label)

        # Find first data row (skip sub-headers and blank/numbering rows)
        data_start = sub_row + 1
        while data_start < len(df):
            val = str(df.iloc[data_start, 0]).strip()
            if val and val != "nan" and len(val) > 1:
                break
            data_start += 1

        # Extract data
        rows_to_insert = []
        for row_idx in range(data_start, len(df)):
            country = str(df.iloc[row_idx, 0]).strip()
            if not country or country == "nan":
                continue

            for col_idx, (yr, direction) in col_map.items():
                if col_idx >= len(df.columns):
                    continue
                val = df.iloc[row_idx, col_idx]
                val_str = str(val).strip() if pd.notna(val) else ""
                if val_str in ("", "*", "nan"):
                    continue

                rows_to_insert.append((
                    source_id, sheet_name, row_idx,
                    direction,   # indicator_raw = Assets/Liabilities/Net
                    country,     # country_or_sector
                    yr,          # period_raw
                    val_str,     # value_raw
                    "EUR mn",    # unit_raw
                ))

        if rows_to_insert:
            conn.executemany(
                """INSERT INTO raw_fdi
                   (source_id, sheet_name, row_index, indicator_raw, country_or_sector,
                    period_raw, value_raw, unit_raw)
                   VALUES (?,?,?,?,?,?,?,?)""",
                rows_to_insert,
            )
            parsed.append(sheet_name)
            print(f"    Sheet '{sheet_name}': {len(rows_to_insert)} cells")

    return parsed


def extract_file(filename, url, category, desc, freq, meth, conn):
    """Extract a single source file into the appropriate raw table."""
    filepath = RAW_EXCEL_DIR / filename
    if not filepath.exists():
        print(f"  SKIP (not downloaded): {filename}")
        return

    print(f"  EXTRACT {filename} [{category}]")
    source_id = get_or_create_source(conn, filename, url, category, desc, freq, meth)
    table = TABLE_MAP.get(category, "raw_macro")

    # FDI by_country files have grouped sub-columns — use dedicated extractor
    if category == "fdi" and "by_country" in filename:
        sheets = _extract_fdi_grouped(filepath, source_id, conn)
        update_sheets_parsed(conn, source_id, sheets)
        return

    # Try auto layout for FX reserves, macro, FX rates, ext debt by creditor
    if category in ("fx_reserves", "macro", "fx_rates") or (
        category == "external_debt" and "creditor" in filename
    ):
        sheets = _extract_auto(filepath, source_id, conn, table)
        update_sheets_parsed(conn, source_id, sheets)
        return

    # For services/tourism by country, the country might be in col 0 or 1
    extra = None
    if "by_country" in filename:
        if category in ("services", "tourism"):
            extra = {"country": 0}
    elif "by_activity" in filename or "branch_of_activity" in filename:
        extra = {"country_or_sector": 0}

    # Auto-detect indicator column for standard matrix files
    indicator_col = 0
    data_start_col = 1
    if extra:
        indicator_col = 1 if extra.get("country", extra.get("country_or_sector")) == 0 else 0
        data_start_col = max(indicator_col + 1, 2)
    else:
        # Peek at the file to detect layout
        sheet0 = safe_read_excel(filepath)
        if sheet0 is not None:
            indicator_col, data_start_col = _detect_layout(filepath, sheet0)

    sheets = extract_matrix(
        filepath, source_id, conn, table,
        indicator_col=indicator_col,
        data_start_col=data_start_col,
        extra_cols=extra,
    )
    update_sheets_parsed(conn, source_id, sheets)


MONTH_MAP = {
    # English
    "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
    "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    # Serbian Cyrillic
    "\u0458\u0430\u043d": "01", "\u0444\u0435\u0431": "02", "\u043c\u0430\u0440": "03",
    "\u0430\u043f\u0440": "04", "\u043c\u0430\u0458": "05", "\u0458\u0443\u043d": "06",
    "\u0458\u0443\u043b": "07", "\u0430\u0432\u0433": "08", "\u0441\u0435\u043f": "09",
    "\u043e\u043a\u0442": "10", "\u043d\u043e\u0432": "11", "\u0434\u0435\u0446": "12",
}


def _month_from_text(text):
    """Try to extract month number from a text string."""
    if not text:
        return None
    s = text.strip().rstrip(".").lower()
    for prefix, month in MONTH_MAP.items():
        if s.startswith(prefix):
            return month
    return None


def _extract_auto(filepath, source_id, conn, table_name):
    """
    Extract files with various layouts: standard matrix, transposed,
    and year+month sub-row structures (FX reserves, macro, FX rates).
    """
    sheets = get_sheet_names(filepath)
    parsed = []

    for sheet_name in sheets:
        df = safe_read_excel(filepath, sheet=sheet_name)
        if df is None or df.empty:
            continue

        # Try standard matrix first
        header_row = _find_header_row(df)
        if header_row is not None:
            indicator_col, data_start_col = _detect_layout(filepath, df)
            periods = []
            for col_idx in range(data_start_col, len(df.columns)):
                val = df.iloc[header_row, col_idx]
                period_str = _normalize_period(val)
                if period_str:
                    periods.append((col_idx, period_str))

            if periods:
                start_row = header_row + 1
                rows_to_insert = []
                for row_idx in range(start_row, len(df)):
                    indicator = str(df.iloc[row_idx, indicator_col]).strip()
                    if not indicator or indicator == "nan":
                        continue
                    for col_idx, period_str in periods:
                        val = df.iloc[row_idx, col_idx]
                        val_str = str(val).strip() if pd.notna(val) else ""
                        unit = "RSD per unit" if table_name == "raw_fx_rates" else ""
                        if table_name == "raw_fx_rates":
                            rows_to_insert.append(
                                (source_id, sheet_name, row_idx, indicator, period_str, val_str, unit)
                            )
                        else:
                            rows_to_insert.append(
                                (source_id, sheet_name, row_idx, indicator, period_str, val_str, unit)
                            )
                if rows_to_insert:
                    _insert_raw(conn, table_name, rows_to_insert)
                    parsed.append(sheet_name)
                    print(f"    Sheet '{sheet_name}': {len(rows_to_insert)} cells")
                continue

        # --- Transposed layout: years in rows, indicators in columns ---

        # Find column header row (row with indicator names across columns)
        indicator_row = None
        for i in range(min(15, len(df))):
            text_count = 0
            for j in range(2, min(10, len(df.columns))):
                val = str(df.iloc[i, j]).strip()
                if val and val != "nan" and len(val) > 2:
                    text_count += 1
            if text_count >= 2:
                indicator_row = i
                break

        if indicator_row is None:
            continue

        # Find the column with years
        year_col = None
        for col in range(min(3, len(df.columns))):
            yr_count = 0
            for row in range(indicator_row + 1, min(indicator_row + 30, len(df))):
                val = df.iloc[row, col]
                s = str(val).strip()
                if re.match(r"^(19|20)\d{2}(\.0)?$", s):
                    yr_count += 1
                elif isinstance(val, datetime):
                    yr_count += 1
            if yr_count >= 3:
                year_col = col
                break

        if year_col is None:
            continue

        # Detect if there's a month column (year+month sub-rows)
        # Check if there's a column between year_col and the first data col
        # that has month names
        month_col = None
        first_data_col = year_col + 1
        for col in range(year_col + 1, min(year_col + 3, len(df.columns))):
            month_count = 0
            for row in range(indicator_row + 2, min(indicator_row + 30, len(df))):
                val = str(df.iloc[row, col]).strip()
                if _month_from_text(val):
                    month_count += 1
            if month_count >= 3:
                month_col = col
                first_data_col = col + 1
                break

        # Collect indicator names from column headers
        indicators = {}
        for col_idx in range(first_data_col, len(df.columns)):
            name = str(df.iloc[indicator_row, col_idx]).strip()
            if not name or name == "nan":
                # Try row above or below
                for try_row in [indicator_row - 1, indicator_row + 1]:
                    if 0 <= try_row < len(df):
                        name = str(df.iloc[try_row, col_idx]).strip()
                        if name and name != "nan":
                            break
                if not name or name == "nan":
                    name = f"col_{col_idx}"
            # Clean up newlines in indicator names
            name = re.sub(r"\s+", " ", name).strip()
            indicators[col_idx] = name

        if not indicators:
            continue

        # Find data start row (skip header rows + numbering rows)
        data_start = indicator_row + 1
        # Skip rows that have numbers like "1", "2", "3" as column numbering
        for row in range(indicator_row + 1, min(indicator_row + 5, len(df))):
            all_nums = True
            for col_idx in indicators:
                val = str(df.iloc[row, col_idx]).strip()
                if val and val != "nan" and not re.match(r"^\d+\.?\d*$", val):
                    all_nums = False
                    break
            if all_nums:
                data_start = row + 1
            else:
                break

        # Extract data
        rows_to_insert = []
        current_year = None

        for row_idx in range(data_start, len(df)):
            # Get year (carry forward if empty)
            year_val = df.iloc[row_idx, year_col]
            year_str = str(year_val).strip() if pd.notna(year_val) else ""

            if re.match(r"^(19|20)\d{2}(\.0)?$", year_str):
                current_year = year_str.replace(".0", "")
            elif isinstance(year_val, datetime):
                current_year = str(year_val.year)

            if not current_year:
                continue

            # Determine period
            if month_col is not None:
                month_val = str(df.iloc[row_idx, month_col]).strip()
                month_num = _month_from_text(month_val)
                if month_num:
                    period_str = f"{current_year}-{month_num}"
                elif year_str and year_str != "nan":
                    # This row has a year value - it's an annual total
                    period_str = current_year
                else:
                    continue
            else:
                period_str = _normalize_period(year_val)
                if not period_str:
                    continue

            for col_idx, indicator in indicators.items():
                val = df.iloc[row_idx, col_idx]
                val_str = str(val).strip() if pd.notna(val) else ""
                unit = "RSD per unit" if table_name == "raw_fx_rates" else ""

                if table_name == "raw_fx_rates":
                    rows_to_insert.append(
                        (source_id, sheet_name, row_idx, indicator, period_str, val_str, unit)
                    )
                else:
                    rows_to_insert.append(
                        (source_id, sheet_name, row_idx, indicator, period_str, val_str, unit)
                    )

        if rows_to_insert:
            _insert_raw(conn, table_name, rows_to_insert)
            parsed.append(sheet_name)
            print(f"    Sheet '{sheet_name}' (transposed): {len(rows_to_insert)} cells")

    return parsed


def _insert_raw(conn, table_name, rows):
    """Insert rows into the appropriate raw table."""
    if table_name == "raw_fx_rates":
        cols = "(source_id, sheet_name, row_index, currency, period_raw, value_raw, unit_raw)"
    else:
        cols = "(source_id, sheet_name, row_index, indicator_raw, period_raw, value_raw, unit_raw)"
    placeholders = ",".join(["?"] * len(rows[0]))
    conn.executemany(
        f"INSERT INTO {table_name} {cols} VALUES ({placeholders})", rows
    )


RAW_TABLES = [
    "raw_bop", "raw_services", "raw_fdi", "raw_external_debt",
    "raw_iip", "raw_fx_reserves", "raw_fx_rates", "raw_macro",
]


def extract_all():
    """Extract all downloaded source files (full rebuild of raw tables)."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    # Clear all raw tables + metadata to avoid duplicates on re-run
    for table in RAW_TABLES:
        conn.execute(f"DELETE FROM {table}")
    conn.execute("DELETE FROM metadata")
    conn.commit()

    for filename, url, category, desc, freq, meth in SOURCES:
        try:
            extract_file(filename, url, category, desc, freq, meth, conn)
        except Exception as e:
            print(f"  ERROR extracting {filename}: {e}")

    conn.commit()
    conn.close()
    print("\nExtraction complete.")


if __name__ == "__main__":
    extract_all()
