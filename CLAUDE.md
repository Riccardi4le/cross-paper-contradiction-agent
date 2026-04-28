# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the agent

```bash
# Web UI (recommended — drag-and-drop, no CLI needed)
python webapp.py
# then open http://localhost:5000

# CLI (minimum 2 PDFs)
python main.py paper1.pdf paper2.pdf paper3.pdf

# With options
python main.py --topic "intermittent fasting" --model llama3.1:8b papers/*.pdf

# Prerequisite: Ollama must be running with a model pulled
ollama serve
ollama pull qwen2.5:7b-instruct   # default model
```

## Web UI

`webapp.py` is a Flask server with 5 endpoints:
- `GET /` — serves `templates/index.html` (single-page app)
- `GET /api/models` — lists available Ollama models for the UI dropdown
- `POST /api/run` — accepts multipart PDF upload + model + topic, starts background job, returns `job_id`
- `GET /api/status/<job_id>` — polling: returns `{status, phase_index, phase_label, error_message}`
- `GET /api/result/<job_id>` — returns `{markdown, stats, errors}` once done

**Threading model:** jobs run in a background thread serialised by `_global_lock`. Only one job runs at a time — safe for a local single-user tool. `cpc_agent.llm.OLLAMA_MODEL` is monkey-patched inside the lock before each run to honour the model chosen in the UI.

## Installing dependencies

```bash
pip install -r requirements.txt
```

No build step. No test suite — this is a portfolio/demo project; the smoke test is running it end-to-end on real PDFs.

## Architecture

**5-phase LangGraph pipeline** with a shared `AgentState` TypedDict flowing linearly through nodes:

```
ingest → extract → cluster → detect → investigate → build_map
```

All state transitions are in `cpc_agent/graph.py`. Each node takes the full state dict and returns `{**state, <updated_keys>}`.

**Phase responsibilities:**
- `nodes/ingest.py` — PyMuPDF extracts text + metadata from PDFs into `Paper` objects. Long papers truncated at `MAX_PAPER_CHARS` (24k chars).
- `nodes/extract.py` — LLM extracts structured `Claim` objects per paper using JSON mode. Prioritizes abstract/results/discussion sections for long papers.
- `nodes/cluster.py` — sentence-transformers embeds all claims; sklearn `HDBSCAN` clusters them. Falls back to agglomerative if HDBSCAN produces no clusters. LLM labels each cluster topic.
- `nodes/detect.py` — LLM-as-judge classifies each multi-paper cluster: `agreement / partial / conflict / unrelated`. Only clusters with ≥2 papers are evaluated.
- `nodes/investigate.py` — For `conflict`/`partial` clusters only: runs 3 LLM comparators (methodology, population, definitions) then a final `diagnose_disagreement` call. Caps at `MAX_CONFLICT_PAIRS` (3) cross-paper pairs per cluster.
- `nodes/build_map.py` — Renders `output/contradiction_map_<timestamp>.md`. Sections ordered: conflict > partial > agreement > unrelated.

Note: older mentions of `MAX_CONFLICT_PAIRS` are outdated. The current implementation aggregates evidence across all paper pairs in a flagged cluster.

## Key design decisions

**Ollama JSON mode** (`format="json"`) is used for all structured calls in `llm.py`. The Pydantic schema is appended inline to every prompt — Ollama respects it better than relying on the schema parameter alone.

**Prompts are external files** in `cpc_agent/prompts/*.txt`, loaded once at module import time. Modify them directly to tune quality — no code changes needed. Each prompt uses `{placeholder}` format strings.

**`diagnose_disagreement` is the killer feature** — the 5-category diagnosis (`methodological / population / definitional / genuine_conflict / outdated_data`) is what differentiates this from a claim comparison tool. The `diagnose.txt` prompt is the most sensitive; treat it carefully.

**Config via env vars** (`.env` file or shell): `OLLAMA_HOST`, `OLLAMA_MODEL`, `CPC_OUTPUT_DIR`. `config.py` is imported lazily in `main.py` after env vars are set, so `--model` and `--output-dir` CLI flags work correctly.

**Non-fatal errors** accumulate in `state["errors"]` and are printed at the end + included in the output Markdown. Individual paper/cluster failures don't abort the run.

## Reliability updates

- The clustering fallback now keeps 2-claim runs together instead of splitting them into singleton clusters.
- Investigation now considers all paper pairs inside a conflicting cluster instead of only the first pair.
- Any references in older notes to `MAX_CONFLICT_PAIRS` are outdated; the current implementation aggregates evidence across the whole flagged cluster.
- The web UI now sanitizes rendered markdown, escapes dynamic warnings, stores uploads with unique filenames, and validates Ollama model names exactly.

## Adding a new phase or tool

1. Add a function in `cpc_agent/nodes/<new_node>.py` with signature `(state: AgentState) -> AgentState`
2. Register it in `graph.py` with `graph.add_node(...)` and `graph.add_edge(...)`
3. Add any new state keys to `AgentState` in `models.py`

## Model quality guidance

Quality scales with model size. `qwen2.5:7b-instruct` is the minimum. `qwen2.5:14b` or `mistral-nemo:12b` produce noticeably better diagnoses on ambiguous conflicts. The bottleneck is always `extract_claims.txt` (structured extraction) and `diagnose.txt` (nuanced classification).
