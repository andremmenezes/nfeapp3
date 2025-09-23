# nfe-suite/apps/combo_app/app.py
# App Streamlit com abas (XML, PDF, ZIP/Lote) e exportação de Excel em memória.

import io
import os
import zipfile
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st

# =========================
# Configuração de página
# =========================
st.set_page_config(page_title="NFe Suite", layout="wide")

# =========================
# Helpers gerais de arquivo
# =========================
def save_uploaded_files(files, dest_dir: Path) -> list[Path]:
    """Grava arquivos enviados para uma pasta e retorna a lista de Paths."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for f in files:
        p = dest_dir / f.name
        with open(p, "wb") as out:
            out.write(f.getbuffer())
        saved.append(p)
    return saved

def extract_zip_to(zip_bytes: bytes, dest_dir: Path) -> list[Path]:
    """Extrai um ZIP (em bytes) para dest_dir e retorna os Paths extraídos (arquivos, sem diretórios)."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for member in zf.infolist():
            if member.is_dir():
                continue
            target = dest_dir / Path(member.filename).name  # normaliza nome
            with zf.open(member, "r") as src, open(target, "wb") as dst:
                dst.write(src.read())
            saved.append(target)
    return saved

# =========================
# Helpers de Excel (in-memory)
# =========================
def df_to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    """
    Recebe {'NomeDaAba': DataFrame} e devolve bytes de um .xlsx sem gravar em disco.
    """
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, df in sheets.items():
            safe_name = (name or "Planilha")[:31]
            (df if not df.empty else pd.DataFrame()).to_excel(
                writer, index=False, sheet_name=safe_name
            )
    buf.seek(0)
    return buf.getvalue()

def excel_filename(prefix: str = "resultado") -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.xlsx"

# =========================
# Pipelines simples (troque pelos seus se desejar)
# =========================
def processar_xmls(paths: list[Path]) -> pd.DataFrame:
    """
    Parser simples de XML de NF-e (exemplo).
    -> Troque/adapte por sua lógica existente quando quiser.
    """
    ns = {"ns": "http://www.portalfiscal.inf.br/nfe"}
    linhas: list[dict] = []

    for p in paths:
        try:
            root = ET.parse(p).getroot()
            ch = root.find("./ns:protNFe/ns:infProt/ns:chNFe", ns)
            emit = root.find("./ns:NFe/ns:infNFe/ns:emit/ns:xNome", ns)
            vnf = root.find("./ns:NFe/ns:infNFe/ns:total/ns:ICMSTot/ns:vNF", ns)

            linhas.append({
                "arquivo": p.name,
                "chave": ch.text if ch is not None else "",
                "emitente": emit.text if emit is not None else "",
                "valor_nota": vnf.text if vnf is not None else "",
            })
        except Exception as e:
            linhas.append({
                "arquivo": p.name,
                "chave": "",
                "emitente": "",
                "valor_nota": "",
                "erro": str(e),
            })

    df = pd.DataFrame(linhas)
    return df

def processar_pdfs_basico(paths: list[Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Placeholder de processamento de PDF (sem OCR/leitura de barras para evitar dependências nativas).
    Retorna:
      - df_resumo: um resumo por arquivo
      - df_chaves: tabela de chaves (aqui vazio, caso você não tenha extractor)
    Se você já tem um extractor (ex.: pdf_app/extractor.py), pluge aqui.
    """
    # Exemplo de resumo simples
    resumo = [{"arquivo": p.name, "status": "Recebido"} for p in paths]
    df_resumo = pd.DataFrame(resumo)
    df_chaves = pd.DataFrame(columns=["arquivo", "chave_44"])
    return df_resumo, df_chaves

# =========================
# Pasta temporária por sessão
# =========================
session_tmp = Path(tempfile.gettempdir()) / f"nfe_suite_{os.getpid()}"
session_tmp.mkdir(parents=True, exist_ok=True)

# =========================
# UI
# =========================
st.title("NFe Suite – Upload e Processamento")
tab_xml, tab_pdf, tab_zip = st.tabs(["XML (múltiplos)", "PDF (múltiplos)", "ZIP/Lote"])

# --------- Aba: XML (múltiplos) ----------
with tab_xml:
    st.subheader("Enviar XMLs")
    xml_files = st.file_uploader(
        "Selecione um ou mais arquivos .xml",
        type=["xml"],
        accept_multiple_files=True,
        help="Você pode arrastar e soltar vários arquivos."
    )

    if st.button("Processar XMLs", disabled=not xml_files):
        dest = session_tmp / "xml_uploads"
        paths = save_uploaded_files(xml_files, dest)
        st.success(f"{len(paths)} XML(s) recebidos.")

        df_xml = processar_xmls(paths)
        st.dataframe(df_xml, use_container_width=True)

        xlsx_bytes = df_to_excel_bytes({"XMLs": df_xml})
        st.download_button(
            label="Baixar Excel (XMLs)",
            data=xlsx_bytes,
            file_name=excel_filename("xmls"),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# --------- Aba: PDF (múltiplos) ----------
with tab_pdf:
    st.subheader("Enviar PDFs")
    pdf_files = st.file_uploader(
        "Selecione um ou mais PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="Se quiser leitura de chaves de barras, plugar extractor nesta aba."
    )

    if st.button("Processar PDFs", disabled=not pdf_files):
        dest = session_tmp / "pdf_uploads"
        paths = save_uploaded_files(pdf_files, dest)
        st.success(f"{len(paths)} PDF(s) recebidos.")

        # Se você tiver um extractor pronto, substitua a linha abaixo por ele
        df_resumo, df_chaves = processar_pdfs_basico(paths)

        st.dataframe(df_resumo, use_container_width=True)
        if not df_chaves.empty:
            st.dataframe(df_chaves, use_container_width=True)

        xlsx_bytes = df_to_excel_bytes({"Resumo_PDF": df_resumo, "Chaves_PDF": df_chaves})
        st.download_button(
            label="Baixar Excel (PDFs)",
            data=xlsx_bytes,
            file_name=excel_filename("pdfs"),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# --------- Aba: ZIP/Lote ----------
with tab_zip:
    st.subheader("Enviar ZIP com lote (XMLs e/ou PDFs)")
    zip_file = st.file_uploader(
        "Selecione um .zip",
        type=["zip"],
        help="Dentro do ZIP, coloque os arquivos diretamente (sem subpastas profundas)."
    )

    if st.button("Processar ZIP", disabled=not zip_file):
        dest = session_tmp / "zip_extract"
        paths = extract_zip_to(zip_file.getvalue(), dest)
        st.success(f"{len(paths)} arquivo(s) extraído(s).")

        xmls = [p for p in paths if p.suffix.lower() == ".xml"]
        pdfs = [p for p in paths if p.suffix.lower() == ".pdf"]

        sheets: dict[str, pd.DataFrame] = {}

        # XMLs do lote
        if xmls:
            df_xml = processar_xmls(xmls)
            sheets["XMLs"] = df_xml
            st.write("Prévia XMLs (ZIP/Lote)")
            st.dataframe(df_xml.head(30), use_container_width=True)

        # PDFs do lote

