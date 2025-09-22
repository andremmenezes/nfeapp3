import os
import io
import zipfile
import tempfile
import pandas as pd
import streamlit as st

from extractor import extrair_chaves_de_pdf

st.set_page_config(page_title="Chaves de NF-e (PDF)", layout="wide")
st.title("Extrair chaves de acesso de PDFs")

st.write("Envie um **.zip** com arquivos PDF. O app lê **todas as páginas** de cada PDF, "
         "identifica **todas as chaves de 44 dígitos**, remove **duplicatas** e mostra o resultado.")

with st.expander("Configurações (opcional)"):
    poppler_path = st.text_input("poppler_path (somente Windows/local se precisar)", value="")
    poppler_path = poppler_path or None
    dpi = st.number_input("DPI para conversão de página (pdf2image)", min_value=100, max_value=600, value=300, step=50)

zip_file = st.file_uploader("Selecione um arquivo .zip com PDFs", type=["zip"])

if zip_file is not None:
    with tempfile.TemporaryDirectory() as td:
        zf = zipfile.ZipFile(io.BytesIO(zip_file.read()))
        zf.extractall(td)

        linhas = []
        resumo = []

        for nome in sorted(os.listdir(td)):
            if not nome.lower().endswith(".pdf"):
                continue
            caminho_pdf = os.path.join(td, nome)
            try:
                chaves, outras = extrair_chaves_de_pdf(caminho_pdf, dpi=dpi, poppler_path=poppler_path)
                for c in chaves:
                    linhas.append({"arquivo": nome, "chave_44": c})
                resumo.append({
                    "arquivo": nome,
                    "qtd_chaves_44": len(chaves),
                    "chaves_44": ", ".join(chaves) if chaves else "",
                    "outras_leituras": ", ".join(outras) if outras else ""
                })
            except Exception as e:
                resumo.append({
                    "arquivo": nome,
                    "qtd_chaves_44": 0,
                    "chaves_44": "",
                    "outras_leituras": f"ERRO: {e}"
                })

        df_chaves = pd.DataFrame(linhas).drop_duplicates().reset_index(drop=True)
        df_resumo = pd.DataFrame(resumo).sort_values("arquivo").reset_index(drop=True)

        st.subheader("Resumo por arquivo")
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
else:
    st.info("Envie o ZIP com PDFs para começar.")

