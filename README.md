Lantern V2

A local AI decision-support system that answers financial questions about a company's data — with numbers it computed, not numbers it generated. Runs entirely on local infrastructure; no data leaves the machine.

Why

Ask an LLM for your net profit margin and two things can go wrong: it recalls the wrong formula, and it invents a plausible number. Lantern takes both jobs away from the model.

How
Question → RAG      retrieves the metric definition and benchmarks
         → SQLite   executes that definition against the data
         → LLM      interprets a figure it did not produce

The model never supplies the formula or the number. It only explains the result.

What it computes

Net profit margin · days sales outstanding · client concentration · burn rate · revenue trend · expense breakdown · revenue per employee · client and revenue churn

Adapting to a new database

An adapter layer maps incoming column names to required fields by synonym matching and generates SQL views, so the same queries run against an unfamiliar schema. Before executing, the system shows its interpretation of the question and waits for confirmation.
