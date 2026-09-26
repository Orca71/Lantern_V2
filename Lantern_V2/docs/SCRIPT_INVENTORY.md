# Lantern V2 Script Inventory

This document maps the purpose, inputs, outputs, dependencies, and boundaries of each Python script in Lantern V2.

Current scripts:

- `adviser.py`
- `app.py`
- `ingest.py`
- `main.py`
- `metrics_classifier.py`
- `query_router.py`
- `retrieve.py`

---

# `app.py`

## Purpose
- This is the web/UI interface where the system receives requests and returns responses.

## Why It Exists
- It is the communication layer between the user and system.

## Inputs
- User prompt/question
- db_key
- conversation history (optional)

## Outputs
- System response to the posted prompt
- Streaming response (`/ask`)
- Evaluation JSON (`/ask_eval`)

## Main Functions / Classes
- Main Functions:
  - run_classification
  - stream_ollama
  - ask_question
  - ask_eval
- Classes:
  - HistoryExchange
  - QuestionRequest

## Depends On
- json
- FastAPI
- BaseModel
- adviser.py
- retrieve.py
- query_router.py

## Used By
- Browser UI / frontend
- External API requests

## Should NOT Do
- Should not contain core financial reasoning logic
- Should not become overloaded with retrieval or classification logic

## Current Weaknesses
- Some business logic may be too close to interface layer
- May overlap with `main.py` as another interface layer

## Real-DB / Shippable Notes
- This is the interactive web/API layer where the user connects with the system.

## AI_suggestion
- Consider making `app.py` the primary production interface and eventually reducing `main.py` to development/debugging only.
- Keep this layer thin: request validation, orchestration, and response delivery only.

---

# `main.py`

## Purpose
- The terminal interaction layer between the LLM and the user
- It is an extension of adviser.py for CLI interaction

## Why It Exists
- Prevents overcrowding adviser.py
- Contains CLI/UI layer components

## Inputs
- Information from adviser.py
- User company selection
- User question

## Outputs
- Terminal-based entry point of information into the LLM by user

## Main Functions / Classes
- select_company - where one of the three companies is selected
- run_session - runs a session between LLM and user
- main - where everything comes together

## Depends On
- adviser.py
- company selection

## Used By
- Run directly by user through terminal
- Not used by app.py

## Should NOT Do
- Should not duplicate long-term production UI responsibilities if app.py becomes primary

## Current Weaknesses
- May be partially redundant with app.py
- Could create duplicate interface maintenance

## Real-DB / Shippable Notes
- Useful for debugging, testing, and CLI fallback

## AI_suggestion
- Reposition `main.py` as a development/testing shell unless CLI remains a strategic product feature.
- If web UI becomes stable, consider archiving `main.py` into a dev_tools or legacy folder.

---

# `adviser.py`

## Purpose
- This is where the LLM is loaded, the prompt is finalized, and sent to the LLM

## Why It Exists
- To load the LLM and feed structured information to it

## Inputs
- MODEL_URL
- Classification and live data results from metrics_classifier.py
- query_router.py
- Retrieved financial concepts and SQL data from retrieve.py
- User prompt/question

## Outputs
- Final answer from LLM

## Main Functions / Classes
- build_prompt - builds prompts using imported functions from multiple scripts combined with LLM instructions
- call_ollama
- ask

## Depends On
- retrieve.py
- query_router.py
- metrics_classifier.py

## Used By
- app.py
- main.py

## Should NOT Do
- Should not directly own UI responsibilities
- Should not become overloaded with raw retrieval logic

## Current Weaknesses
- Prompt engineering complexity may become difficult to maintain
- Heavy orchestration burden

## Real-DB / Shippable Notes
- Core reasoning/orchestration layer

## AI_suggestion
- This is the cognitive core of Lantern.
- Long term, consider modularizing prompt policy, response rules, and orchestration to avoid prompt bloat.

---

# `ingest.py`

## Purpose
- To read financial documents, embed them, and store them in ChromaDB

## Why It Exists
- This is the base knowledge source of this RAG system

## Inputs
- Financial documents

## Outputs
- ChromaDB containing embedded documents
- Verification of retrieval quality

## Main Functions / Classes
- No formal functions or classes

## Depends On
- SentenceTransformer (embedding)
- ChromaDB (storage)

## Used By
- retrieve.py

## Should NOT Do
- Anything beyond reading, embedding, storing, and validating retrieval integrity

## Current Weaknesses
- For loops and commands are not stored in unified functions
- Procedural design reduces modularity

## Real-DB / Shippable Notes
- The ChromaDB creation layer

## AI_suggestion
- Consider splitting into modular functions:
  - load_documents
  - embed_documents
  - store_documents
  - verify_retrieval
- Strong candidate for future ETL pipeline expansion.

---

# `retrieve.py`

## Purpose
- Loads and executes financial SQL queries on the selected SQLite database, and retrieves relevant financial concept documents from ChromaDB based on semantic similarity between the user’s question and embedded documents.

## Why It Exists
- Provides the adviser layer with grounded context by combining:
  - live financial metrics from the selected SQLite database
  - relevant financial concept documents from ChromaDB
- This allows the system to answer questions using both company-specific data and general financial knowledge.

## Inputs
- User question
- db_key
- Paths to SQLite DBs, ChromaDB, and queries

## Outputs
- Retrieval of desired documents and metrics

## Main Functions / Classes
- load_queries
- get_embedding_model
- get_collection
- get_sql_queries
- get_live_data
- get_concepts
- retrieve

## Depends On
- SQLite3
- ChromaDB

## Used By
- adviser.py

## Should NOT Do
- Should not generate final answers

## Current Weaknesses
- Currently runs all SQL queries, even though query_router may select relevant ones
- Possible overlap with query_router.py

## Real-DB / Shippable Notes
- Context assembly layer

## AI_suggestion
- Best architectural improvement: allow `query_router.py` to filter SQL execution before running all queries.
- Shift from “run all then filter” toward “select then execute.”

---

# `query_router.py`

## Purpose
- To find out which query words are found in the question using regex

## Why It Exists
- To prevent running all query scripts and only run the related queries to the question

## Inputs
- User question

## Outputs
- Related queries, or all queries if no match is found

## Main Functions / Classes
- route - cleans user questions, removes punctuation, and searches for query words

## Depends On
- Regex
- User question

## Used By
- adviser.py
- app.py

## Should NOT Do
- Should not execute SQL
- Should not retrieve ChromaDB concepts
- Should not generate answers

## Current Weaknesses
- Current design may overlap with retrieve.py if retrieval still runs all SQL queries
- Regex matching may miss semantic variations

## Real-DB / Shippable Notes
- Lightweight intent/query selection layer

## AI_suggestion
- Excellent candidate for future evolution:
  - Regex → embedding similarity
  - Regex → classifier
- Current regex system is fast MVP logic, but likely brittle at scale.

---

# `metrics_classifier.py`

## Purpose
- This is the pre-classification part of the system, whose job is to pre-classify the threshold of whatever metric has been chosen prior

## Why It Exists
- To remove the classification burden from the LLM

## Inputs
- YAML file containing threshold intervals for each metric
- Live data from SQL queries

## Outputs
- Classified metric thresholds
- Prompt-ready classification block for the LLM

## Main Functions / Classes
- _load_schema
- _validate_extraction
- _find_threshold
- _extract
- pre_classify_live_data
- format_classifications_for_prompt

## Depends On
- YAML file

## Used By
- adviser.py

## Should NOT Do
- Should not classify without YAML schema information

## Current Weaknesses
- Heavy dependence on YAML correctness
- Schema errors can break classification accuracy

## Real-DB / Shippable Notes
- Deterministic classification layer

## AI_suggestion
- Strong architectural move.
- Keeps benchmark logic deterministic and outside the LLM.
- Consider adding schema testing/versioning as Lantern grows.
