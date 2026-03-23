"""
Download all NBS Excel source files to data/raw_excel/.
Skips files that already exist (use --force to re-download).
"""

import sys, time
from pathlib import Path
import urllib.request
import ssl

# allow running as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import SOURCES, RAW_EXCEL_DIR


def download_all(force: bool = False):
    RAW_EXCEL_DIR.mkdir(parents=True, exist_ok=True)

    # NBS may need a browser-like header
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # some NBS endpoints have cert issues — allow fallback
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    ok, fail = 0, 0
    for filename, url, category, desc, freq, meth in SOURCES:
        dest = RAW_EXCEL_DIR / filename
        if dest.exists() and not force:
            print(f"  SKIP (exists): {filename}")
            ok += 1
            continue

        print(f"  GET  {filename} ...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
                dest.write_bytes(resp.read())
            print(f"    OK  ({dest.stat().st_size:,} bytes)")
            ok += 1
            time.sleep(0.5)  # be polite
        except Exception as e:
            print(f"    FAIL: {e}")
            fail += 1

    print(f"\nDone: {ok} ok, {fail} failed out of {len(SOURCES)} sources.")
    return fail


if __name__ == "__main__":
    force = "--force" in sys.argv
    download_all(force=force)
