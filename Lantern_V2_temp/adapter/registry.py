# Track which databases have been mapped and validated
#Each database goes through the adapter wizard once
#Detects schema changes and triggers re-mapping when needed

import sys
import json
import yaml
import hashlib
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PROJECT_ROOT

# Registry Locations
REGISTRY_DIR = PROJECT_ROOT / "adapter" / "registry"
REGISTRY_FILE = REGISTRY_DIR / "registry.json"
MAPPINGS_DIR = REGISTRY_DIR / "mappings"

# Internal Helpers

def _ensure_dirs():
    """Create registry directories if they don't exist."""
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    MAPPINGS_DIR.mkdir(parents=True, exist_ok=True)

def _load_registry() -> dict:
    """Load registry from disk. Returns empty if file doesn't exist."""
    _ensure_dirs()
    if not REGISTRY_FILE.exists():
        return {"databases": {}}
    with open(REGISTRY_FILE, "r") as f:
        return json.load(f)


def _save_registry(registry: dict):
    """Save registry to disk"""
    _ensure_dirs()
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)

def _compute_schema_hash(schema: dict) -> str:
    """
    Hash the real database schema.
    Used to detect when the underlying schema has changed
    since the database was originally mapped.
    """
    schema_str = json.dumps(schema, sort_keys=True, default=str)
    return hashlib.sha256(schema_str.encode()).hexdigest()[:16]

def _db_key(db_path: str) -> str:
    """Resolve a database path to an absolute string key."""
    return str(Path(db_path).resolve())

# Public API

def is_registered(db_path: str) -> bool:
    """check if a database has ever been mapped """
    registry = _load_registry()
    return _db_key(db_path) in registry["databases"]

def is_ready(db_path: str, current_schema: dict) -> bool:
    """
    A database is ready if:
        1. it is registered
        2. Its status is 'ready'
        3. Its current schema hash matches the stored one
            (i.e., the underlying schema hasn't changed)
    """
    registry = _load_registry()
    entry = registry["databases"].get(_db_key(db_path))

    if not entry:
        return False
    if entry.get("status") != "ready":
        return False

    current_hash = _compute_schema_hash(current_schema)
    return entry.get("schema_hash") == current_hash

def get_mappings(db_path: str) -> dict | None:
    """Load the saved mapping YAML for a registered database."""
    registry = _load_registry()
    entry = registry["databases"].get(_db_key(db_path))

    if not entry:
        return None

    mapping_path = MAPPINGS_DIR / entry["mapping_file"]
    if not mapping_path.exists():
        return None

    with open(mapping_path, "r") as f:
        return yaml.safe_load(f)

def register(db_path: str, business_type: str,
            mapping: dict, schema: dict, company_name: str = None):
    """
    Persist a confirmed mapping. Saves the mapping YAML to disk and updates the registry with metadata.
    """
    _ensure_dirs()
    db_key = _db_key(db_path)
    db_name = Path(db_path).stem
    mapping_filename = f"{db_name}_mapping.yaml"
    mapping_path = MAPPINGS_DIR / mapping_filename

    # Save mapping to its own YAML file
    with open(mapping_path, 'w') as f:
        yaml.safe_dump(mapping, f, default_flow_style=False, sort_keys = False)

    #Update registry entry
    registry = _load_registry()
    registry["databases"][db_key] = {
        "db_path": db_key,
        "db_name": db_name,
        "business_type": business_type,
        "company_name": company_name or db_name,
        "schema_hash": _compute_schema_hash(schema),
        "mapping_file": mapping_filename,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "status": "ready",
    }
    _save_registry(registry)

    print(f" Registered: {db_name}")
    print(f" Mapping file: {mapping_path}")

def unregister(db_path: str):
    """
    Remove a database from the registry and delete its mapping.
    Used when a user wants to re-map from scratch.
    """
    registry = _load_registry()
    entry = registry["databases"].pop(_db_key(db_path), None)

    if entry:
        mapping_path = MAPPINGS_DIR / entry["mapping_file"]
        if mapping_path.exists():
            mapping_path.unlink()
        _save_registry(registry)
        print(f" Unregistered: {entry['db_name']}")
    else:
        print(f" Not registered: {db_path}")

def list_registered() -> list[dict]:
    """List metadata for all registered databases."""
    registry = _load_registry()
    return list(registry["databases"].values())
