import streamlit as st

st.set_page_config(page_title="NFe Suite – XML & PDF", layout="wide")
st.title("NFe Suite – XML & PDF")

tab_xml, tab_pdf = st.tabs(["Processar XML (lote ➜ Excel)", "Extrair chaves de PDFs"])

with tab_xml:
    st.write("Use hoje o app separado em `apps/xml_app`. Este tab é só um placeholder.")

with tab_pdf:
    st.write("Use hoje o app separado em `apps/pdf_app`. Este tab é só um placeholder.")
