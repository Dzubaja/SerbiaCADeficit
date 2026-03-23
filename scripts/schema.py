"""
Create the SQLite database schema: metadata + raw + clean tables.
"""

import sqlite3, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DB_PATH


DDL = """
-- ── Metadata ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS metadata (
    source_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    filename        TEXT NOT NULL UNIQUE,
    url             TEXT,
    category        TEXT,       -- bop, services, fdi, external_debt, etc.
    description     TEXT,
    frequency       TEXT,       -- annual, quarterly, monthly, daily
    methodology     TEXT,       -- BPM5, BPM6, etc.
    download_date   TEXT,
    file_size_bytes INTEGER,
    sheets_parsed   TEXT        -- JSON list of sheet names parsed
);

-- ── Raw tables (data as-extracted from Excel) ─────────────────────────
CREATE TABLE IF NOT EXISTS raw_bop (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES metadata(source_id),
    sheet_name      TEXT,
    row_index       INTEGER,
    indicator_raw   TEXT,       -- original row label from Excel
    period_raw      TEXT,       -- original column header (year or month)
    value_raw       TEXT,       -- original cell value as string
    unit_raw        TEXT
);

CREATE TABLE IF NOT EXISTS raw_services (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES metadata(source_id),
    sheet_name      TEXT,
    row_index       INTEGER,
    indicator_raw   TEXT,
    country         TEXT,
    period_raw      TEXT,
    value_raw       TEXT,
    unit_raw        TEXT
);

CREATE TABLE IF NOT EXISTS raw_fdi (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES metadata(source_id),
    sheet_name      TEXT,
    row_index       INTEGER,
    indicator_raw   TEXT,
    country_or_sector TEXT,
    period_raw      TEXT,
    value_raw       TEXT,
    unit_raw        TEXT
);

CREATE TABLE IF NOT EXISTS raw_external_debt (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES metadata(source_id),
    sheet_name      TEXT,
    row_index       INTEGER,
    indicator_raw   TEXT,
    period_raw      TEXT,
    value_raw       TEXT,
    unit_raw        TEXT
);

CREATE TABLE IF NOT EXISTS raw_iip (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES metadata(source_id),
    sheet_name      TEXT,
    row_index       INTEGER,
    indicator_raw   TEXT,
    period_raw      TEXT,
    value_raw       TEXT,
    unit_raw        TEXT
);

CREATE TABLE IF NOT EXISTS raw_fx_reserves (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES metadata(source_id),
    sheet_name      TEXT,
    row_index       INTEGER,
    indicator_raw   TEXT,
    period_raw      TEXT,
    value_raw       TEXT,
    unit_raw        TEXT
);

CREATE TABLE IF NOT EXISTS raw_fx_rates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES metadata(source_id),
    sheet_name      TEXT,
    row_index       INTEGER,
    currency        TEXT,
    period_raw      TEXT,
    value_raw       TEXT,
    unit_raw        TEXT
);

CREATE TABLE IF NOT EXISTS raw_macro (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES metadata(source_id),
    sheet_name      TEXT,
    row_index       INTEGER,
    indicator_raw   TEXT,
    period_raw      TEXT,
    value_raw       TEXT,
    unit_raw        TEXT
);

-- ── Clean tables (standardized, dashboard-ready) ──────────────────────
CREATE TABLE IF NOT EXISTS clean_bop (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES metadata(source_id),
    date            TEXT,       -- ISO date: YYYY-01-01 for annual, YYYY-MM-01 for monthly
    frequency       TEXT,       -- annual / monthly
    indicator_code  TEXT,       -- e.g. CA, CA.GOODS, CA.SERVICES, FA, FA.FDI
    indicator_name  TEXT,       -- human-readable
    sub_indicator   TEXT,       -- credit / debit / net (where applicable)
    value           REAL,       -- numeric, in millions EUR
    unit            TEXT        -- EUR_MN
);

CREATE TABLE IF NOT EXISTS clean_services (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES metadata(source_id),
    date            TEXT,
    frequency       TEXT,
    service_type    TEXT,       -- transport, travel, IT, etc.
    country         TEXT,       -- NULL for totals
    direction       TEXT,       -- credit / debit / net
    value           REAL,
    unit            TEXT
);

CREATE TABLE IF NOT EXISTS clean_fdi (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES metadata(source_id),
    date            TEXT,
    frequency       TEXT,
    flow_or_position TEXT,     -- flow / position
    indicator       TEXT,       -- e.g. equity, debt, reinvested_earnings
    country_or_sector TEXT,
    direction       TEXT,       -- assets / liabilities / net
    value           REAL,
    unit            TEXT
);

CREATE TABLE IF NOT EXISTS clean_external_debt (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES metadata(source_id),
    date            TEXT,
    frequency       TEXT,
    debtor_type     TEXT,       -- public_sector, private_sector, nbs, banks, etc.
    creditor_type   TEXT,
    maturity        TEXT,       -- short_term / long_term
    value           REAL,
    unit            TEXT
);

CREATE TABLE IF NOT EXISTS clean_iip (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES metadata(source_id),
    date            TEXT,
    frequency       TEXT,
    indicator       TEXT,
    direction       TEXT,       -- assets / liabilities / net
    value           REAL,
    unit            TEXT
);

CREATE TABLE IF NOT EXISTS clean_fx_reserves (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES metadata(source_id),
    date            TEXT,
    frequency       TEXT,
    indicator       TEXT,
    value           REAL,
    unit            TEXT
);

CREATE TABLE IF NOT EXISTS clean_fx_rates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES metadata(source_id),
    date            TEXT,
    frequency       TEXT,
    currency        TEXT,       -- USD, EUR, GBP, CHF etc.
    rate_type       TEXT,       -- official, buying, selling, middle
    value           REAL,
    unit            TEXT        -- RSD per unit
);

CREATE TABLE IF NOT EXISTS clean_macro (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER REFERENCES metadata(source_id),
    date            TEXT,
    frequency       TEXT,
    indicator_code  TEXT,
    indicator_name  TEXT,
    value           REAL,
    unit            TEXT
);

-- ── Indexes for dashboard queries ─────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_clean_bop_date ON clean_bop(date);
CREATE INDEX IF NOT EXISTS idx_clean_bop_indicator ON clean_bop(indicator_code);
CREATE INDEX IF NOT EXISTS idx_clean_services_date ON clean_services(date);
CREATE INDEX IF NOT EXISTS idx_clean_fdi_date ON clean_fdi(date);
CREATE INDEX IF NOT EXISTS idx_clean_ext_debt_date ON clean_external_debt(date);
CREATE INDEX IF NOT EXISTS idx_clean_fx_reserves_date ON clean_fx_reserves(date);
CREATE INDEX IF NOT EXISTS idx_clean_fx_rates_date ON clean_fx_rates(date);
CREATE INDEX IF NOT EXISTS idx_clean_macro_date ON clean_macro(date);
"""


def create_schema():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(DDL)
    conn.close()
    print(f"Schema created: {DB_PATH}")


if __name__ == "__main__":
    create_schema()
