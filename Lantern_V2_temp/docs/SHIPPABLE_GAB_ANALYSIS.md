# SHIPPABLE_GAP_ANALYSIS.md

## Current Prototype State
- Reads 8 financial statements.
- Uses live databases for 3 demo companies.
- Does not yet have a database adapter layer.
- LLM can still hallucinate.
- LLM does not always follow instructions consistently.

## Shippable Prototype Goal
- A grounded financial advisory system that gives concise answers, avoids unsupported claims, follows instructions, and works reliably on controlled demo datasets.

---

## Gap 1: Database Portability

### Current State
- Lantern only supports live databases for 3 demo companies.
- Current live data access depends on one expected schema.

### Risk
- Real databases may not match Lantern’s expected schema.
- Missing or renamed fields could break retrieval and metric classification.

### Needed Improvement
- Add a database adapter layer.

### Future Direction
- Create an adapter that maps real database schemas into Lantern’s internal canonical schema.

---

## Gap 2: LLM Hallucination / Instruction Following

### Current State
- The LLM sometimes performs its own classification even after classification is already provided.
- The LLM does not always follow advisor instructions fully.

### Risk
- Wrong classification.
- Wrong reasoning based on wrong classification.
- Unsupported financial advice.

### Needed Improvement
- Improve instruction hierarchy and prompt structure.
- Prevent the LLM from overriding structured classifications.
- Add validation/evaluation before returning answers.

### Future Direction
- Strengthen the layers before the LLM.
- Test a different LLM if instruction-following remains weak.
- Add an evaluator/checker that flags unsupported claims.

---

## Gap 3: Redundant Classification / Routing Logic

### Current State
- `query_router.py` and `retrieve.py` both appear to classify or match the user question against financial PDF concepts.
- Only one module should own this responsibility.

### Risk
- Unclear classification pipeline.
- Conflicting classification results.
- Harder debugging and maintenance.

### Needed Improvement
- Establish one source of truth for PDF/concept routing.

### Future Direction
- Decide whether `query_router.py` or `retrieve.py` owns PDF/concept classification.
- Keep the other module focused on its core responsibility.
- Remove or refactor redundant functions.
