FROM python:3.11-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    poppler-utils \
    libzbar0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0"]
