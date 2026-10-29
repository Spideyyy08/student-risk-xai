"""
Download public benchmark datasets:
1. UCI 697: Predict Students' Dropout and Academic Success
2. UCI 320: Student Performance (Math & Portuguese)
No fabricated fallback data. Exits with instructions on download failure.
"""

import sys
import urllib.request
import zipfile
import io
from pathlib import Path

# Bootstrap sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ml_pipeline.config import EXTERNAL_DATA_DIR
import pandas as pd


def download_uci697():
    """Download UCI 697 dataset via ucimlrepo or direct zip archive."""
    out_file = EXTERNAL_DATA_DIR / "uci697_dropout_success.csv"
    if out_file.exists():
        print(f"[OK] UCI 697 already exists at {out_file}")
        return

    print("Fetching UCI 697 (Student Dropout and Academic Success)...")
    success = False
    try:
        from ucimlrepo import fetch_ucirepo
        dataset = fetch_ucirepo(id=697)
        X = dataset.data.features
        y = dataset.data.targets
        df = pd.concat([X, y], axis=1)
        df.to_csv(out_file, index=False)
        print(f"[SUCCESS] Downloaded UCI 697 ({len(df)} rows) via ucimlrepo to {out_file}")
        success = True
    except Exception as err:
        print(f"[INFO] ucimlrepo direct fetch unsuccessful: {err}")

    if not success:
        # Fallback to direct UCI URL download
        url = "https://archive.ics.uci.edu/static/public/697/predict+students+dropout+and+academic+success.zip"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                # Find data csv file
                csv_names = [n for n in z.namelist() if n.endswith(".csv")]
                if csv_names:
                    with z.open(csv_names[0]) as zf:
                        df = pd.read_csv(zf, sep=";")
                        df.to_csv(out_file, index=False)
                        print(f"[SUCCESS] Downloaded UCI 697 from archive zip to {out_file}")
                        success = True
        except Exception as err:
            print(f"[ERROR] Could not download UCI 697: {err}")

    if not success:
        print("\n" + "=" * 60)
        print("MANUAL DOWNLOAD REQUIRED FOR UCI 697:")
        print("1. Download https://archive.ics.uci.edu/dataset/697/predict+students+dropout+and+academic+success")
        print(f"2. Extract and place data.csv at: {out_file}")
        print("=" * 60)
        sys.exit(1)


def download_uci320():
    """Download UCI 320 Student Performance dataset."""
    out_file = EXTERNAL_DATA_DIR / "uci320_student_performance.csv"
    if out_file.exists():
        print(f"[OK] UCI 320 already exists at {out_file}")
        return

    print("Fetching UCI 320 (Student Performance)...")
    url = "https://archive.ics.uci.edu/static/public/320/student+performance.zip"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if "student-mat.csv" in z.namelist():
                with z.open("student-mat.csv") as zf:
                    df = pd.read_csv(zf, sep=";")
                    df.to_csv(out_file, index=False)
                    print(f"[SUCCESS] Downloaded UCI 320 (Math cohort: {len(df)} rows) to {out_file}")
                    return
    except Exception as err:
        print(f"[INFO] Could not automatically download UCI 320: {err}")
        print(f"UCI 320 is optional for secondary benchmarks. Place student-mat.csv at {out_file} if desired.")


def main():
    download_uci697()
    download_uci320()


if __name__ == "__main__":
    main()
