---
title: Cross-Paper Contradiction Agent
emoji: 📚
colorFrom: blue
colorTo: red
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Surface and diagnose contradictions across research papers.
---

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

## Run on Hugging Face Spaces

This repo is ready to deploy as a **Docker Space**.

1. Create a new Space → SDK: **Docker**.
2. Push this repository to the Space's git remote.
3. In **Settings → Variables and secrets**, add a secret:
   - `GROQ_API_KEY` = your key from https://console.groq.com/keys
4. (Optional) override the default model with a public variable:
   - `GROQ_MODEL` = `llama-3.3-70b-versatile`
5. The Space builds the `Dockerfile` and exposes the Flask UI on port `7860`.

```bash
# Push to a Space (after creating it on the HF website)
git remote add space https://huggingface.co/spaces/<your-user>/<space-name>
git push space main
```

## Run locally

```bash
pip install -r requirements.txt
echo "GROQ_API_KEY=sk-..." > .env
python webapp.py
# open http://localhost:7860
```

## CLI usage

```bash
# Basic (≥ 2 PDFs)
python main.py paper1.pdf paper2.pdf paper3.pdf

# With topic label
python main.py --topic "intermittent fasting" papers/*.pdf

# Override model
python main.py --model llama-3.1-8b-instant paper1.pdf paper2.pdf

# Custom output directory
python main.py --output-dir ./results paper1.pdf paper2.pdf
```

Output is saved to `output/contradiction_map_<timestamp>.md`.

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
| `GROQ_API_KEY` | *(required)* | Groq API key — set as a Space secret |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Model used for all LLM calls |
| `CPC_OUTPUT_DIR` | `./output` | Where the Markdown report is written |
| `PORT` | `7860` | Port the Flask UI binds to |
| `HOST` | `0.0.0.0` | Bind address |

Available Groq models (curated list shown in the UI dropdown):
`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `openai/gpt-oss-20b`,
`openai/gpt-oss-120b`, `moonshotai/kimi-k2-instruct`, `qwen/qwen3-32b`.

## Tech stack

- **LangGraph** — multi-phase pipeline orchestration
- **Groq** — fast hosted LLM inference
- **sentence-transformers** — embeddings (`all-MiniLM-L6-v2`)
- **HDBSCAN** — density-based claim clustering
- **PyMuPDF** — PDF text extraction
- **Pydantic v2** — structured output validation
- **Flask** — web UI server
- **Rich** — terminal output

## Notes on reliability

- The clustering fallback keeps 2-claim runs in the same cluster instead of splitting them into singletons, so contradiction detection still runs.
- Investigation aggregates pairwise comparisons across **all** paper pairs in a flagged cluster (not just the first pair).
- The web UI sanitizes rendered markdown, escapes dynamic warnings, stores uploads with unique filenames, and validates model names exactly against the curated list.
