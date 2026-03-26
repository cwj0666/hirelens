FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY src ./src
COPY data ./data
COPY docker ./docker
COPY README.md ./

RUN chmod +x /app/docker/*.sh \
    && mkdir -p /app/data/runtime /app/outputs

EXPOSE 8501 8000

CMD ["/app/docker/run-streamlit.sh"]
