#This script normalizes excel and csv files into SQlite databases
#Each sheet becomes a table, Each column header becomes a column name. Similar process to other DBs
import sys
import sqlite3
import re
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PROJECT_ROOT

NORMALIZED_DIR = PROJECT_ROOT / "adapter" / "normalized"
SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv"}

def _sanitize_name(name: str) -> str:
    """
    Clean up a sheet or column name to be SQL-friendl.
    Lowercase, replace non-alphanumeric chars with underscores,
    strip leading/trailing underscores
    """
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", str(name).strip().lower())
    return cleaned.strip("_")


def _read_source_file(file_path: Path) -> dict:
    """
    Read an Excel or CSV file and return its content as a dict
    of DataFrames keyed by sheet name. CSV is treated as a single sheet using the filename stem.
    """
    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(file_path)
        return {file_path.stem: df}

    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(file_path, sheet_name=None)

    raise ValueError(f"Unsupported file type: {suffix}")


def ingest(file_path: str, output_name: str = None) -> str:
    """
    Ingest an Excel or CSV file into a SQLite database.
    Args:
        file_path: path to the Excel or CSV file
        output_name: optional name for the output .db file (default to the input file's stem)
    Returns:
        absolute path to the created SQLite database
    """
    source = Path(file_path).resolve()

    if not source.exists():
        raise FileNotFoundError(f"File not found: {source}")

    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {source.suffix}."
            f"Supported: {SUPPORTED_EXTENSIONS}"
        )

    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    db_name = output_name or source.stem
    db_path = NORMALIZED_DIR / f"{db_name}.db"
    print(f"\nReading: {source.name}")
    sheets = _read_source_file(source)
    print(f"Found {len(sheets)} sheet(s): {list(sheets.keys())}")
    conn = sqlite3.connect(db_path)
    try:
        for sheet_name, df in sheets.items():
            table_name = _sanitize_name(sheet_name)
            df.columns = [_sanitize_name(c) for c in df.columns]

            #Drop rows that are entirely empty (common in excel files)
            df = df.dropna(how="all")
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            print(f"    Loaded: {sheet_name} -> {table_name} ({len(df)} rows)")
    finally:
        conn.close()
    print(f"\nNormalized database: {db_path}")
    return str(db_path)

# CLI Entry Point
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python adapter/excel_ingestion.py <file_path>"
              "[output_name]")
        print("Example: python adapter/excel_ingestion.py"
              "uploads/customer_data.xlsx")
        sys.exit(1)
    file_path = sys.argv[1]
    output_name = sys.argv[2] if len(sys.argv) > 2 else None
    db_path = ingest(file_path, output_name)
    print(f"\nNext step: python adapter/setup_wizard.py {db_path} service")
