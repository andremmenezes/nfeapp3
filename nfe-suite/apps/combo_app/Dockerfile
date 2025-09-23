# Base oficial Python slim
FROM python:3.10-slim

# Instala dependências do sistema: poppler-utils (pdf2image) e libzbar (pyzbar)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils libzbar0 \
 && rm -rf /var/lib/apt/lists/*

# Cria diretório app
WORKDIR /app

# Copia requirements do combo_app e instala
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia todo o combo_app (incluindo processors/ e app.py)
COPY . /app

# Streamlit em porta 8000 (App Service)
ENV PORT=8000
EXPOSE 8000

# Desabilita telemetry do streamlit e usa raiz /app
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Comando de inicialização
CMD ["streamlit", "run", "app.py", "--server.port", "8000", "--server.address", "0.0.0.0"]
