FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["bash", "-lc", "streamlit run nfe-suite/apps/combo_app/app.py --server.port $PORT --server.address 0.0.0.0"]
