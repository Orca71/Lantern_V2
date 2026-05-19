#Adapter for service_based businuess.
import sys
import sqlite3
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapter.base_adapter import BaseAdapter
from config import SQL_DIR

# ----------------------------------------------------------
# CANONICAL SCHEMA
# The six tables Lantern's SQL queries expect.
# Every service business database must expose these —
# either directly or through views the adapter creates.
# ----------------------------------------------------------
CANONICAL_SCHEMA = {
    "cash_snapshot": [
        "snapshot_id", "snapshot_date", "cash_balance",
        "accounts_receivable", "accounts_payable"
    ],
    "clients": [
        "client_id", "client_name", "industry",
        "status", "acquired_date"
    ],
    "company": [
        "company_name", "industry", "founded_date", "created_at"
    ],
    "employees": [
        "employee_id", "name", "role",
        "salary", "hire_date", "end_date"
    ],
    "expenses": [
        "expense_id", "amount", "category",
        "expense_date", "vendor", "is_recurring"
    ],
    "invoices": [
        "invoice_id", "client_id", "amount", "issue_date",
        "due_date", "paid_date", "status", "service_type"
    ],
}

TABLE_SYNONYMS = {
    "cash_snapshot":  ["bank_balances", "cash_positions", "financials",
                       "cash_records", "balance_sheet", "cash_history"],
    "clients":        ["customers", "accounts", "contacts",
                       "client_list", "customer_list"],
    "company":        ["organization", "business", "firm",
                       "company_info", "entity"],
    "employees":      ["staff", "headcount", "personnel",
                       "team_members", "workers", "people"],
    "expenses":       ["costs", "expenditures", "spending",
                       "outflows", "payments", "transactions"],
    "invoices":       ["billing", "billing_records", "bills", "orders",
                       "sales", "sales_records", "revenue_records",
                       "invoice_records"],
}

COLUMN_SYNONYMS = {
    # --- Cash Snapshot ---
    "snapshot_id":         ["balance_id", "record_id", "position_id"],
    "snapshot_date":       ["date", "record_date", "as_of_date",
                            "balance_date"],
    "cash_balance":        ["balance", "cash", "cash_on_hand",
                            "bank_balance"],
    "accounts_receivable": ["receivables", "ar", "money_owed", "outstanding"],
    "accounts_payable":    ["payables", "ap", "owed", "liabilities"],

    # --- Clients ---
    "client_id":           ["customer_id", "account_id", "cust_id"],
    "client_name":         ["customer_name", "account_name", "name", "company"],
    "acquired_date":       ["start_date", "client_since", "onboarded_at",
                            "joined_date", "created_at"],

    # --- Company ---
    "company_name":        ["name", "business_name", "organization_name"],
    "founded_date":        ["established", "inception_date", "start_date"],

    # --- Shared (Clients + Company) ---
    "industry":            ["vertical", "sector", "business_type",
                            "domain", "market"],

    # --- Employees ---
    "employee_id":         ["staff_id", "person_id", "worker_id", "id"],
    "name":                ["full_name", "employee_name", "staff_name",
                            "person_name", "fullname"],
    "role":                ["job_title", "position", "title", "designation",
                            "job_role"],
    "salary":              ["annual_salary", "compensation", "pay", "wage",
                            "base_salary"],
    "hire_date":           ["start_date", "joined_at", "employment_start",
                            "onboarded_at"],
    "end_date":            ["termination_date", "exit_date", "left_at",
                            "departure_date"],

    # --- Shared (Expenses + Invoices) ---
    "amount":              ["invoice_total", "invoice_amount", "bill_amount",
                            "payment_amount", "cost_amount", "total", "value",
                            "subtotal"],

    # --- Expenses ---
    "expense_id":          ["cost_id", "transaction_id", "payment_id"],
    "expense_date":        ["date", "transaction_date", "payment_date",
                            "cost_date"],
    "category":            ["cost_category", "expense_category",
                            "expense_type", "classification", "type"],
    "vendor":              ["vendor_name", "supplier", "supplier_name",
                            "payee", "merchant"],
    "is_recurring":        ["recurring", "repeat", "subscription",
                            "is_subscription"],

    # --- Invoices ---
    "invoice_id":          ["bill_id", "order_id", "sale_id",
                            "transaction_id"],
    "issue_date":          ["created_at", "billing_date", "invoice_date",
                            "date", "sale_date"],
    "due_date":            ["payment_due", "deadline", "expiry_date"],
    "paid_date":           ["payment_date", "settled_at", "cleared_date",
                            "received_date"],
    "status":              ["statues", "state", "active_flag",
                            "account_status", "invoice_status"],
    "service_type":        ["type", "category", "service", "product_type"],
}

class ServiceBusinessAdapter(BaseAdapter):

    def inspect_schema(self) -> dict:
        """
        Read all tables and columns from the real database.
        Reuses the logic from schema_inspector.py.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        schema = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            schema[table] = [
                {
                    "name":        row[1],
                    "type":        row[2],
                    "nullable":    not bool(row[3]),
                    "primary_key": bool(row[5]),
                }
                for row in cursor.fetchall()
            ]
        conn.close()
        return schema

    def suggest_mappings(self, schema: dict) -> dict:
        """
        walk the real schema and suggest canonical mappings
        using TABLE_SYNONYMS and COLUMN_SYNONYMS.
        Returns:
            {canonical_table: {
                "real_table": str or None,
                "columns": {canonical_col: real_col or None}
            }}
        """
        real_tables = {t.lower(): t for t in schema.keys()}
        suggestions = {}

        for canonical_table, canonical_cols in CANONICAL_SCHEMA.items():
            real_table = self._match_table(canonical_table, real_tables)
            col_mapping = {}

            if real_table:
                real_cols = {
                    c["name"].lower(): c["name"]
                    for c in schema[real_table]
                }
                for canonical_col in canonical_cols:
                    col_mapping[canonical_col] = self._match_column(
                        canonical_col, real_cols
                    )
            else:
                for canonical_col in canonical_cols:
                    col_mapping[canonical_col] = None

            suggestions[canonical_table] = {
                "real_table": real_table,
                "columns": col_mapping,
            }
        return suggestions

    def _match_table(self, canonical: str, real_tables: dict) -> str | None:
        """Match a canonical table name to a real table"""
        if canonical in real_tables:
            return real_tables[canonical]
        for synonym in TABLE_SYNONYMS.get(canonical, []):
            if synonym.lower() in real_tables:
                return real_tables[synonym.lower()]
        return None

    def _match_column(self, canonical: str, real_cols: dict) -> str | None:
        """Match a canonical column name to a real column."""
        if canonical in real_cols:
            return real_cols[canonical]
        for synonym in COLUMN_SYNONYMS.get(canonical, []):
            if synonym.lower() in real_cols:
                return real_cols[synonym.lower()]
        return None


    def validate_mapping(self, mapping: dict) -> list[str]:
        """
        Check that every required canonical field resolves.
        Returns list of error strings. Empty list means valid.
        """
        required = {
            "cash_snapshot": ["snapshot_date", "cash_balance"],
            "clients":       ["client_id", "client_name"],
            "employees":     ["employee_id", "name", "hire_date"],
            "expenses":      ["expense_id", "amount",
                              "category", "expense_date"],
            "invoices":      ["invoice_id", "client_id",
                              "amount", "issue_date", "due_date"],
        }
        errors = []
        for table, cols in required.items():
            table_mapping = mapping.get(table, {})
            if not table_mapping.get("real_table"):
                errors.append(f"[{table}] No matching table found.")
                continue
            for col in cols:
                if not table_mapping["columns"].get(col):
                    errors.append(
                        f"[{table}.{col}] Required column not mapped."
                    )
        return errors

    # ----------------------------------------------------------
    # GENERATE VIEWS
    # ----------------------------------------------------------

    def generate_views(self, mapping: dict) -> list[str]:
        views = []
        print(f"DEBUG generate_views: received {len(mapping)} tables")
        for canonical_table, details in mapping.items():
            real_table = details.get("real_table")
            columns = details.get("columns", {})
            print(f"  DEBUG: {canonical_table} -> real_table={real_table!r}, columns={len(columns)}")

            if not real_table:
                print(f"    SKIP: no real_table")
                continue

            col_lines = []
            for canonical_col, real_col in columns.items():
                if real_col:
                    if real_col != canonical_col:
                        col_lines.append(f"    {real_col} AS {canonical_col}")
                    else:
                        col_lines.append(f"    {real_col}")

            print(f"    col_lines count: {len(col_lines)}")
            if not col_lines:
                print(f"    SKIP: no col_lines")
                continue

            col_block = ",\n".join(col_lines)
            sql = (
                f"CREATE VIEW IF NOT EXISTS {canonical_table} AS\n"
                f"SELECT\n"
                f"{col_block}\n"
                f"FROM {real_table};"
            )
            views.append(sql)
            print(f"    ADDED view for {canonical_table}")
        return views
