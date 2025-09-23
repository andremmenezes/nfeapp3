FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils libzbar0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app

ENV PORT=8000
EXPOSE 8000
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
CMD ["streamlit", "run", "app.py", "--server.port", "8000", "--server.address", "0.0.0.0"]

