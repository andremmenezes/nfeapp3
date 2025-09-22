import os
from dataclasses import dataclass
from typing import List, Tuple, Dict, Set

import pandas as pd
from pdf2image import convert_from_path
from pyzbar.pyzbar import decode
from PIL import Image

@dataclass
class PDFExtractionResult:
    arquivo: str
    chaves_44: List[str]
    outras_leituras: List[str]

def extrair_chaves_de_pdf(
    caminho_pdf: str,
    dpi: int = 300,
    poppler_path: str | None = None
) -> PDFExtractionResult:
    imagens = convert_from_path(caminho_pdf, dpi=dpi, poppler_path=poppler_path)

    chaves: Set[str] = set()
    outras: Set[str] = set()

    for img in imagens:
        if img.mode != "RGB":
            img = img.convert("RGB")

        for code in decode(img):
            texto = code.data.decode("utf-8", errors="ignore").strip()
            if texto.isdigit() and len(texto) == 44:
                chaves.add(texto)
            else:
                if texto:
                    outras.add(texto)

    return PDFExtractionResult(
        arquivo=os.path.basename(caminho_pdf),
        chaves_44=sorted(chaves),
        outras_leituras=sorted(outras),
    )

def processar_pasta_pdfs(
    pasta: str,
    poppler_path: str | None = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    linhas_chaves = []
    linhas_resumo = []

    for nome in os.listdir(pasta):
        if not nome.lower().endswith(".pdf"):
            continue

        caminho_pdf = os.path.join(pasta, nome)
        try:
            result = extrair_chaves_de_pdf(caminho_pdf, poppler_path=poppler_path)
            for chave in result.chaves_44:
                linhas_chaves.append({"arquivo": result.arquivo, "chave_44": chave})
            linhas_resumo.append({
                "arquivo": result.arquivo,
                "qtd_chaves_44": len(result.chaves_44),
                "chaves_44": ", ".join(result.chaves_44) if result.chaves_44 else "",
                "outras_leituras": ", ".join(result.outras_leituras) if result.outras_leituras else "",
            })
        except Exception as e:
            linhas_resumo.append({
                "arquivo": nome,
                "qtd_chaves_44": 0,
                "chaves_44": "",
                "outras_leituras": f"ERRO: {e}"
            })

    df_chaves = pd.DataFrame(linhas_chaves).drop_duplicates().reset_index(drop=True)
    df_resumo = pd.DataFrame(linhas_resumo).sort_values("arquivo").reset_index(drop=True)
    return df_chaves, df_resumo
