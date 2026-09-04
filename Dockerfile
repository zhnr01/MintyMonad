FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/instance && useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 5050
ENTRYPOINT ["/app/docker-entrypoint.sh"]
