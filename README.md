# Lantern V2

A local AI decision-support system that answers financial and operational
questions about a company's own data — and answers them with numbers it computed,
not numbers it generated.

Runs entirely on local infrastructure. No data leaves the machine.

## The problem this is built around

Ask an LLM "what was our net profit margin last quarter?" over a retrieval
pipeline and you will sometimes get a confident, well-formatted, wrong number.
Retrieval finds text that looks relevant; generation produces something that reads
like an answer. Neither step computes anything.

For business questions where the figure is the answer, that failure mode is
disqualifying.

## How it works

Lantern V2 separates the two jobs:

```
Question
   │
   ├─► Schema mapping ──► SQL query ──► exact figures        (deterministic)
   │
   ├─► Vector retrieval ──► benchmarks, definitions, context (semantic)
   │
   └─► LLM ──► interpretation grounded in both              (generative)
```

**SQL runs first.** Every figure in the response comes from a query against the
source database, not from the model. **Retrieval supplies context** — what the
metric means, what a healthy range looks like. **The LLM interprets** the numbers
it was handed. It is never the source of a number.

## What it computes

Eight financial and operational metrics, each backed by its own query:

net profit margin · days sales outstanding · client concentration · burn rate ·
revenue trend · expense breakdown · revenue per employee · client and revenue churn

Ships with three synthetic consulting-firm datasets — Apex Strategy, Meridian
Consulting Group, and Vertex Advisory Partners — each with a deliberately
different financial profile, so the system can be exercised end to end without
proprietary data.

## Adapting to a new database

Business schemas never match. The adapter layer maps incoming column names to the
metrics via synonym matching and generates SQL views over whatever it finds, so
the same eight queries run against a new dataset without rewriting them.

Before executing, the system shows the user its interpretation of the question and
which fields it plans to use, and waits for confirmation. Silent misinterpretation
is the expensive failure in a system like this; confirmation makes it visible.

## Evaluation

Responses are scored on relevance, faithfulness, accuracy, and overall quality,
with results written to an HTML viewer for inspection. Failures are traced to the
stage that produced them — retrieval, SQL, or generation — rather than logged as a
single pass/fail.

<!-- ADD YOUR ACTUAL SCORES HERE. A table of results across the three datasets is
the single most valuable thing you can put in this README — almost no portfolio
project reports evaluation numbers on its own output. Even mediocre scores beat no
scores, because reporting them is the credible act. -->

## Stack

| | |
|---|---|
| API | FastAPI |
| LLM | Ollama, llama3.1:8b (local) |
| Vector store | ChromaDB |
| Database | SQLite |
| Container | Docker |
| Tested on | RunPod, RTX 3090 |

## Running it

```bash
docker pull shahn17/lantern-lumen:latest
docker run -p 8000:8000 shahn17/lantern-lumen:latest
```

<!-- Verify this command actually works from a clean machine before publishing.
A run command that fails is worse than no run command. -->

## Relationship to Lantern Intelligence (V1)

<!-- One or two sentences: what V1 was, and why V2 is a different system rather
than a rewrite. Right now both repos are pinned with no explanation and a reader
assumes V2 replaced a failed V1. If they're genuinely different systems, saying so
turns two half-finished-looking repos into two projects. -->

---

<!-- BEFORE PUBLISHING:

1. Secrets scan — RunPod keys, API keys, tokens. Check git history, not just
   current files. `git log -p | grep -iE "key|token|secret|password"`
2. Hardcoded paths — D:\runpod_backup\ and /workspace/Lantern_V2/ will be noticed.
3. Set the About description on the repo (separate from this README — the pinned
   card pulls from About only).
4. Add topics: rag, llm, fastapi, chromadb, ollama, sql, local-llm, evaluation
5. Delete every HTML comment in this file.
-->
