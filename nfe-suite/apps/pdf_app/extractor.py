import os
from typing import List, Tuple, Set

from pdf2image import convert_from_path
from pyzbar.pyzbar import decode

def extrair_chaves_de_pdf(caminho_pdf: str, dpi: int = 300, poppler_path: str | None = None) -> Tuple[List[str], List[str]]:
    """
    Lê todas as páginas de um PDF, decodifica códigos de barras/QR e retorna:
      - lista de chaves de 44 dígitos (sem duplicatas, ordenadas)
      - outras leituras (que não têm 44 dígitos), para conferência
    """
    imagens = convert_from_path(caminho_pdf, dpi=dpi, poppler_path=poppler_path)

    chaves: Set[str] = set()
    outras: Set[str] = set()

    for img in imagens:
        if img.mode != "RGB":
            img = img.convert("RGB")
        for code in decode(img):
            texto = (code.data or b"").decode("utf-8", errors="ignore").strip()
            if texto.isdigit() and len(texto) == 44:
                chaves.add(texto)
            elif texto:
                outras.add(texto)

    return sorted(chaves), sorted(outras)

