# =============================================================
# LANTERN INTELLIGENCE v2 — view_executor.py
# Executes confirmed CREATE VIEW statements against the
# connected database. Runs once per database setup.
# After this, Lantern's queries run against canonical views
# as if the database was always structured that way.
# =============================================================
import sys
import sqlite3
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

def execute_views(db_path: str, view_sqls: list[str]) -> list[str]:
    """
    Execute CREATE VIEW statements against the database.
    skips views that already exist (If not exists handles this).

    Args:
        db_path: path to the SQLite database file
        view_sqls: list of CREATE VIEW SQL strings from generate_views()
    Returns:
        list of error strings. Empty list means all views created.
    """
    if not Path(db_path).exists():
        return [f"Database not found: {db_path}"]

    errors = []
    conn = sqlite3.connect(db_path)

    try:
        cursor = conn.cursor()
        for sql in view_sqls:
            try:
                cursor.execute(sql)
                # Extract view name for confirmation message
                view_name = sql.split("VIEW IF NOT EXISTS")[1].split()[0]
                print(f"    Created View: {view_name}")
            except sqlite3.Error as e:
                error_msg = f"Failed to create view: {e}"
                errors.append(error_msg)
                print(f"    ERROR: {error_msg}")
        conn.commit()
    finally:
        conn.close()
    return errors

def drop_views(db_path: str, view_names: list[str]) -> list[str]:
    """
    Drop existing caninical view from the databse.
    Used when re-mapping an already configured database.

    Args:
        db_path:    path to the SQLite database file
        view_names: list of canonical view names to drop

    Returns:
        list of error strings. Empty list means all views dropped.
    """
    if not Path(db_path).exists():
        return [f"Database not found: {db_path}"]

    errors = []
    conn = sqlite3.connect(db_path)

    try:
        cursor = conn.cursor()
        for name in view_names:
            try:
                cursor.execute(f"DROP VIEW IF EXISTS {name}")
                print(f"    Dropped view: {name}")
            except sqlite3.Error as e:
                error_msg = f"Failed to drop view {name}: {e}"
                errors.append(error_msg)
                print(f" ERROR: {error_msg}")
        conn.commit()
    finally:
        conn.close()

    return errors

def verify_views(db_path: str, expected_views: list[str]) -> list[str]:
    """
    Confirms that all expected canonical views exist and are queryable.
    Runs a lightweight SELECT against each view.

    Args:
        db_path:    path to the SQLite database file
        expected_views: list of canonical view names to check

    Returns:
        list of error strings. Empty list means all views verified.
    """
    if not Path(db_path).exists():
        return [f"Database not found: {db_path}"]

    errors = []
    conn = sqlite3.connect(db_path)

    try:
        cursor = conn.cursor()
        for view_name in expected_views:
            try:
                cursor.execute(f"SELECT * FROM {view_name} LIMIT 1")
                print(f"    Verified: {view_name}")
            except sqlite3.Error as e:
                error_msg = f"View not queryable - {view_name}: {e}"
                errors.append(error_msg)
                print(f"    ERROR: {error_msg}")
    finally:
        conn.close()

    return errors
