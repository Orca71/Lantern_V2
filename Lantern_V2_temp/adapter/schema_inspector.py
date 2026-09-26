# Schema_inspector.py
# Reads the structure of a SQLite database - tables, columns, types, nullability and primary keys
import sqlite3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_PATHS

def inspect_schema(db_path):
    """
    Read all tables and their columns from a sqlite DB.
    Returns :
        dict: {table_name: [column_info_dic, ...]}
    """
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    #Get list of tables (excluding SQLite internal tables)
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]

    schema = {}
    for table in tables:
        #PRAGMA table_info returns: cid, name, type, notnull, dflat_value, pl
        cursor.execute(f"PRAGMA table_info({table})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                "name": row[1],
                "type": row[2],
                "nullable": not bool(row[3]),
                "default": row[4],
                "primary_key": bool(row[5]),
            })
        schema[table] = columns
    conn.close()
    return schema

def print_schema(db_name, schema):
    """Human-readable schema dump."""
    print(f"\n{'=' * 60}")
    print(f"Database: {db_name}")
    print(f"{'=' * 60}")
    for table, columns in schema.items():
        print(f"\nTable: {table}")
        for col in columns:
            pk_marker = " (PK)" if col["primary_key"] else ""
            nullable  = "NULL" if col["nullable"] else "NOT NULL"
            print(f"  {col['name']:30} {col['type']:15} {nullable}{pk_marker}")


if __name__ == "__main__":
    for db_key, db_path in DB_PATHS.items():
        schema = inspect_schema(db_path)
        print_schema(db_key, schema)
