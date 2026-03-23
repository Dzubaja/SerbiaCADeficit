"""
Main pipeline: download → extract → clean → verify.

Usage:
    python run_pipeline.py              # full pipeline
    python run_pipeline.py --skip-download   # skip download step
    python run_pipeline.py --force      # re-download all files
"""

import os, sqlite3, sys
from pathlib import Path

# Ensure UTF-8 output on Windows
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DB_PATH
from scripts.schema import create_schema
from scripts.download import download_all
from scripts.extract import extract_all
from scripts.clean import clean_all


def verify(db_path):
    """Print summary counts for all tables."""
    conn = sqlite3.connect(str(db_path))
    print("\n" + "=" * 60)
    print("DATABASE SUMMARY")
    print("=" * 60)

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()

    for (table,) in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
        print(f"  {table:30s} {count:>10,} rows")

    # Key stats for dashboard
    print("\n" + "-" * 60)
    print("KEY STATS FOR DASHBOARD:")
    print("-" * 60)

    for label, query in [
        ("BOP date range", "SELECT MIN(date), MAX(date) FROM clean_bop"),
        ("BOP indicators", "SELECT COUNT(DISTINCT indicator_code) FROM clean_bop"),
        ("Services types", "SELECT COUNT(DISTINCT service_type) FROM clean_services"),
        ("FDI records", "SELECT COUNT(*) FROM clean_fdi"),
        ("Ext debt records", "SELECT COUNT(*) FROM clean_external_debt"),
        ("FX reserves records", "SELECT COUNT(*) FROM clean_fx_reserves"),
        ("FX rates records", "SELECT COUNT(*) FROM clean_fx_rates"),
        ("Macro indicators", "SELECT COUNT(DISTINCT indicator_code) FROM clean_macro"),
        ("Sources loaded", "SELECT COUNT(*) FROM metadata"),
    ]:
        try:
            result = conn.execute(query).fetchone()
            vals = " | ".join(str(v) for v in result)
            print(f"  {label:25s} {vals}")
        except Exception as e:
            print(f"  {label:25s} ERROR: {e}")

    conn.close()


def main():
    args = sys.argv[1:]
    skip_download = "--skip-download" in args
    force = "--force" in args

    print("=" * 60)
    print("NBS External Sector Data Pipeline")
    print("=" * 60)

    # Step 1: Schema
    print("\n[1/4] Creating database schema...")
    create_schema()

    # Step 2: Download
    if skip_download:
        print("\n[2/4] Skipping download (--skip-download)")
    else:
        print("\n[2/4] Downloading source files...")
        download_all(force=force)

    # Step 3: Extract
    print("\n[3/4] Extracting data from Excel files...")
    extract_all()

    # Step 4: Clean
    print("\n[4/4] Cleaning and standardizing data...")
    clean_all()

    # Verify
    verify(DB_PATH)

    print(f"\nDatabase: {DB_PATH}")
    print("Pipeline complete!")


if __name__ == "__main__":
    main()
