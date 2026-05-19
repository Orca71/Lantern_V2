# =============================================================
# LANTERN INTELLIGENCE v2 — config.py
# Single source of truth for paths, model settings, constants
# =============================================================
from pathlib import Path

# Project root = the folder this file lives in.
# Every other path derives from here, so the project is portable.
PROJECT_ROOT = Path(__file__).parent.resolve()

# --- Paths ---
DATABASES_DIR      = PROJECT_ROOT / "databases"
CHROMA_STORE_DIR   = PROJECT_ROOT / "chroma_store"
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
SQL_DIR            = PROJECT_ROOT / "matrix_queries"
STATIC_DIR         = PROJECT_ROOT / "static"
TEMPLATES_DIR      = PROJECT_ROOT / "templates"
SCHEMA_PATH        = PROJECT_ROOT / "metrics_schema.yaml"

# --- Databases ---
DB_PATHS = {
    "service1": DATABASES_DIR / "service1.db",
    "service2": DATABASES_DIR / "service2.db",
    "service3": DATABASES_DIR / "service3.db",
    "testcase": DATABASES_DIR / "test_cases.db",
}

COMPANY_NAMES = {
    "service1": "Apex Strategy Consulting",
    "service2": "Meridian Consulting Group",
    "service3": "Vertex Advisory Partners",
    "testcase": "Test Case Company"
}

# --- LLM ---
OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"

# --- RAG ---
COLLECTION_NAME      = "lantern_financial_concepts"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K_CONCEPTS       = 3
