"""Leitura e triagem. Limites operacionais não substituem isolamento do processo."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import hashlib
import re
import unicodedata
import pdfplumber
from pypdf import PdfReader


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize('NFKD', texto)
    return re.sub(r'\s+', ' ', ''.join(c for c in texto if not unicodedata.combining(c))).lower().strip()


@dataclass(frozen=True)
class Limites:
    max_mb: int = 100
    max_paginas: int = 400


class DocumentoRecusado(ValueError):
    def __init__(self, codigo: str, mensagem: str):
        super().__init__(mensagem)
        self.codigo = codigo


def inspecionar(caminho: Path, limites: Limites) -> dict:
    if caminho.stat().st_size > limites.max_mb * 1024 * 1024:
        raise DocumentoRecusado('limite_excedido', 'Arquivo excede o limite de tamanho.')
    with caminho.open('rb') as stream:
        cabecalho = stream.read(1024)
    if b'%PDF-' not in cabecalho:
        raise DocumentoRecusado('arquivo_invalido', 'Conteúdo não apresenta cabeçalho PDF.')
    try:
        leitor = PdfReader(caminho)
        if leitor.is_encrypted:
            raise DocumentoRecusado('pdf_protegido', 'Fornecer uma cópia autorizada sem senha.')
        paginas = len(leitor.pages)
        if not paginas:
            raise DocumentoRecusado('arquivo_invalido', 'PDF sem páginas.')
        if paginas > limites.max_paginas:
            raise DocumentoRecusado('limite_excedido', 'Arquivo excede o limite de páginas.')
    except DocumentoRecusado:
        raise
    except Exception as erro:
        raise DocumentoRecusado('arquivo_invalido', 'Não foi possível interpretar a estrutura PDF.') from erro
    with caminho.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'arquivo': caminho.name, 'sha256': digest, 'total_paginas': paginas}


def ler_linhas(caminho: Path) -> tuple[list[dict], list[dict]]:
    linhas, paginas = [], []
    with pdfplumber.open(caminho) as pdf:
        for numero, pagina in enumerate(pdf.pages, 1):
            filtrada = pagina.filter(lambda obj: obj.get('object_type') != 'char' or obj.get('upright', True))
            atuais = filtrada.extract_text_lines(y_tolerance=5, return_chars=False)
            for linha in atuais:
                texto = linha['text'].strip()
                if texto:
                    linhas.append({'texto': texto, 'pagina': numero,
                        'bbox': [round(linha[k], 2) for k in ('x0', 'top', 'x1', 'bottom')],
                        'altura_pagina': pagina.height})
            paginas.append({'pagina': numero, 'linhas': len(atuais),
                            'caracteres': sum(len(l['text']) for l in atuais)})
            pagina.close()
    repeticoes = Counter(t for t, p in {(normalizar(l['texto']), l['pagina']) for l in linhas
                       if l['bbox'][1] < 80 or l['bbox'][3] > l['altura_pagina'] - 60})
    for i, linha in enumerate(linhas):
        linha['indice'] = i
        texto = normalizar(linha['texto'])
        linha['margem_repetida'] = (repeticoes[texto] >= 3
            and (linha['bbox'][1] < 80 or linha['bbox'][3] > linha['altura_pagina'] - 60)
            and not re.search(r'ementa|disciplina|curso|objetiv|bibliograf|referencia|conteudo|competenc|habilidade|universidade|faculdade|institui', texto))
    return linhas, paginas


def fonte(linha: dict) -> dict:
    return {'pagina': linha['pagina'], 'bbox': linha['bbox'], 'texto': linha['texto']}
