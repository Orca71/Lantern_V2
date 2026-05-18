# Single entry point that orchestrates the full adapter flow.
# Runs once per new database

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapter.service_adapter import ServiceBusinessAdapter, CANONICAL_SCHEMA
from adapter.mapping_confirmer import run_confirmation
from adapter.view_executor import execute_views, drop_views, verify_views
from adapter import registry

# ADAPTER REGISTRY
# Maps business type strings to adapter classes.
# Add new business types here as they're built.

ADAPTER_TYPES = {
    "service": ServiceBusinessAdapter,
}

def setup_database(db_path: str, business_type: str = "service",
                    force_remap: bool = False) -> bool:
    """
    Full adapter setup flow for a single database.

    Args:
        db_path:    path to the SQLite database file
        business_type: which adapter to use (default: service)
        force_remap: if True, re-map even if already registered

    Returns:
        True if setup completed successfully, False otherwise.
    """
    print("\n" + "=" * 60)
    print("Database Setup Wizard")
    print("=" * 60)
    print(f"Database:      {db_path}")
    print(f"Business type: {business_type}")
    print("=" * 60)

    # --- Validate business type ---
    if business_type not in ADAPTER_TYPES:
        print(f"\nERROR: Unknown business type '{business_type}'.")
        print(f"Available: {list(ADAPTER_TYPES.keys())}")
        return False

    adapter_class = ADAPTER_TYPES[business_type]
    adapter = adapter_class(db_path)

    # Step 1: Inspect current schema
    print("\n[1/7] Inspecting database schema...")
    schema = adapter.inspect_schema()
    print(f"    Found {len(schema)} tables.")

    # Step 2: Check if already registered
    if registry.is_ready(db_path, schema) and not force_remap:
        print("\n[2/7] Database is already mapped and ready.")
        print("      Use force_remap=True to re-map from scratch.")
        return True

    if registry.is_registered(db_path):
        print("\n[2/7] Database is registered but schema has changed "
              "or re-map was requested.")
        print("      Dropping existing canonical views...")
        drop_views(db_path, list(CANONICAL_SCHEMA.keys()))
        registry.unregister(db_path)
    else:
        print("\n[2/7] New database — running full setup.")

    # --- Step 3: Suggest mappings ---
    print("\n[3/7] Detecting column mappings via synonyms...")
    suggestions = adapter.suggest_mappings(schema)

    # --- Step 4: User confirmation ---
    print("\n[4/7] Awaiting user confirmation...")
    confirmed = run_confirmation(suggestions)

    if not confirmed:
        print("\n cancelled by user. Database not configured")
        return False

    # --- Step 5: Validate confirmed mapping ---
    print("\n[5/7] Validating mapping...")
    errors = adapter.validate_mapping(confirmed)

    if errors:
        print(" Validation failed:")
        for err in errors:
            print(f"        - {err}")
        print("\n      Re-run setup to correct the mapping.")
        return False

    print("     Mapping is Valid")
    # --- Step 6: Generate and execute views ---
    print("\n[6/7] Generating and creating canonical views...")
    view_sqls = adapter.generate_views(confirmed)
    execute_errors = execute_views(db_path, view_sqls)

    if execute_errors:
        print("     View creation failed. Setup aborted")
        return False

    # --- Step 7: Verify and register ---
    print("\n[7/7] Verifying views and registering database...")
    verify_errors = verify_views(db_path, list(CANONICAL_SCHEMA.keys()))

    if verify_errors:
        print("      Views were created but not all are queryable.")
        print("      Setup aborted — database not registered.")
        # Roll back: drop the views we just created
        drop_views(db_path, list(CANONICAL_SCHEMA.keys()))
        return False

    registry.register(
        db_path=db_path,
        business_type=business_type,
        mapping=confirmed,
        schema=schema,
    )
    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    print(f"Database is now Lantern-ready: {Path(db_path).name}")
    print("=" * 60)
    return True

# CLI ENTRY POINT


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python adapter/setup_wizard.py <db_path> "
              "[business_type] [--force]")
        print("Example: python adapter/setup_wizard.py "
              "databases/customer1.db service")
        sys.exit(1)

    force_remap = "--force" in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != "--force"]

    db_path = args[0]
    business_type = args[1] if len(args) > 1 else "service"

    success = setup_database(db_path, business_type, force_remap)
    sys.exit(0 if success else 1)
