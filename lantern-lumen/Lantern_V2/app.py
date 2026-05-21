import json
import shutil
import sqlite3
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests as req

from adviser import COMPANY_NAMES, prepare
from query_router import route
from config import OLLAMA_URL, OLLAMA_MODEL, STATIC_DIR, TEMPLATES_DIR, PROJECT_ROOT
from adapter import registry as reg
from adapter.service_adapter import ServiceBusinessAdapter, CANONICAL_SCHEMA
from adapter.excel_ingestion import ingest as excel_ingest
from adapter.view_executor import execute_views, verify_views, drop_views

#APP SETUP

app = FastAPI(title="Lantern Intelligence")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADAPTER_TYPES = {
    "service": ServiceBusinessAdapter,
}

#Requests Models

class HistoryExchange(BaseModel):
    question: str
    answer: str

class QuestionRequests(BaseModel):
    question: str
    db_key: str
    history: Optional[List[HistoryExchange]] = []

class InspectRequest(BaseModel):
    db_path: str
    business_type: str = "service"

class ConfirmMappingRequests(BaseModel):
    db_path: str
    business_type: str = "service"
    mapping: dict

#Streaming Generator

def stream_ollama(prompt):
    """Generator that yields tokens from ollama as they arive."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.1,
            "num_predict": 512
        }
    }
    try:
        response = req.post(OLLAMA_URL, json=payload, stream=True, timeout=120)
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        yield f"ERROR: {str(e)}"

#Chat endpoints
@app.post("/ask")
async def ask_question(req_body: QuestionRequests):
    history = [{"question": h.question, "answer": h.answer}
                for h in req_body.history]
    prompt = prepare(req_body.question, req_body.db_key, history=history)
    return StreamingResponse(stream_ollama(prompt), media_type='text/plain')

@app.post("/ask_eval")
async def ask_eval(req_body: QuestionRequests):
    history = [{"question": h.question, "answer": h.answer}
                for h in req_body.history]
    prompt = prepare(req_body.question, req_body.db_key, history=history)
    full_response = ""
    for token in stream_ollama(prompt):
        if token.startswith("ERROR:"):
            return {"erro": token}
        full_response += token
    return {
        "question": req_body.question,
        "company": COMPANY_NAMES.get(req_body.db_key, req_body.db_key),
        "answer": full_response,
        "selectec_queries": route(req_body.question)
    }

#Company database endpoints

@app.get("/companies")
async def get_companies():
    """Returns demo companies plus all registered external databases."""
    companies = [
        {"key": k, "name": v, "source": "demo"}
        for k, v in COMPANY_NAMES.items()
    ]
    for entry in reg.list_registered():
        companies.append({
            "key": entry["db_path"],
            "name": entry.get("company_name", entry["db_name"]),
            "source": "external",
        })
    return {"companies": companies}

@app.post("/upload")
async def upload_database(file: UploadFile = File(...)):
    """
    Accept a file upload. Excel/CSV files are normalized to
    SQLite via ingestion; .db files are used directly.
    """
    uploads_dir = PROJECT_ROOT / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    file_path = uploads_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    suffix = file_path.suffix.lower()
    try:
        if suffix in (".xlsx", ".xls", ".csv"):
            db_path = excel_ingest(str(file_path))
        elif suffix in (".db", ".sqlite", ".sqlite3"):
            db_path = str(file_path.resolve())
        else:
            return {"success": False,
                    "error": f"Unsupported file type: {suffix}"}
        return {"success": True, "db_path": db_path}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/inspect-and-suggest")
async def inspect_and_suggest(req: InspectRequest):
    """
    Inspect a data schema adn return suggested canonical mappings. Called after connecting a SQLite database or
    after excel ingestion completes.
    """
    if req.business_type not in ADAPTER_TYPES:
        return {"error": f"Uknown business type: {req.business_type}"}
    try:
        adapter = ADAPTER_TYPES[req.business_type](req.db_path)
        schema = adapter.inspect_schema()
        suggestions = adapter.suggest_mappings(schema)
        return {"schema": schema, "suggestions": suggestions}
    except Exception as e:
        return {"error": str(e)}

@app.post("/confirm-mapping")
async def confirm_mapping_endpoint(body: ConfirmMappingRequests):
    if body.business_type not in ADAPTER_TYPES:
        return {"error": f"Unknown business type: {body.business_type}"}

    adapter = ADAPTER_TYPES[body.business_type](body.db_path)
    schema = adapter.inspect_schema()

    # Validate required fields
    errors = adapter.validate_mapping(body.mapping)
    if errors:
        return {"success": False, "errors": errors}

    # Drop existing views ONLY if re-mapping
    if reg.is_registered(body.db_path):
        drop_views(body.db_path, list(CANONICAL_SCHEMA.keys()))
        reg.unregister(body.db_path)

    # Generate and execute views
    view_sqls = adapter.generate_views(body.mapping)
    execute_errors = execute_views(body.db_path, view_sqls)
    if execute_errors:
        return {"success": False, "errors": execute_errors}

    # Verify views are queryable
    verify_errors = verify_views(body.db_path, list(CANONICAL_SCHEMA.keys()))
    if verify_errors:
        drop_views(body.db_path, list(CANONICAL_SCHEMA.keys()))
        return {"success": False, "errors": verify_errors}

    # Pull company name from the canonical company view
    company_name = Path(body.db_path).stem
    try:
        conn = sqlite3.connect(body.db_path)
        row = conn.execute("SELECT company_name FROM company LIMIT 1").fetchone()
        if row:
            company_name = row[0]
        conn.close()
    except Exception:
        pass

    # Register
    reg.register(
        db_path=body.db_path,
        business_type=body.business_type,
        mapping=body.mapping,
        schema=schema,
        company_name=company_name
    )

    return {
        "success": True,
        "db_path": body.db_path,
        "company_name": company_name
    }

@app.delete("/database")
async def delete_database(db_path: str):
    """Unregister a database from registry"""
    reg.unregister(db_path)
    return {"success": True}

#Utility Endpoints
@app.post("/route")
async def get_routes(req_body: QuestionRequests):
    queries = route(req_body.question)
    return {"queries": queries}

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open(TEMPLATES_DIR / "index.html", "r") as f:
        return f.read()
