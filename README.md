# NBS External Sector Database

SQLite database built from publicly available National Bank of Serbia data,
designed as the foundation for a current account and external sector dashboard.

## Data Sources

All data from: https://www.nbs.rs/sr_RS/finansijsko_trziste/informacije-za-investitore-i-analiticare/

**27 source files** covering:

| Category | Files | Coverage |
|----------|-------|----------|
| Balance of Payments | 5 | 1997-2026 (annual + monthly) |
| Services | 3 | 2007-2025 (annual + monthly + by country) |
| Tourism | 2 | 2007-2025 (annual + by country) |
| FDI | 4 | 2010-2024 (flows + positions, by country + sector) |
| External Debt | 4 | 2000-2025 (by debtor, creditor, maturity) |
| IIP | 1 | 2013-Q3 2025 |
| FX Reserves | 2 | 2002-2026 |
| FX Rates | 2 | 1997-2025 (daily + monthly averages) |
| Macro Indicators | 4 | 2000-2025 |

## Database Structure

Two-layer design in `data/db/nbs_external_sector.db`:

### Metadata
- `metadata` — source file registry (URL, category, frequency, methodology)

### Raw Layer (data as-extracted from Excel)
- `raw_bop`, `raw_services`, `raw_fdi`, `raw_external_debt`
- `raw_iip`, `raw_fx_reserves`, `raw_fx_rates`, `raw_macro`

### Clean Layer (standardized, dashboard-ready)
- `clean_bop` — BOP line items: date, indicator_code, indicator_name, value (EUR mn)
- `clean_services` — services by type, country, direction
- `clean_fdi` — FDI flows and positions by country/sector
- `clean_external_debt` — debt by debtor/creditor/maturity
- `clean_iip` — international investment position
- `clean_fx_reserves` — NBS foreign exchange reserves
- `clean_fx_rates` — exchange rates (EUR, USD, CHF, GBP, etc.)
- `clean_macro` — GDP growth, CPI, trade, fiscal balance, public debt, etc.

## Quick Start

```bash
# Install dependencies
pip install pandas openpyxl xlrd

# Run full pipeline (download + extract + clean)
python run_pipeline.py

# Re-run without re-downloading
python run_pipeline.py --skip-download

# Force re-download everything
python run_pipeline.py --force
```

## Project Structure

```
nbs_dashboard/
  config.py                 # Source URLs and paths
  run_pipeline.py           # Main pipeline orchestrator
  scripts/
    download.py             # Download Excel files from NBS
    schema.py               # SQLite schema (DDL)
    extract.py              # Parse Excel -> raw tables
    clean.py                # Raw -> clean standardization
  data/
    raw_excel/              # Downloaded .xls/.xlsx files
    db/
      nbs_external_sector.db  # SQLite database
```

## Sample Queries

```sql
-- Current account balance, annual
SELECT date, value FROM clean_bop
WHERE indicator_code = 'CA' AND frequency = 'annual'
ORDER BY date;

-- Trade deficit (goods)
SELECT date, indicator_name, sub_indicator, value
FROM clean_bop
WHERE indicator_code = 'CA.GOODS'
AND frequency = 'annual'
ORDER BY date;

-- FDI by top countries
SELECT country_or_sector, SUM(value) as total
FROM clean_fdi
WHERE flow_or_position = 'flow'
GROUP BY country_or_sector
ORDER BY total DESC LIMIT 10;

-- FX reserves trend
SELECT date, indicator, value
FROM clean_fx_reserves
WHERE indicator LIKE '%Total%'
ORDER BY date;

-- GDP growth
SELECT date, value FROM clean_macro
WHERE indicator_name LIKE '%БДП%' AND indicator_name LIKE '%раст%'
ORDER BY date;
```

## Recommended Dashboard Views

1. **Current Account Overview** — CA balance (EUR mn), CA/GDP %, trend 2007-present
2. **CA Components Waterfall** — goods, services, primary income, secondary income
3. **Trade in Goods** — exports vs imports, deficit trend
4. **Services Balance** — IT/business services, tourism, transport breakdown
5. **FDI Financing** — net FDI vs CA deficit (coverage ratio)
6. **External Debt Monitor** — total stock, debt/GDP, maturity profile
7. **FX Reserves Adequacy** — reserves in months of imports, reserves/short-term debt
8. **IIP Summary** — net international position, assets vs liabilities

## Key KPIs

- Current Account / GDP (%)
- Trade deficit (EUR mn)
- Services surplus (EUR mn)
- FDI coverage ratio (net FDI / CA deficit)
- External debt / GDP (%)
- FX reserves / months of imports
- FX reserves / short-term debt

## Refreshing Data

NBS publishes monthly BOP data around the 15th of each month.
To refresh: `python run_pipeline.py --force`

For incremental updates, modify `config.py` to add new monthly files
and run `python run_pipeline.py`.
