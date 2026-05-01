# Deploy su Hugging Face Spaces

Guida rapida per pubblicare l'agente come **Docker Space**.

## 1. Crea lo Space

1. Vai su https://huggingface.co/new-space
2. **Owner**: il tuo username
3. **Space name**: es. `cpc-agent`
4. **License**: MIT (o quella che preferisci)
5. **SDK**: **Docker** → *Blank*
6. **Hardware**: CPU basic è sufficiente (l'inferenza LLM avviene su Groq)
7. Crea lo Space

## 2. Configura il segreto Groq

Nello Space appena creato → **Settings → Variables and secrets**:

- **New secret**
  - Name: `GROQ_API_KEY`
  - Value: la tua chiave da https://console.groq.com/keys

(Opzionale) **New variable** pubblica:
- `GROQ_MODEL` = `llama-3.3-70b-versatile`

## 3. Push del codice

Dalla root del progetto:

```bash
# Login (una volta sola)
huggingface-cli login

# Aggiungi il remote dello Space
git remote add space https://huggingface.co/spaces/<tuo-user>/cpc-agent

# Push
git push space main
```

In alternativa, se il branch principale è `main` ma lo Space si aspetta `main`:

```bash
git push space main:main
```

## 4. Verifica il build

- La tab **Logs** mostra il build del `Dockerfile`.
- Al primo avvio `sentence-transformers` scarica `all-MiniLM-L6-v2` (~90 MB).
- Quando lo stato passa a **Running**, apri lo Space — vedrai la UI Flask.

## File chiave

- `Dockerfile` — build del container, espone porta 7860 (richiesto da HF).
- `.dockerignore` — esclude `output/`, `sample_papers/`, `.pptx`, ecc.
- `webapp.py` — legge `HOST` e `PORT` da env var.
- `README.md` — frontmatter YAML obbligatorio (`sdk: docker`, `app_port: 7860`).

## Troubleshooting

- **"GROQ_API_KEY is not set"** → secret mancante o nome sbagliato. Deve essere esattamente `GROQ_API_KEY`.
- **Build OOM** → CPU basic ha 16 GB; se fallisse, aggiungi `--no-cache-dir` (già presente) o passa a hardware più grande.
- **Permission denied su `output/`** → il `Dockerfile` crea la dir come `user` (UID 1000), che è il default richiesto da HF Spaces.
- **Modello sentence-transformers scarica ogni cold start** → normale su Space gratuiti senza storage persistente. Per persistenza, abilita *Persistent storage* nelle Settings dello Space e monta `/data`.
