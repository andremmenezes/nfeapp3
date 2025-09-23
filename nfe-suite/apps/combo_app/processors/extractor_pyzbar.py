# nfe-suite/apps/combo_app/processors/extractor_pyzbar.py
# Extrai chaves 44 dígitos lendo o código de barras do DANFE com PYZBAR.
# Converte PDF -> imagens (uma por página) usando pdf2image (Poppler).
# Requisitos de runtime (no container): poppler-utils, libzbar0.

from __future__ import annotations
from typing import Tuple, List
import re
from pdf2image import convert_from_path
from pyzbar.pyzbar import decode
from PIL import Image

_ONLY_DIGITS = re.compile(r"\D+")

def _only_digits(s: str) -> str:
    return _ONLY_DIGITS.sub("", s or "")

def extrair_chaves_de_pdf(pdf_path: str, dpi: int = 300) -> Tuple[List[str], List[str]]:
    """
    Retorna (chaves_44, outras_leituras).
    - chaves_44: lista de chaves com 44 dígitos deduplicadas.
    - outras_leituras: strings lidas dos códigos (para auditoria).
    """
    pages = convert_from_path(pdf_path, dpi=dpi)  # requer poppler
    chaves: list[str] = []
    outras: list[str] = []

    for img in pages:
        if not isinstance(img, Image.Image):
            img = Image.fromarray(img)
        # melhora leitura: B/W
        img = img.convert("L")
        decoded = decode(img)  # pyzbar usa libzbar
        for d in decoded:
            val_raw = (d.data or b"").decode(errors="ignore")
            if not val_raw:
                continue
            outras.append(val_raw)
            dig = _only_digits(val_raw)
            if len(dig) == 44:
                chaves.append(dig)

    # dedup preservando ordem
    seen = set()
    chaves = [c for c in chaves if c not in seen and not seen.add(c)]
    return chaves, outras

