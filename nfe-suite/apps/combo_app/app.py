import io
import os
import zipfile
import tempfile
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="NFe Suite", layout="wide")

# ===== Helpers =====
def save_uploaded_files(files, dest_dir: Path) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for f in files:
        p = dest_dir / f.name
        with open(p, "wb") as out:
            out.write(f.getbuffer())
        saved.append(p)
    return saved

def extract_zip_to(zip_bytes: bytes, dest_dir: Path) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for member in zf.infolist():
            # ignora diretórios
            if member.is_dir():
                continue
            # normaliza caminho (evita path traversal)
            target = dest_dir / Path(member.filename).name
            with zf.open(member, "r") as src, open(target, "wb") as dst:
                dst.write(src.read())
            saved.append(target)
    return saved

# ===== UI =====
st.title("NFe Suite – Upload e Processamento")
tab_xml, tab_pdf, tab_zip = st.tabs(["XML (múltiplos)", "PDF (múltiplos)", "ZIP/Lote"])

# Pasta temporária por sessão
session_tmp = Path(tempfile.gettempdir()) / f"nfe_suite_{st.session_state.get('_session_id', os.getpid())}"
session_tmp.mkdir(parents=True, exist_ok=True)

with tab_xml:
    st.subheader("Enviar XMLs")
    xml_files = st.file_uploader(
        "Selecione um ou mais arquivos .xml",
        type=["xml"],
        accept_multiple_files=True,
        help="Você pode arrastar vários de uma vez."
    )
    if st.button("Processar XMLs", disabled=not xml_files):
        dest = session_tmp / "xml_uploads"
        paths = save_uploaded_files(xml_files, dest)
        st.success(f"{len(paths)} XML(s) recebidos.")
        # TODO: plugue aqui sua função que processa os XMLs e gera Excel
        # ex: df = processar_xmls(paths); st.dataframe(df)

with tab_pdf:
    st.subheader("Enviar PDFs")
    pdf_files = st.file_uploader(
        "Selecione um ou mais PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="Arraste vários se preferir."
    )
    if st.button("Processar PDFs", disabled=not pdf_files):
        dest = session_tmp / "pdf_uploads"
        paths = save_uploaded_files(pdf_files, dest)
        st.success(f"{len(paths)} PDF(s) recebidos.")
        # TODO: plugue aqui sua função de leitura (ex.: extrair chaves)
        # ex: df = processar_pdfs(paths); st.dataframe(df)

with tab_zip:
    st.subheader("Enviar ZIP com lote (XMLs e/ou PDFs)")
    zip_file = st.file_uploader(
        "Selecione um .zip contendo os arquivos",
        type=["zip"],
        help="Dentro do ZIP coloque os arquivos diretamente (sem pastas profundas)."
    )
    if st.button("Processar ZIP", disabled=not zip_file):
        dest = session_tmp / "zip_extract"
        paths = extract_zip_to(zip_file.getvalue(), dest)
        st.success(f"{len(paths)} arquivo(s) extraído(s) para {dest}")
        # Aqui você pode filtrar por tipo e chamar seus pipelines:
        xmls = [p for p in paths if p.suffix.lower() == ".xml"]
        pdfs = [p for p in paths if p.suffix.lower() == ".pdf"]
        st.write(f"XMLs: {len(xmls)} | PDFs: {len(pdfs)}")
        # TODO: processar xmls/pdfs conforme suas funções
        # ex: df_xml = processar_xmls(xmls); df_pdf = processar_pdfs(pdfs)
