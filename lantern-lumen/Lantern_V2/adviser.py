# =============================================================
# LANTERN INTELLIGENCE v2 — adviser.py
# Phase 5: LLM reasoning layer
# =============================================================

import json
import requests
from query_router import route
from retrieve import retrieve
from metrics_classifier import pre_classify_live_data, format_classifications_for_prompt
from config import OLLAMA_URL, OLLAMA_MODEL, COMPANY_NAMES
from adapter import registry as reg
from pathlib import Path

# -------------------------------------------------------------
# BUILD PROMPT
# -------------------------------------------------------------

def build_prompt(question, company_name, live_data, concepts,
                 selected_queries, history=None):

    classifications      = pre_classify_live_data(live_data)
    classification_block = format_classifications_for_prompt(classifications)

    system = f"""You are Lantern, an AI financial adviser for small businesses, analyzing {company_name}.
Answer financial questions using ONLY the live data, retrieved concepts, and conversation history in this prompt.

VALIDITY CHECK — DO THIS FIRST:
- Before using any formula, confirm the inputs are valid.
- If inputs are invalid, do not force a calculation. State the issue and stop.
- Do NOT use absolute values to fix negative inputs or invent alternate formulas.
- If PRE-COMPUTED CLASSIFICATIONS show Runway as PROFITABLE:
  - Do not calculate runway.
  - State the company is not currently burning cash.
  - State runway is not a current constraint.
  - Do not speculate about future cash depletion.

DATA HIERARCHY:
1. PRE-COMPUTED CLASSIFICATIONS are ground truth. State them as established facts. Never re-classify, qualify, or contradict them.
2. Live financial data is the source of truth for specific numbers.
3. Retrieved concepts provide definitions and formulas only — not conclusions or classifications.

RESPONSE FORMAT:
- Answer in 2–4 sentences. One short paragraph. No bullet points.
- State the metric value, its pre-computed classification, and one clear takeaway.
- Reference specific numbers from the live data.
- Do not show arithmetic or formula substitution.
- Do not hedge. Never use phrases like "I can see", "I can conclude", or "it appears".
- Do not introduce metrics the question did not ask about.
- Do not use phrases like "the live data shows" — reference numbers directly.
- When explaining causes, frame them as possibilities, not facts.
- If data is missing or invalid, say so clearly and stop.

If the question asks for predictions or forecasts, respond ONLY with:
"I can only analyze historical data. I cannot predict future performance."

If the question asks about a company not in your data, respond ONLY with:
"I only have data for {company_name}."

If the question is a greeting or unrelated to financial analysis, respond ONLY with:
"I am Lantern, your financial adviser for {company_name}. Please ask me a financial question."
"""

    concept_section = "\n\n=== FINANCIAL CONCEPT KNOWLEDGE ===\n"
    for concept in concepts:
        concept_section += f"\n--- {concept['metric']} ---\n"
        concept_section += concept["text"]
        concept_section += "\n"

    data_section = "\n\n=== LIVE FINANCIAL DATA ===\n"
    data_section += f"Company: {company_name}\n\n"

    for query_name in selected_queries:
        rows = live_data.get(query_name, [])
        data_section += f"[ {query_name.upper().replace('_', ' ')} ]\n"

        if isinstance(rows, dict) and "error" in rows:
            data_section += f"  ERROR: {rows['error']}\n"
        elif isinstance(rows, list) and len(rows) == 0:
            data_section += "  No data returned\n"
        elif isinstance(rows, list):
            for row in rows:
                for key, value in row.items():
                    data_section += f"  {key}: {value}\n"
                data_section += "\n"
        else:
            data_section += f"  {rows}\n"

    history_section = ""
    if history:
        history_section = "\n\n=== CONVERSATION HISTORY ===\n"
        history_section += "(Previous exchanges in this session)\n\n"
        for exchange in history:
            history_section += f"User: {exchange['question']}\n"
            history_section += f"Lantern: {exchange['answer']}\n\n"

    prompt = f"""{system}

{classification_block}

{concept_section}

{data_section}

{history_section}

=== CURRENT QUESTION ===
{question}

=== YOUR RESPONSE ===
Answer directly using the PRE-COMPUTED CLASSIFICATIONS and live data above.
Reference specific numbers. 2–4 sentences maximum.
"""

    return prompt


# -------------------------------------------------------------
# OLLAMA CALL
# -------------------------------------------------------------

def call_ollama(prompt, stream=True):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": stream,
        "options": {
            "temperature": 0.1,
            "num_predict": 512,
        },
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            stream=stream,
            timeout=120,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        return "ERROR: Cannot connect to Ollama. Make sure the server is running."
    except requests.exceptions.Timeout:
        return "ERROR: Ollama timed out."

    full_response = ""

    if stream:
        print("\nLantern: ", end="", flush=True)
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    print(token, end="", flush=True)
                    full_response += token
                    if chunk.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue
        print("\n")
    else:
        data = response.json()
        full_response = data.get("response", "")

    return full_response

# Prepare function, for both HTTP streaming and CLI

def prepare(question, db_key, history=None):
    company_name = COMPANY_NAMES.get(db_key)
    if not company_name:
        for entry in reg.list_registered():
            if entry["db_path"] == db_key or \
               entry["db_path"] == str(Path(db_key).resolve()):
                company_name = entry.get(
                    "company_name",
                    entry.get("db_name", Path(db_key).stem)
                )
                break

    # Final fallback
    if not company_name:
        company_name = Path(db_key).stem \
            if ("/" in db_key or "\\" in db_key) else db_key
    selected_queries = route(question)
    context   = retrieve(question, db_key, selected_queries = selected_queries)
    live_data = context["live_data"]
    concepts  = context["concepts"]
    prompt = build_prompt(
        question=question,
        company_name=company_name,
        live_data=live_data,
        concepts=concepts,
        selected_queries=selected_queries,
        history=history
    )
    return prompt

# -------------------------------------------------------------
# ASK
# -------------------------------------------------------------

def ask(question, db_key):
    response = call_ollama(prepare(question, db_key))
    return response


# -------------------------------------------------------------
# QUICK TEST
# -------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("ADVISER.PY - Quick Test")
    print("=" * 60)

    test_cases = [
        ("Is our cash runway safe?", "service1"),
        ("Are we losing clients?", "service2"),
        ("How productive is our team?", "service3"),
    ]

    for question, db_key in test_cases:
        company = COMPANY_NAMES[db_key]
        print(f"\n{'=' * 60}")
        print(f"Company: {company}")
        print(f"Question: {question}")
        print("=" * 60)
        ask(question, db_key)
        print("\nPress Enter for next test")
        input()

    print("=" * 60)
    print("ALL TESTS COMPLETE.")
    print("=" * 60)
