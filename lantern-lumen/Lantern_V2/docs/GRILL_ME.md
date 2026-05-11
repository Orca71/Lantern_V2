# GRILL_ME.md

## Purpose
This document contains questions used to pressure-test Lantern’s architecture, reasoning, retrieval, and shippability.

---

## 1. System Identity
- What exact problem does Lantern solve?
- Who is the user?
- What question should Lantern answer better than a normal chatbot?
- What makes Lantern more than an LLM wrapper?

---

## 2. Data Flow
- Where does the user question enter?
- Which module touches the question first?
- What is the exact order: router, retriever, classifier, advisor?
- Where does the final response get created?
- Which module owns orchestration?

---

## 3. Module Boundaries
- Does each script have one clear responsibility?
- Is any module doing another module’s job?
- Should `query_router.py` or `retrieve.py` own classification?
- Does `app.py` contain business logic?
- Does `advisor.py` retrieve data, or only reason over retrieved data?

---

## 4. Retrieval
- How does Lantern decide which PDF concepts are relevant?
- What happens if ChromaDB returns weak or irrelevant chunks?
- Does Lantern measure retrieval confidence?
- Are duplicate chunks possible?
- What happens if no relevant context is found?

---

## 5. Live Database
- What schema does Lantern expect?
- What happens if a real database has different table or column names?
- What fields are required for financial advice?
- How does Lantern report missing fields?
- Where should the schema adapter live?

---

## 6. Metric Classification
- Who owns metric classification?
- Does the LLM ever override structured classification?
- What happens if a metric is missing?
- What happens if classification fails?
- Are classification rules deterministic and explainable?

---

## 7. LLM Reasoning
- What exactly is the LLM allowed to do?
- What is the LLM not allowed to do?
- How do we prevent hallucinated classifications?
- How do we force concise answers?
- What evidence must be included before the LLM answers?

---

## 8. Evaluation / Safety
- How does Lantern detect hallucination?
- How does it check whether an answer is grounded?
- What makes an answer unacceptable?
- Does Lantern refuse or warn when evidence is insufficient?
- Is there an evaluator before the response reaches the user?

---

## 9. Shippability
- What must work reliably in a recruiter demo?
- What parts are still fragile?
- What breaks if the database changes?
- What breaks if the LLM changes?
- What is the minimum version that counts as shippable?

---

## 10. Next Refactor
- What is the single biggest architectural confusion right now?
- What redundant logic should be removed first?
- Which module should become the source of truth for routing?
- Which change would reduce hallucination the most?
- Which change would make Lantern easier to explain?
