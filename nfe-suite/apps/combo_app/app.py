import streamlit as st

st.set_page_config(page_title="NFe Suite – XML & PDF", layout="wide")
st.title("NFe Suite – XML & PDF")

tab_xml, tab_pdf = st.tabs(["Processar XML (lote ➜ Excel)", "Extrair chaves de PDFs"])

with tab_xml:
    st.markdown("### Seu fluxo atual de XML aqui")
    st.info("Cole aqui a UI do seu xml_app (ou importe as funções).")

with tab_pdf:
    st.markdown("### Extração de chaves a partir de PDFs")
    st.info("Reaproveite a lógica do pdf_app (importando o módulo extractor).")
