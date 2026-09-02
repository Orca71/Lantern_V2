<div align="center">

# Lantern V2

**A local AI decision-support system that answers financial questions about your data —<br/>with numbers it computed, not numbers it generated.**

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-llama3.1:8b-000000?style=flat-square)
![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6B6B?style=flat-square)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![Runs Locally](https://img.shields.io/badge/runs-100%25%20locally-success?style=flat-square)

</div>

---

## The problem

Ask an LLM for your net profit margin and two things can go wrong: it recalls the wrong formula, and it invents a plausible number.

Lantern takes both jobs away from the model.

## The pipeline

```mermaid
flowchart LR
    Q([Question]) --> R
    R["<b>RAG</b><br/>retrieves the definition<br/>and benchmarks"]
    S["<b>SQLite</b><br/>executes it against<br/>your data"]
    L["<b>LLM</b><br/>interprets a figure<br/>it did not produce"]
    R --> S --> L --> A([Answer])

    style Q fill:#1f6feb,stroke:none,color:#fff
    style A fill:#238636,stroke:none,color:#fff
    style R fill:#8957e5,stroke:none,color:#fff
    style S fill:#1f6feb,stroke:none,color:#fff
    style L fill:#db6d28,stroke:none,color:#fff
```

> [!IMPORTANT]
> The model never supplies the formula or the number. It only explains the result.

## What it computes

| | | | |
|---|---|---|---|
| Net profit margin | Days sales outstanding | Client concentration | Burn rate |
| Revenue trend | Expense breakdown | Revenue per employee | Client & revenue churn |

## Adapting to a new database

Business schemas never match. An adapter layer maps incoming column names to the required fields by synonym matching and generates SQL views, so the same queries run against a schema they've never seen.

> [!NOTE]
> Before executing, the system shows its interpretation of the question and waits for confirmation. Silent misinterpretation is the expensive failure here — confirmation makes it visible.

## Testing

Validated end to end through manual testing across the three synthetic datasets, with incorrect results traced to the stage that caused them — retrieval, SQL, or generation.

> [!NOTE]
> Automated scoring is the next planned addition. Right now correctness is verified by hand against known values in the synthetic data.

## Data

Ships with three synthetic consulting-firm datasets I generated — **Apex Strategy**, **Meridian Consulting Group**, and **Vertex Advisory Partners** — each with a deliberately different financial profile, so the system runs end to end without proprietary data.

## Running locally

Built to run entirely on local hardware — no cloud services, no external model APIs, no data leaving the machine. Developed and tested against a local Ollama instance.
