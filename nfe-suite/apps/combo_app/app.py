# nfe-suite/apps/combo_app/app.py
# App Streamlit com abas (XML, PDF, ZIP/Lote).
# Aba XML: gera o MESMO Excel do xml_app (colunas e formatação).
# Aba PDF: extrai chaves de NF-e dos PDFs usando o extractor do pdf_app e
#         disponibiliza Excel/CSV como no app dedicado — mas sem bug de to_excel (usa BytesIO).

import io
import os
import sys
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
from io import BytesIO
import xml.etree.ElementTree as ET

import pandas as pd
import streamlit as st
from openpyxl import load_workbook

# =========================
# Config da página
# =========================
st.set_page_config(page_title="NFe Suite", layout="wide")
st.title("NFe Suite – Upload e Processamento")

# =========================
# Imports do extractor (pdf_app)
# =========================
# Estrutura esperada do repo:
# nfe-suite/
#   apps/
#     combo_app/   (ESTE arquivo)
#     pdf_app/
#       extractor.py  (contém extrair_chaves_de_pdf)
HERE = Path(__file__).resolve()
PDF_APP_DIR = (HERE.parent.parent / "pdf_app").resolve()  # .../apps/pdf_app
if str(PDF_APP_DIR) not in sys.path:
    sys.path.insert(0, str(PDF_APP_DIR))

try:
    # noqa: E402
    from extractor import extrair_chaves_de_pdf  # type: ignore
except Exception as e:
    extrair_chaves_de_pdf = None  # será verificado ao usar a aba PDF
    _extractor_import_error = e

# =========================
# Helpers gerais de arquivos
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
# Helpers de Excel (XML/PDF)
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
# === Funções do xml_app (mantém o MESMO Excel do seu app) ===
# =========================
def get_text_or_zero(elem):
    return elem.text if elem is not None and elem.text else "0"

def extract_info_from_xml(file, result_list):
    tree = ET.parse(file)
    root = tree.getroot()
    ns = {"ns": "http://www.portalfiscal.inf.br/nfe"}

    nfe = root.find("./ns:NFe/ns:infNFe/ns:ide/ns:nNF", ns)
    serie = root.find("./ns:NFe/ns:infNFe/ns:ide/ns:serie", ns)
    nat_operacao = root.find("./ns:NFe/ns:infNFe/ns:ide/ns:natOp", ns)

    data_saida_entrada = root.find("./ns:NFe/ns:infNFe/ns:ide/ns:dhSaiEnt", ns)
    if data_saida_entrada is not None and data_saida_entrada.text:
        data_saida_entrada = f"{data_saida_entrada.text[8:10]}/{data_saida_entrada.text[5:7]}/{data_saida_entrada.text[0:4]}"
    else:
        data_saida_entrada = ""

    data_emissao = root.find("./ns:NFe/ns:infNFe/ns:ide/ns:dhEmi", ns)
    if data_emissao is not None and data_emissao.text:
        data_emissao = f"{data_emissao.text[8:10]}/{data_emissao.text[5:7]}/{data_emissao.text[0:4]}"
    else:
        data_emissao = ""

    valor_frete = root.find("./ns:NFe/ns:infNFe/ns:total/ns:ICMSTot/ns:vFrete", ns)
    valor_desc = root.find("./ns:NFe/ns:infNFe/ns:total/ns:ICMSTot/ns:vDesc", ns)
    valor_outro = root.find("./ns:NFe/ns:infNFe/ns:total/ns:ICMSTot/ns:vOutro", ns)
    valor_tot_nota = root.find("./ns:NFe/ns:infNFe/ns:total/ns:ICMSTot/ns:vNF", ns)
    valor_tot_prod = root.find("./ns:NFe/ns:infNFe/ns:total/ns:ICMSTot/ns:vProd", ns)

    chave = root.find("./ns:protNFe/ns:infProt/ns:chNFe", ns)
    cnpj_emitente = root.find("./ns:NFe/ns:infNFe/ns:emit/ns:CNPJ", ns)
    nome_emitente = root.find("./ns:NFe/ns:infNFe/ns:emit/ns:xNome", ns)

    item_num = 1
    for item in root.findall("./ns:NFe/ns:infNFe/ns:det", ns):
        cod = item.find(".ns:prod/ns:cProd", ns)
        descricao = item.find(".ns:prod/ns:xProd", ns)
        unidade = item.find(".ns:prod/ns:uCom", ns)
        quantidade = item.find(".ns:prod/ns:qCom", ns)
        valor_unit = item.find(".ns:prod/ns:vUnCom", ns)
        desconto_item = item.find(".ns:prod/ns:vDesc", ns)
        desconto_item = desconto_item.text if desconto_item is not None and desconto_item.text else ""
        valor_total_item = item.find(".ns:prod/ns:vProd", ns)
        icms_percent = item.find(".ns:imposto/ns:ICMS/ns:ICMS00/ns:pICMS", ns)
        icms_valor = item.find(".ns:imposto/ns:ICMS/ns:ICMS00/ns:vICMS", ns)
        ipi_percent = item.find(".ns:imposto/ns:IPI/ns:IPITrib/ns:pIPI", ns)
        ipi_valor = item.find(".ns:imposto/ns:IPI/ns:IPITrib/ns:vIPI", ns)

        linha = [
            nfe.text, serie.text, nat_operacao.text, data_emissao, data_saida_entrada,
            valor_frete.text, chave.text, cnpj_emitente.text, nome_emitente.text,
            valor_tot_nota.text, valor_tot_prod.text, valor_desc.text, valor_outro.text,
            item_num, cod.text, descricao.text, unidade.text, quantidade.text,
            valor_unit.text, desconto_item, valor_total_item.text,
            get_text_or_zero(icms_percent), get_text_or_zero(icms_valor),
            get_text_or_zero(ipi_percent), get_text_or_zero(ipi_valor),
        ]
        result_list.append([str(i) for i in linha])
        item_num += 1

def format_excel(df: pd.DataFrame) -> BytesIO:
    output = BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)
    wb = load_workbook(output)
    ws = wb.active

    formatos_colunas = {
        "Valor do Frete": "R$ #,##0.00",
        "Valor Total da Nota": "R$ #,##0.00",
        "Valor Total dos Produtos": "R$ #,##0.00",
        "Descontos Aplicados": "R$ #,##0.00",
        "Outras Despesas Acessórias": "R$ #,##0.00",
        "Valor Unitário": "R$ #,##0.00",
        "Desconto": "R$ #,##0.00",
        "Valor Total do Item": "R$ #,##0.00",
        "ICMS (valor)": "R$ #,##0.00",
        "IPI (valor)": "R$ #,##0.00",
        "Data de emissão": "DD/MM/YYYY",
        "Data de Saída/Entrada": "DD/MM/YYYY",
        "ICMS(%)": "0.00%",
        "IPI(%)": "0.00%",
        "Quantidade": "0.00",
        "NFe": "@",
        "Série": "@",
        "Chave": "@",
        "CNPJ do Emitente": "@",
        "Cód. Produto": "@",
    }

    cabecalho = {cell.value.strip(): idx + 1 for idx, cell in enumerate(ws[1]) if cell.value}

    for nome_coluna, formato in formatos_colunas.items():
        if nome_coluna in cabecalho:
            col_idx = cabecalho[nome_coluna]
            for row in ws.iter_rows(min_row=2, min_col=col_idx, max_col=col_idx):
                cell = row[0]
                try:
                    valor = str(cell.value or "").replace("R$", "").replace("%", "").replace(",", ".").strip()
                    if valor == "":
                        continue
                    if formato == "0":
                        cell.value = int(float(valor))
                    elif formato.endswith("%"):
                        cell.value = float(valor) / 100
                    elif formato == "@":
                        cell.value = str(cell.value).strip()
                    else:
                        cell.value = float(valor)
                    cell.number_format = formato
                    if nome_coluna == "CNPJ do Emitente":
                        cnpj = "".join(filter(str.isdigit, str(cell.value)))
                        if len(cnpj) == 14:
                            cell.value = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
                except:
                    pass

    final_output = BytesIO()
    wb.save(final_output)
    final_output.seek(0)
    return final_output

# =========================
# Pipelines para PDF (usa extractor do pdf_app)
# =========================
def processar_pdfs(paths: list[Path], dpi: int = 300, poppler_path: str | None = None):
    """
    Para cada PDF, extrai chaves com o extractor do pdf_app.
    Retorna:
      df_resumo: por arquivo (qtd_chaves_44, lista, outras leituras)
      df_chaves: uma linha por chave (deduplicado)
    """
    if extrair_chaves_de_pdf is None:
        raise RuntimeError(
            f"Extractor não disponível. Erro de import: {_extractor_import_error!r}\n"
            "Verifique se nfe-suite/apps/pdf_app/extractor.py existe e dependências (pdf2image, pillow, pyzbar/poppler) estão instaladas."
        )

    linhas = []
    resumo = []
    for p in sorted(paths, key=lambda x: x.name.lower()):
        try:
            chaves, outras = extrair_chaves_de_pdf(str(p), dpi=dpi, poppler_path=poppler_path)
            chaves = sorted(set(chaves))  # dedup e ordena
            for c in chaves:
                linhas.append({"arquivo": p.name, "chave_44": c})
            resumo.append({
                "arquivo": p.name,
                "qtd_chaves_44": len(chaves),
                "chaves_44": ", ".join(chaves) if chaves else "",
                "outras_leituras": ", ".join(outras) if outras else ""
            })
        except Exception as e:
            resumo.append({
                "arquivo": p.name,
                "qtd_chaves_44": 0,
                "chaves_44": "",
                "outras_leituras": f"ERRO: {e}"
            })

    df_chaves = pd.DataFrame(linhas).drop_duplicates().reset_index(drop=True)
    df_resumo = pd.DataFrame(resumo).sort_values("arquivo").reset_index(drop=True)
    return df_resumo, df_chaves

def excel_resumo_chaves(df_resumo: pd.DataFrame, df_chaves: pd.DataFrame) -> bytes:
    """Gera um .xlsx com 2 abas: Resumo_PDF e Chaves_PDF (em memória)."""
    return df_to_excel_bytes({"Resumo_PDF": df_resumo, "Chaves_PDF": df_chaves})

# =========================
# Pasta temporária por sessão
# =========================
session_tmp = Path(tempfile.gettempdir()) / f"nfe_suite_{os.getpid()}"
session_tmp.mkdir(parents=True, exist_ok=True)

# =========================
# Abas
# =========================
tab_xml, tab_pdf, tab_zip = st.tabs(["XML (múltiplos)", "PDF (múltiplos)", "ZIP/Lote"])

# --------- Aba: XML (usa MESMO Excel do xml_app) ----------
with tab_xml:
    st.subheader("Enviar XMLs")
    xml_files = st.file_uploader(
        "Selecione um ou mais arquivos .xml",
        type=["xml"],
        accept_multiple_files=True,
        help="Arraste e solte vários arquivos."
    )

    if st.button("Processar XMLs", disabled=not xml_files):
        dest = session_tmp / "xml_uploads"
        paths = save_uploaded_files(xml_files, dest)
        st.success(f"{len(paths)} XML(s) recebidos.")

        colunas = [
            "NFe", "Série", "Natureza da Operação", "Data de emissão", "Data de Saída/Entrada",
            "Valor do Frete", "Chave", "CNPJ do Emitente", "Nome do Emitente",
            "Valor Total da Nota", "Valor Total dos Produtos", "Descontos Aplicados",
            "Outras Despesas Acessórias", "Nº Item na Nota", "Cód. Produto", "Descrição",
            "Unidade de Medida", "Quantidade", "Valor Unitário", "Desconto", "Valor Total do Item",
            "ICMS(%)", "ICMS (valor)", "IPI(%)", "IPI (valor)",
        ]
        notas: list[list[str]] = []
        for p in paths:
            extract_info_from_xml(p, notas)
        df_xml = pd.DataFrame(columns=colunas, data=notas)

        excel_bytes = format_excel(df_xml)  # BytesIO
        st.success("✅ Processamento concluído!")
        st.download_button(
            label="📥 Baixar Excel (XMLs)",
            data=excel_bytes.getvalue(),
            file_name=f"NotasFiscais-{datetime.now().strftime('%Y%m%d-%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.dataframe(df_xml.head(50), use_container_width=True)

# --------- Aba: PDF (usa extractor do pdf_app) ----------
with tab_pdf:
    st.subheader("Enviar PDFs")
    with st.expander("Configurações (opcional)"):
        dpi = st.number_input("DPI para conversão (pdf2image)", min_value=100, max_value=600, value=300, step=50)
        poppler_path = st.text_input("poppler_path (somente Windows/local se precisar)", value="")
        poppler_path = poppler_path or None

    pdf_files = st.file_uploader(
        "Selecione um ou mais PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="O app lê TODAS as páginas e encontra TODAS as chaves de 44 dígitos (remove duplicatas)."
    )

    if st.button("Processar PDFs", disabled=not pdf_files):
        if extrair_chaves_de_pdf is None:
            st.error("Extractor não encontrado. Verifique dependências e o arquivo apps/pdf_app/extractor.py.")
        else:
            dest = session_tmp / "pdf_uploads"
            paths = save_uploaded_files(pdf_files, dest)
            st.success(f"{len(paths)} PDF(s) recebidos.")

            df_resumo, df_chaves = processar_pdfs(paths, dpi=int(dpi), poppler_path=poppler_path)

            st.subheader("Resumo por arquivo")
            st.dataframe(df_resumo, use_container_width=True)

            st.subheader("Linhas por chave (deduplicadas)")
            st.dataframe(df_chaves, use_container_width=True)

            # Excel com duas abas (Resumo_PDF e Chaves_PDF)
            xlsx_bytes = excel_resumo_chaves(df_resumo, df_chaves)
            st.download_button(
                "📥 Baixar Excel (PDFs)",
                data=xlsx_bytes,
                file_name=excel_filename("pdfs"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            # CSV opcional das chaves
            st.download_button(
                "Baixar chaves (CSV)",
                data=df_chaves.to_csv(index=False).encode("utf-8"),
                file_name="chaves_por_linha.csv",
                mime="text/csv",
                use_container_width=True
            )

# --------- Aba: ZIP/Lote (processa XMLs e PDFs juntos) ----------
with tab_zip:
    st.subheader("Enviar ZIP com lote (XMLs e/ou PDFs)")
    with st.expander("Configurações de PDF (opcional)"):
        dpi_zip = st.number_input("DPI (ZIP)", min_value=100, max_value=600, value=300, step=50, key="dpi_zip")
        poppler_path_zip = st.text_input("poppler_path (ZIP)", value="", key="poppler_zip") or None

    zip_file = st.file_uploader("Selecione um .zip", type=["zip"])
    if st.button("Processar ZIP", disabled=not zip_file):
        dest = session_tmp / "zip_extract"
        paths = extract_zip_to(zip_file.getvalue(), dest)
        st.success(f"{len(paths)} arquivo(s) extraído(s).")

        xmls = [p for p in paths if p.suffix.lower() == ".xml"]
        pdfs = [p for p in paths if p.suffix.lower() == ".pdf"]

        sheets: dict[str, pd.DataFrame] = {}

        # XMLs do lote -> MESMO Excel do xml_app
        if xmls:
            colunas = [
                "NFe", "Série", "Natureza da Operação", "Data de emissão", "Data de Saída/Entrada",
                "Valor do Frete", "Chave", "CNPJ do Emitente", "Nome do Emitente",
                "Valor Total da Nota", "Valor Total dos Produtos", "Descontos Aplicados",
                "Outras Despesas Acessórias", "Nº Item na Nota", "Cód. Produto", "Descrição",
                "Unidade de Medida", "Quantidade", "Valor Unitário", "Desconto", "Valor Total do Item",
                "ICMS(%)", "ICMS (valor)", "IPI(%)", "IPI (valor)",
            ]
            notas_zip: list[list[str]] = []
            for p in xmls:
                extract_info_from_xml(p, notas_zip)
            df_xml_zip = pd.DataFrame(columns=colunas, data=notas_zip)
            sheets["XMLs"] = df_xml_zip
            st.write("Prévia XMLs do ZIP")
            st.dataframe(df_xml_zip.head(50), use_container_width=True)

        # PDFs do lote
        if pdfs:
            if extrair_chaves_de_pdf is None:
                st.warning("Extractor não disponível — PDFs do ZIP não serão processados.")
            else:
                df_resumo_zip, df_chaves_zip = processar_pdfs(pdfs, dpi=int(dpi_zip), poppler_path=poppler_path_zip)
                sheets["Resumo_PDF"] = df_resumo_zip
                sheets["Chaves_PDF"] = df_chaves_zip
                st.write("Prévia PDFs do ZIP")
                st.dataframe(df_resumo_zip.head(50), use_container_width=True)

        if sheets:
            xlsx_bytes = df_to_excel_bytes(sheets)
            st.download_button(
                label="📥 Baixar Excel consolidado (ZIP/Lote)",
                data=xlsx_bytes,
                file_name=excel_filename("lote"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.info("Nenhum XML/PDF válido encontrado no ZIP.")

