# SYSTEM_OVERVIEW.md

## What Lantern Is
- Lantern is a prototype financial AI advisory system designed for small businesses.
- It combines financial statement retrieval, live database analysis, metric classification, and LLM reasoning to answer financial and business questions.

## Core Goal
- Provide grounded financial and business advisory after analyzing available company data, financial statements, and structured metrics.

## Current Architecture
- UI / API interface layer (`app.py`)
- Query routing layer (`query_router.py`)
- Retrieval layer (`retrieve.py`)
- Metric classification layer (`metrics_classifier.py`)
- Advisory / reasoning layer (`advisor.py`)
- Knowledge ingestion layer (`ingest.py`)
- RAG + live database integration

## Current Strengths
- Working prototype
- Modular script structure
- Financial PDF ingestion + ChromaDB retrieval
- Live company database integration
- YAML-based metric classification
- Early architecture documentation and audit process

## Current Weaknesses
- LLM hallucination risk
- Inconsistent instruction-following
- Limited adaptability to new database schemas
- Redundant or unclear classification pipeline
- LLM may override pre-classified data
- Prototype still relies on controlled datasets

## Current Prototype State
- 8 financial statements
- 3 live company databases
- No schema adapter layer yet
- Controlled environment

## Long-Term Goal
- A polished, recruiter-ready, shippable financial advisory prototype that:
  - Minimizes hallucination
  - Follows strict instruction hierarchy
  - Adapts to multiple database schemas
  - Uses clear module boundaries
  - Demonstrates production-oriented software and system practices
