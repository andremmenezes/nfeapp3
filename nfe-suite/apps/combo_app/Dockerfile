# ========= Base =========
FROM python:3.10-slim

# Evita prompts e deixa logs em tempo real
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Pacotes de SO necessários para pdf2image e pyzbar
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libzbar0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# ========= App =========
WORKDIR /app

# Copia requirements primeiro para aproveitar cache
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copia o código do app
COPY app.py /app/app.py
COPY processors /app/processors

# Porta que o Azure expõe (informativa)
EXPOSE 8000

# IMPORTANTE:
# Use bash -lc para expandir ${PORT} em tempo de execução.
# Se PORT não vier do ambiente, usa 8000.
CMD ["bash","-lc","streamlit run /app/app.py --server.port ${PORT:-8000} --server.address 0.0.0.0"]
