# Presents suggested mappings to the user for review.
#To see if the adapter has matched the columns and tables correctly

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

def display_mappings(suggestions: dict):
    """
    Print the suggested mappings in a readable format

    """
    print("\n" + "=" * 60)
    print("LANTERN — Schema Mapping Review")
    print("=" * 60)
    print("Review each mapping below. Edit or clear anything")
    print("before confirming. Views are only created on confirm.")
    print("=" * 60)

    for canonical_table, details in suggestions.items():
        real_table = details.get("real_table") or "(no match)"
        print(f"\nTable: {canonical_table} <- {real_table}")
        print("-" * 40)

        for canonical_col, real_col in details["columns"].items():
            match = real_col or "(no match)"
            print(f" {canonical_col:30} <- {match}")

def confirm_mappings(suggestions: dict) -> dict:
    """
    Walk the user through every mapping interactively.
    For each table and column, the user can:
        - Press Enter to accept the suggestion
        - Type a different column/table name to override
        - Type 'clear' to remove the mapping entirely
    Returns the confirmed mapping dict in the same shape
    as suggestions, with user edits applied.

    """
    print("\n" + "=" * 60)
    print("LANTERN — Confirm Mappings")
    print("=" * 60)
    print("Press Enter to accept. Type a new name to override.")
    print("Type 'clear' to remove a mapping.")
    print("=" * 60)

    confirmed = {}
    for canonical_table, details in suggestions.items():
        print(f"\n-- Table: {canonical_table}")
        real_table = details.get("real_table") or ""

        # Confirm table mappings
        user_input = input(
            f"   real table [{real_table or 'no match'}]: "
        ).strip()
        if user_input.lower() == "clear":
            confirmed[canonical_table] = {
                "real_table": None,
                "columns": {col: None for col in details["columns"]}
            }
            print(f" Cleared - {canonical_table} will be skipped")
            continue

        confirmed_table = user_input if user_input else real_table or None

        # confirm column mapping
        confirmed_cols = {}
        for canonical_col, real_col in details["columns"].items():
            suggestion = real_col or ""
            user_input = input(f" {canonical_col:30} [{suggestion or 'no match'}]: ").strip()
            if user_input.lower() == "clear":
                confirmed_cols[canonical_col] = None
            elif user_input:
                confirmed_cols[canonical_col] = user_input
            else:
                confirmed_cols[canonical_col] = real_col

        confirmed[canonical_table] = {
            "real_table": confirmed_table,
            "columns":    confirmed_cols,
        }
    return confirmed

def run_confirmation(suggestions: dict) -> dict:
    """
    Full confirmation flow:
    1. Display all suggestions at once for overview
    2. Walk through each for interactive confirmation
    3. Return confirmed mapping

    Args:
        suggestions: output of ServiceBusinessAdapter.suggest_mappings()

    Returns:
        confirmed mapping dict ready for validate_mapping()
        and generate_views()
    """
    display_mappings(suggestions)
    print("\nReady to review each mapping.")
    proceed = input("Press Enter to start or 'q' to quit: ").strip().lower()
    if proceed == "q":
        print("Mapping cancelled.")
        return {}

    confirmed = confirm_mappings(suggestions)

    print("\n" + "=" * 60)
    print("MAPPING CONFIRMED")
    print("=" * 60)
    display_mappings(confirmed)

    final = input("\nApply this mapping and create views? (yes/no): ").strip().lower()
    if final != "yes":
        print("Mapping not applied. Run again to restart.")
        return {}

    return confirmed
