"""Identificação complementar em capas: alias explícito, evidência e revisão.

Não identifica qualquer logotipo. OCR textual UNIPAC é um alias conhecido;
não deduz campus, CNPJ ou identidade cadastral. Não altera o PDF original.
"""
from pathlib import Path
import re
import pdfplumber
from .documento import normalizar
from .ocr import verificar, ambiente_tessdata

NOME_UNIPAC = 'Centro Universitário Presidente Antônio Carlos'


def reconhecer_alias(texto):
    return bool(re.search(r'\bunipac\b', normalizar(texto)))


def aplicar_evidencias(analise, evidencias):
    analise['identificacao_institucional'] = {'candidatos': evidencias,
        'regra': 'alias_unipac_v1', 'associacao': 'nao_aplicada'}
    registros = analise.get('ementas', [])
    # Escopo conservador: plano único, sem outro candidato de disciplina.
    if (len(registros) != 1 or analise.get('candidatos_inconclusivos') or
        registros[0].get('metodo_segmentacao') != 'perfil_plano_aprendizagem_unico' or not evidencias):
        return analise
    registro = registros[0]
    atual = registro['dados'].get('instituicao')
    if atual and normalizar(atual) not in {normalizar(NOME_UNIPAC), 'unipac'}:
        registro['avisos'].append('instituicao_divergente_do_alias_da_capa_conferir')
        return analise
    registro['dados']['instituicao'] = atual or NOME_UNIPAC
    registro.setdefault('evidencias', {})['instituicao'] = evidencias
    registro['avisos'].append('instituicao_normalizada_por_alias_unipac_conferir_campus')
    analise['identificacao_institucional']['associacao'] = 'perfil_plano_unico_revisao_obrigatoria'
    return analise


def identificar(origem: Path, analise, config):
    evidencias, verificacoes = [], []
    registros = analise.get("ementas", [])
    if (len(registros) != 1 or registros[0].get("metodo_segmentacao") != "perfil_plano_aprendizagem_unico"
        or registros[0]["dados"].get("instituicao")):
        return analise
    with pdfplumber.open(origem) as pdf:
        numeros = sorted({1, min(2, len(pdf.pages)), max(1, len(pdf.pages)-1), len(pdf.pages)})
        for numero in numeros:
            pagina = pdf.pages[numero-1]
            for linha in pagina.extract_text_lines(return_chars=False):
                if reconhecer_alias(linha['text']):
                    evidencias.append({'pagina':numero, 'texto':linha['text'],
                        'bbox':[linha[k] for k in ('x0','top','x1','bottom')],
                        'metodo':'texto_nativo', 'alias':'UNIPAC', 'nome_normalizado':NOME_UNIPAC})
            # Busca complementar mesmo quando há texto nativo suficiente.
            if not pagina.images or config.modo == 'nunca':
                continue
            verificacoes.append(numero)
            if len(verificacoes) > config.max_paginas_ocr:
                raise RuntimeError('Limite de páginas do OCR institucional excedido.')
            if pagina.width * pagina.height * (config.dpi/72)**2 > config.max_megapixels*1_000_000:
                raise RuntimeError('Página excede limite de pixels do OCR institucional.')
            import pypdfium2 as pdfium
            pytesseract, extra = verificar(config)
            with pdfium.PdfDocument(str(origem)) as doc:
                render = doc[numero-1]
                try:
                    bitmap = render.render(scale=config.dpi/72)
                    try: imagem = bitmap.to_pil().copy()
                    finally: bitmap.close()
                finally: render.close()
            try:
                with ambiente_tessdata(config):
                    dados = pytesseract.image_to_data(imagem, lang=config.idioma,
                        config=f'{extra} --psm 11', timeout=config.timeout,
                        output_type=pytesseract.Output.DICT)
                for i,texto in enumerate(dados['text']):
                    if reconhecer_alias(texto):
                        x,y,w,h = (dados[k][i] for k in ('left','top','width','height'))
                        sx,sy = pagina.width/imagem.width,pagina.height/imagem.height
                        evidencias.append({'pagina':numero,'texto':texto,
                            'bbox':[x*sx,y*sy,(x+w)*sx,(y+h)*sy],
                            'metodo':'ocr_complementar_psm11','confianca_ocr':float(dados['conf'][i]),
                            'alias':'UNIPAC','nome_normalizado':NOME_UNIPAC})
            finally: imagem.close()
    aplicar_evidencias(analise, evidencias)
    analise['identificacao_institucional']['paginas_ocr_complementar'] = verificacoes
    return analise
