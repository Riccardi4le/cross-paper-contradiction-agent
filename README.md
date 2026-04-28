# Cross-Paper Contradiction Agent

An AI agent that **doesn't synthesize** research papers — it makes them argue.

Given N papers on the same topic, it extracts empirical claims, clusters them by theme, detects where papers conflict, and **diagnoses why**: different methodology? different population? definitional mismatch? genuine scientific conflict?

## What makes it different

Every AI paper tool today does synthesis: "the consensus says X". But in active research areas there *is* no consensus — there's productive disagreement that AI synthesis flattens.

This agent does the opposite: **show me where papers fight, and explain why**.

## Output example

```markdown
# Contradiction Map — Intermittent Fasting & Weight Loss
Papers analyzed: 4 | Claims: 38 | Clusters: 9 | Contradictions: 3

## Cluster 1 — Long-term weight regain after fasting
🔴 CONFLICT

**Kim 2022** (n=120, 1y follow-up)
> "Participants maintained 90% of weight loss at 12 months"

**Park 2023** (n=450, 2y follow-up)
> "73% of subjects showed full weight regain within 24 months"

### Diagnosis: `population`
Kim recruited from a weight-loss clinic (high motivation), Park from the general population.
Both findings are correct — for different populations.

**Recommendation:** Cite both, specifying the population and time horizon.
```

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) running locally with a model pulled

## Setup

```bash
# 1. Clone / navigate to the project
cd CPC_agent

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Ollama and pull a model
# Download Ollama: https://ollama.com
ollama pull qwen2.5:7b-instruct   # recommended
# or: ollama pull llama3.1:8b

# 4. Start Ollama (if not already running as a service)
ollama serve

# 5. (Optional) copy .env.example to configure model/host
cp .env.example .env
```

## Web UI

A local web interface is available — no CLI needed.

```bash
python webapp.py
# then open http://localhost:5000
```

Features: drag-and-drop PDF upload, live model selection from Ollama, animated phase-by-phase progress, rendered contradiction map in the browser, one-click download.

## CLI usage

```bash
# Basic
python main.py paper1.pdf paper2.pdf paper3.pdf

# With topic label
python main.py --topic "intermittent fasting" papers/*.pdf

# Override model
python main.py --model llama3.1:8b paper1.pdf paper2.pdf

# Custom output directory
python main.py --output-dir ./results paper1.pdf paper2.pdf
```

Output is saved to `output/contradiction_map_<timestamp>.md`.

## Recent fixes

The following logic issues were fixed during review:

- **The clustering fallback could split a two-claim comparison into two singleton clusters.**
  Action taken: when only two claims are present and HDBSCAN finds no structure, the fallback now keeps them in the same cluster so contradiction detection can still run.
- **Conflict investigation only compared the first two papers in a cluster.**
  Action taken: investigation now aggregates pairwise comparisons across all paper pairs inside a flagged cluster before producing the final diagnosis.
- **Multi-paper contradictions could therefore be underdiagnosed or misdiagnosed.**
  Action taken: the final diagnostic summary now uses evidence from the whole cluster instead of an arbitrary first pair.

Practical implication:

- Two-paper runs are less likely to miss obvious conflicts.
- Three-or-more-paper runs now preserve more of the disagreement structure in the final contradiction map.

### Web UI fixes

The local web interface was also improved:

- **Rendered markdown and warning messages were too trusting.**
  Action taken: markdown output and dynamic error content are now sanitized or escaped before entering the DOM.
- **Uploaded files with the same filename could collide on disk.**
  Action taken: uploaded PDFs are now stored with unique generated prefixes.
- **Ollama model validation was too permissive.**
  Action taken: the selected model must now match an actual available model name exactly.

## Pipeline

```
[PDF files]
    ↓
Phase 0 — Ingest        PyMuPDF → text + metadata
    ↓
Phase 1 — Extract       LLM extracts structured claims per paper
    ↓
Phase 2 — Cluster       Embeddings + HDBSCAN → claim groups by topic
    ↓
Phase 3 — Detect        LLM-as-judge: agreement / partial / conflict / unrelated
    ↓
Phase 4 — Investigate   Compare methodology, population, definitions → diagnose
    ↓
Phase 5 — Build Map     Render structured Markdown contradiction map
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct` | Model for all LLM calls |

Set via `.env` file or environment variables.

## Tech stack

- **LangGraph** — multi-phase pipeline orchestration
- **Ollama** — local LLM inference (zero API costs)
- **sentence-transformers** — local embeddings (`all-MiniLM-L6-v2`)
- **HDBSCAN** — density-based claim clustering
- **PyMuPDF** — PDF text extraction
- **Pydantic v2** — structured output validation
- **Flask** — local web UI server
- **Rich** — terminal output
