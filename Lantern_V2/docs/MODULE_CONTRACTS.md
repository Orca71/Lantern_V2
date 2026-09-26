# MODULE_CONTRACTS.md

## `app.py`

### Accepts
- User prompts
- JSON request bodies
- HTTP POST requests

### Returns
- JSON responses
- Streamed responses, if applicable

### Guarantees
- Receives user-facing requests through the API
- Validates request shape through request models
- Returns responses in a consistent API format

### Should Never
- Perform core financial reasoning
- Directly ingest documents
- Directly manage database schema logic
- Return unstructured/random response formats


# MODULE_CONTRACTS.md

## `advisor.py`

### Accepts
- User question from `app.py`
- Retrieved context from `retrieve.py`
- Query type or metric category, if provided

### Returns
- Final advisory response
- Model-generated answer
- Possibly supporting reasoning/context metadata

### Guarantees
- Builds the reasoning/prompt context for the model
- Follows Lantern’s advisor instructions
- Returns a response that `app.py` can send back to the user

### Should Never
- Interact directly with the user interface
- Handle API routes or HTTP requests
- Ingest documents
- Modify database schemas
- Ignore system instructions or retrieved context

## `metrics_classifier.py`

### Accepts
- YAML schema path
- SQL rows or structured live data
- Metric fields/values to classify

### Returns
- Metric classifications
- Prompt-ready metric summary block
- Extraction errors, if any

### Guarantees
- Loads classification rules from the YAML schema
- Classifies live data according to the schema
- Extracts relevant metrics from SQL rows when available
- Returns errors when extraction or classification fails
- Produces a structured block that `advisor.py` can use

### Should Never
- Interact directly with the user interface
- Generate the final advisory answer
- Retrieve documents from ChromaDB
- Modify the source database
- Return a full LLM prompt

## `retrieve.py`

### Accepts
- ChromaDB path / collection
- Live SQL database path
- User query or routed query type
- Retrieval parameters, if provided

### Returns
- Retrieved conceptual context from ChromaDB
- Retrieved live financial data from SQL
- Relevant metadata or source information

### Guarantees
- Retrieves relevant concepts and live data for the user query
- Uses lazy loading for SQL sources when appropriate
- Avoids loading unnecessary SQL databases/scripts
- Returns evidence that `advisor.py` can use

### Should Never
- Generate the final advisory answer
- Interact directly with the user interface
- Load every SQL source when only one is needed
- Modify source databases
- Silently continue with invalid database or ChromaDB paths

## `query_router.py`

### Accepts
- User question from `advisor.py` or `app.py`
- Query keywords / search terms
- Available SQL source names or routing rules

### Returns
- Relevant SQL source or SQL category
- Route decision for which data source should be used

### Guarantees
- Identifies the most relevant SQL source for the user question
- Uses query keywords or routing rules to match the question to the right data source
- Returns a route that `retrieve.py` can use

### Should Never
- Generate the final advisory answer
- Retrieve the actual SQL data directly, unless explicitly designed to do so
- Perform metric classification handled by

## `ingest.py`

### Accepts
- Path to financial PDFs
- ChromaDB storage path / collection name
- Embedding configuration, if provided

### Returns
- Embedded financial PDF chunks
- Updated ChromaDB vector database
- Ingestion status or errors

### Guarantees
- Loads financial PDFs
- Splits documents into retrievable chunks
- Embeds financial PDF content
- Stores embeddings and metadata in ChromaDB
- Avoids duplicate embeddings when possible

### Should Never
- Generate advisory answers
- Perform metric classification
- Modify live SQL databases
- Run during every user question
- Create duplicate embeddings without detection
