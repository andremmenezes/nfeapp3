# Base slim com Python 3.10
FROM python:3.10-slim

# Evita prompts e melhora log
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instala dependências de sistema necessárias pelos seus pacotes
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    zbar-tools \
    libzbar0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Cria diretório de app
WORKDIR /app

# Copia requirements primeiro (para cache de layer)
COPY requirements.txt /app/requirements.txt

# Instala deps Python
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia o resto do código
COPY . /app

# App Service injeta $PORT; garanta que ouvimos nele
ENV PORT=8000

# Expose é só informativo pro Docker; o App Service usa $PORT
EXPOSE 8000

# Comando de inicialização
# (use o caminho real do seu app)
CMD ["streamlit", "run", "nfe-suite/apps/combo_app/app.py", "--server.port", "8000", "--server.address", "0.0.0.0"]
