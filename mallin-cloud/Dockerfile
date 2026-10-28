FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends git nodejs npm ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py index.html ./
RUN mkdir -p /data/deployments
ENV MALLIN_DEPLOY_ROOT=/data/deployments PORT=8787
EXPOSE 8787
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8787}"]
