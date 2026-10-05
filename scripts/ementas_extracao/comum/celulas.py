"""Conversão e posicionamento de células de tabelas."""
import re
from decimal import Decimal
from ementas_extracao.comum.documento import normalizar

def texto_unico(texto):
    return re.sub(r'\s+', ' ', texto or '').strip()


def chave(texto):
    return re.sub(r'[^a-z0-9]', '', normalizar(texto or ''))


def numero(texto):
    texto = texto_unico(texto).replace(',', '.')
    m = re.fullmatch(r'(\d+(?:\.\d+)?)\s*(?:h|horas?)?', texto, re.I)
    if not m:
        return None
    valor = Decimal(m.group(1))
    return int(valor) if valor == valor.to_integral_value() else float(valor)


def celulas(tabela):
    """Células reais, removendo os placeholders das células mescladas."""
    return [[{'texto': texto_unico(t), 'bbox': list(c)}
             for c, t in zip(linha.cells, textos) if c is not None]
            for linha, textos in zip(tabela.rows, tabela.extract())]


def abaixo(coluna, linha):
    centro = (coluna['bbox'][0] + coluna['bbox'][2]) / 2
    candidatos = [c for c in linha if c['bbox'][0] <= centro <= c['bbox'][2]]
    return candidatos[0] if len(candidatos) == 1 else None


def evidencia(pagina, celula, rotulo=None):
    d = {'pagina': pagina, 'bbox': celula['bbox'], 'texto': celula['texto']}
    if rotulo:
        d['cabecalho'] = rotulo['texto']
        d['bbox_cabecalho'] = rotulo['bbox']
    return d


