import os
import io
import zipfile
import tempfile
import pandas as pd
import streamlit as st

from extractor import processar_pasta_pdfs

st.set_page_config(page_title="NFe – Chaves a partir de PDFs", layout="wide")

st.title("Extração de chaves de acesso (PDF ➜ CSV/Excel)")
st.write("Envie um .zip com seus PDFs ou use uma pasta local (modo dev).")

with st.expander("Configurações avançadas"):
    poppler_path = st.text_input("poppler_path (opcional — deixe vazio em Linux com poppler-utils)", value="")
    poppler_path = poppler_path or None

tab1, tab2 = st.tabs(["Enviar ZIP", "Modo Dev (pasta local)"])

df_chaves = None
df_resumo = None

with tab1:
    zip_file = st.file_uploader("Selecione um arquivo .zip com PDFs", type=["zip"])
    if zip_file is not None:
        with tempfile.TemporaryDirectory() as td:
            zf = zipfile.ZipFile(io.BytesIO(zip_file.read()))
            zf.extractall(td)
            df_chaves, df_resumo = processar_pasta_pdfs(td, poppler_path=poppler_path)

with tab2:
    pasta_local = st.text_input("Caminho de uma pasta local com PDFs (somente em dev/local)")
    if st.button("Processar pasta local"):
        if pasta_local and os.path.isdir(pasta_local):
            df_chaves, df_resumo = processar_pasta_pdfs(pasta_local, poppler_path=poppler_path)
        else:
            st.error("Pasta inválida.")

if df_resumo is not None:
    st.subheader("Resumo por arquivo (quantas chaves por PDF)")
    st.dataframe(df_resumo, use_container_width=True)

    st.subheader("Linhas por chave (deduplicadas)")
    st.dataframe(df_chaves, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Baixar resumo (Excel)",
            data=df_resumo.to_excel(index=False, engine="xlsxwriter"),
            file_name="resumo_por_arquivo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with col2:
        st.download_button(
            "Baixar chaves (CSV)",
            data=df_chaves.to_csv(index=False).encode("utf-8"),
            file_name="chaves_por_linha.csv",
            mime="text/csv",
        )
