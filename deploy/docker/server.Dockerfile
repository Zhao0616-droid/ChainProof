FROM python:3.12-slim

WORKDIR /app
COPY deploy/docker/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY engine/ engine/
COPY ai/ ai/
COPY server/ server/
COPY examples/ examples/

WORKDIR /app/server
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
