"""
Configuration: NBS data sources, paths, and metadata.
"""

from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
RAW_EXCEL_DIR = DATA_DIR / "raw_excel"
DB_PATH = DATA_DIR / "db" / "nbs_external_sector.db"

# ── Base URLs ──────────────────────────────────────────────────────────
BASE_EN = "https://www.nbs.rs/export/sites/NBS_site/documents-eng/statistika"
BASE_SR = "https://www.nbs.rs/export/sites/NBS_site/documents/statistika"

# ── Source file registry ───────────────────────────────────────────────
# Each entry: (local_filename, url, category, description, frequency, methodology)
SOURCES = [
    # --- Balance of Payments ---
    (
        "bop_annual_2007_2025.xls",
        f"{BASE_EN}/ino_ekonomski_odnosi/platni_bilans/balance_of_payments_2007_2025.xls",
        "bop", "Balance of payments of Serbia, 2007-2025 (BPM6)",
        "annual", "BPM6",
    ),
    (
        "bop_annual_detailed_2007_2025.xls",
        f"{BASE_EN}/ino_ekonomski_odnosi/platni_bilans/balance_of_payments_2007_2025_detailed.xls",
        "bop", "Balance of payments of Serbia, detailed, 2007-2025 (BPM6)",
        "annual", "BPM6",
    ),
    (
        "bop_monthly_2026.xls",
        f"{BASE_EN}/ino_ekonomski_odnosi/platni_bilans/balance_of_payments_26.xls",
        "bop", "Balance of payments - monthly, 2026 (BPM6)",
        "monthly", "BPM6",
    ),
    (
        "bop_monthly_detailed_2026.xls",
        f"{BASE_EN}/ino_ekonomski_odnosi/platni_bilans/balance_of_payments_detailed_26.xls",
        "bop", "Balance of payments - monthly, detailed, 2026 (BPM6)",
        "monthly", "BPM6",
    ),
    (
        "bop_annual_1997_2006.xls",
        f"{BASE_EN}/ino_ekonomski_odnosi/platni_bilans/balance_of_payments_1997_2006.xls",
        "bop", "Balance of payments of Serbia, 1997-2006 (BPM5)",
        "annual", "BPM5",
    ),

    # --- Services ---
    (
        "services_annual_2007_2025.xls",
        f"{BASE_EN}/ino_ekonomski_odnosi/platni_bilans/services_2007_2025.xls",
        "services", "Services, 2007-2025 (BPM6)",
        "annual", "BPM6",
    ),
    (
        "services_by_country_annual_2007_2025.xls",
        f"{BASE_EN}/ino_ekonomski_odnosi/platni_bilans/services_by_country_2007_2025.xls",
        "services", "Services by country, 2007-2025 (BPM6)",
        "annual", "BPM6",
    ),
    (
        "services_monthly_2025.xls",
        f"{BASE_EN}/ino_ekonomski_odnosi/platni_bilans/services_25.xls",
        "services", "Services, monthly, 2025 (BPM6)",
        "monthly", "BPM6",
    ),

    # --- Tourism ---
    (
        "tourism_by_country_annual_2007_2025.xls",
        f"{BASE_EN}/ino_ekonomski_odnosi/platni_bilans/tourism_by_country_2007_2025.xls",
        "tourism", "Tourism by country, 2007-2025 (BPM6)",
        "annual", "BPM6",
    ),
    (
        "tourism_monthly_2025.xls",
        f"{BASE_EN}/ino_ekonomski_odnosi/platni_bilans/tourism_25.xls",
        "tourism", "Tourism, monthly, 2025 (BPM6)",
        "monthly", "BPM6",
    ),

    # --- FDI ---
    (
        "fdi_flows_by_country_2010_2024.xls",
        f"{BASE_EN}/ino_ekonomski_odnosi/platni_bilans/fdi_by_country_2010_2024.xls",
        "fdi", "FDI flows by country, 2010-2024 (BPM6)",
        "annual", "BPM6",
    ),
    (
        "fdi_flows_by_activity_2010_2024.xls",
        f"{BASE_EN}/ino_ekonomski_odnosi/platni_bilans/fdi_branch_of_activity_2010_2024.xls",
        "fdi", "FDI flows by branch of activity, 2010-2024 (BPM6)",
        "annual", "BPM6",
    ),
    (
        "fdi_positions_by_country_2020_2024.xls",
        f"{BASE_EN}/ino_ekonomski_odnosi/platni_bilans/fdi_by_country_position_25.xls",
        "fdi", "FDI positions by country, 2020-2024 (BPM6)",
        "annual", "BPM6",
    ),
    (
        "fdi_positions_by_activity_2020_2024.xls",
        f"{BASE_EN}/ino_ekonomski_odnosi/platni_bilans/fdi_branch_of_activity_position_25.xls",
        "fdi", "FDI positions by branch of activity, 2020-2024 (BPM6)",
        "annual", "BPM6",
    ),

    # --- External Debt ---
    (
        "ext_debt_by_debtor_creditor.xls",
        f"{BASE_SR}/ino_ekonomski_odnosi/SEOI_spoljni_dug.xls",
        "external_debt", "External debt by debtors and creditors",
        "quarterly", "BPM6",
    ),
    (
        "ext_debt_by_creditor.xls",
        f"{BASE_SR}/ino_ekonomski_odnosi/SBEOI08.xls",
        "external_debt", "External debt by creditor",
        "quarterly", "BPM6",
    ),
    (
        "ext_debt_by_debtor_type.xls",
        f"{BASE_SR}/ino_ekonomski_odnosi/SBEOI10.xls",
        "external_debt", "External debt by type of debtor",
        "quarterly", "BPM6",
    ),
    (
        "ext_debt_by_maturity.xls",
        f"{BASE_SR}/ino_ekonomski_odnosi/SEOI_spoljni_dug_dospece.xls",
        "external_debt", "External debt by remaining maturity",
        "quarterly", "BPM6",
    ),

    # --- IIP ---
    (
        "iip_q3_2025.xls",
        f"{BASE_EN}/ino_ekonomski_odnosi/mip/IIP-IIIQ_2025.xls",
        "iip", "International investment position, Q3 2025",
        "quarterly", "BPM6",
    ),

    # --- FX Reserves ---
    (
        "fx_reserves.xlsx",
        f"{BASE_SR}/ino_ekonomski_odnosi/SBEOI06.xlsx",
        "fx_reserves", "Foreign exchange reserves",
        "monthly", "",
    ),
    (
        "intl_reserves_fx_liquidity.xls",
        f"{BASE_EN}/ino_ekonomski_odnosi/international_reserves_and_foreign_currency_liquidity.xls",
        "fx_reserves", "International reserves and foreign currency liquidity",
        "monthly", "",
    ),

    # --- FX Rates ---
    (
        "fx_rate_movements.xlsx",
        f"{BASE_SR}/ino_ekonomski_odnosi/SBEOI09.xlsx",
        "fx_rates", "FX rate movements",
        "daily", "",
    ),
    (
        "fx_rate_averages.xlsx",
        f"{BASE_SR}/ino_ekonomski_odnosi/SBEOI11.xlsx",
        "fx_rates", "FX rate period averages",
        "monthly", "",
    ),

    # --- Macro / External Position ---
    (
        "macro_indicators.xls",
        f"{BASE_SR}/ostalo/osnovni_makroekonomski_indikatori.xls",
        "macro", "Basic macroeconomic indicators",
        "annual", "",
    ),
    (
        "external_position_indicators.xls",
        f"{BASE_SR}/ostalo/indikatori_eksterne_pozicije.xls",
        "macro", "External position indicators",
        "quarterly", "",
    ),
    (
        "bank_foreign_liabilities.xlsx",
        f"{BASE_SR}/ino_ekonomski_odnosi/SBEOI05.xlsx",
        "macro", "Bank foreign liabilities",
        "monthly", "",
    ),
    (
        "private_sector_debt.xls",
        f"{BASE_SR}/ino_ekonomski_odnosi/dug_privrede_stanovnistva.xls",
        "macro", "Private sector debt (corporate and household)",
        "quarterly", "",
    ),
]
