FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/home/user/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/home/user/.cache/sentence-transformers \
    PORT=7860

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app

COPY --chown=user:user requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
ENV PATH="/home/user/.local/bin:$PATH"

COPY --chown=user:user . .

RUN mkdir -p /home/user/app/output \
    && mkdir -p /home/user/.cache/huggingface \
    && mkdir -p /home/user/.cache/sentence-transformers

EXPOSE 7860

CMD ["python", "webapp.py"]
