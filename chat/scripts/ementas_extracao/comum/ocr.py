"""Normaliza apenas páginas selecionadas para um PDF intermediário em memória.

OCR fornece palavras; OpenCV detecta linhas rasterizadas. O PDF temporário
expressa ambos em coordenadas PDF para reutilizar o interpretador estrutural.
Não é uma cópia de preservação do documento: o original permanece intacto.
"""
from __future__ import annotations

import io
import shutil
import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import pdfplumber
from pypdf import PdfReader, PdfWriter


@dataclass(frozen=True)
class ConfigOCR:
    modo: str = "auto"
    idioma: str = "por"
    dpi: int = 300
    executavel: str | None = None
    tessdata: str | None = None
    timeout: int = 120
    paginas_forcadas: frozenset[int] = frozenset()
    max_paginas_ocr: int = 30
    max_megapixels: int = 40


def decidir(pagina, config: ConfigOCR, numero: int) -> tuple[bool, str]:
    if config.modo == "sempre" or numero in config.paginas_forcadas:
        return True, "OCR solicitado explicitamente"
    if config.modo == "nunca":
        return False, "Somente leitura digital solicitada"
    texto = pagina.extract_text() or ""
    area = pagina.width * pagina.height
    grande_imagem = any((min(pagina.width,i['x1'])-max(0,i['x0'])) *
                       (min(pagina.height,i['bottom'])-max(0,i['top'])) > area*.35
                       for i in pagina.images)
    # Texto distribuído pela página evita OCR provocado só por papel timbrado.
    # Cabeçalho isolado não satisfaz esses critérios. É uma heurística auditável.
    palavras=pagina.extract_words()
    linhas={round(w['top']/5) for w in palavras}
    amplitude=(max(w['bottom'] for w in palavras)-min(w['top'] for w in palavras)) if palavras else 0
    texto_distribuido=len(texto)>200 and len(linhas)>=12 and amplitude>pagina.height*.45
    # Imagem grande com texto insuficiente dispara OCR inclusive em página mista.
    if grande_imagem:
        if not texto_distribuido:
            return True, "Imagem grande e pouco texto distribuído; possível página mista"
    ruins = sum(c == '\ufffd' or (not c.isprintable() and not c.isspace()) for c in texto)
    if texto and ruins / len(texto) > .05:
        return True, "Texto digital contém caracteres inválidos"
    if not texto.strip():
        return True, "Página sem texto; OCR verificará se está vazia"
    return False, "Texto digital distribuído apesar de imagem grande; revisar se imagem contém conteúdo adicional" if grande_imagem else "Texto digital disponível, sem imagem grande detectada"


@contextmanager
def ambiente_tessdata(config: ConfigOCR):
    """Evita aspas literais em argumentos do pytesseract no Windows.

O CLI é sequencial. Um serviço concorrente deve usar processos separados.
"""
    if not config.tessdata:
        yield
        return
    pasta = Path(config.tessdata).expanduser().resolve()
    if not pasta.is_dir():
        raise RuntimeError(f'Diretório tessdata não encontrado: {pasta}')
    anterior = os.environ.get('TESSDATA_PREFIX')
    os.environ['TESSDATA_PREFIX'] = str(pasta)
    try:
        yield
    finally:
        if anterior is None:
            os.environ.pop('TESSDATA_PREFIX', None)
        else:
            os.environ['TESSDATA_PREFIX'] = anterior


def verificar(config: ConfigOCR):
    import pytesseract
    executavel = config.executavel or shutil.which("tesseract")
    if not executavel:
        raise RuntimeError("Tesseract não encontrado. Instale o programa ou informe --tesseract CAMINHO.")
    pytesseract.pytesseract.tesseract_cmd = str(executavel)
    extra = ''
    with ambiente_tessdata(config):
        instalados = set(pytesseract.get_languages(config=extra))
    faltantes = set(config.idioma.split("+")) - instalados
    if faltantes:
        raise RuntimeError(f"Idiomas OCR ausentes: {', '.join(sorted(faltantes))}. Instale os arquivos traineddata correspondentes.")
    return pytesseract, extra


def reconhecer(imagem, largura: float, altura: float, config: ConfigOCR):
    import cv2
    import numpy as np
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase.pdfmetrics import stringWidth

    pytesseract, extra = verificar(config)
    cinza = cv2.cvtColor(np.array(imagem.convert("RGB")),cv2.COLOR_RGB2GRAY)
    # Limiar local preserva texto em cabeçalhos coloridos. Otsu global pode
    # confundir uma faixa colorida inteira com linha e apagar seu título.
    mascara = cv2.adaptiveThreshold(cinza,255,cv2.ADAPTIVE_THRESH_MEAN_C,
                                    cv2.THRESH_BINARY_INV,35,10)
    horizontais = cv2.morphologyEx(mascara,cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT,(max(25,cinza.shape[1]//35),1)))
    verticais = cv2.morphologyEx(mascara,cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT,(1,max(25,cinza.shape[0]//45))))
    for mask,horizontal in ((horizontais,True),(verticais,False)):
        contornos,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        for contorno in contornos:
            x,y,w,h=cv2.boundingRect(contorno)
            if (h if horizontal else w) > config.dpi/25:
                cv2.drawContours(mask,[contorno],-1,0,cv2.FILLED)
    # Retira linhas da imagem submetida ao OCR, mas preserva sua geometria.
    limpa = 255-mascara
    limpa[cv2.bitwise_or(horizontais,verticais)>0]=255
    def ler_dados(imagem_ocr):
        with ambiente_tessdata(config):
            return pytesseract.image_to_data(imagem_ocr,lang=config.idioma,
                config=f"{extra} --psm 3",output_type=pytesseract.Output.DICT,timeout=config.timeout)
    dados_limpos = ler_dados(limpa)
    # Faixas coloridas com letras claras podem perder títulos na binarização.
    # Comparamos duas leituras da MESMA página por evidências estruturais, sem
    # tratar confiança do OCR como probabilidade de classificação documental.
    dados_originais = ler_dados(imagem)
    from ementas_extracao.comum.segmentacao import cabecalho
    from ementas_extracao.comum.documento import normalizar
    def pontuar(d):
        grupos_texto = {}
        for i, t in enumerate(d['text']):
            chave = tuple(d[k][i] for k in ('block_num', 'par_num', 'line_num'))
            grupos_texto.setdefault(chave, []).append(t)
        textos = [' '.join(v).strip() for v in grupos_texto.values()]
        secoes = sum(cabecalho(t) is not None for t in textos)
        metadados = sum(any(normalizar(t).startswith(k) for k in ('disciplina', 'curso', 'carga horaria')) for t in textos)
        return secoes, metadados
    pontuacoes = {'binarizada': pontuar(dados_limpos), 'original': pontuar(dados_originais)}
    variante = 'original' if pontuacoes['original'] > pontuacoes['binarizada'] else 'binarizada'
    dados = dados_originais if variante == 'original' else dados_limpos
    sx,sy=largura/imagem.width,altura/imagem.height
    palavras=[]
    grupos={}
    for i,texto in enumerate(dados['text']):
        if not texto.strip():continue
        chave=tuple(dados[k][i] for k in ('block_num','par_num','line_num'))
        grupos.setdefault(chave,[]).append((dados['top'][i],dados['top'][i]+dados['height'][i]))
    for i,texto in enumerate(dados['text']):
        if not texto.strip():continue
        x,y,w,h=(dados[k][i] for k in ('left','top','width','height'))
        chave=tuple(dados[k][i] for k in ('block_num','par_num','line_num'))
        linha_top=min(v[0] for v in grupos[chave]);linha_bottom=max(v[1] for v in grupos[chave])
        palavras.append({'texto':texto,'bbox':[x*sx,y*sy,(x+w)*sx,(y+h)*sy],
                         'linha_y':[linha_top*sy,linha_bottom*sy],
                         'confianca_ocr':float(dados['conf'][i])})
    memoria=io.BytesIO()
    pdf=canvas.Canvas(memoria,pagesize=(largura,altura))
    for palavra in palavras:
        x0,_,x1,_=palavra['bbox'];y0,y1=palavra['linha_y']; tamanho=max(1,(y1-y0)/.925)
        texto=pdf.beginText(x0,altura-y1+tamanho*.207)
        texto.setFont("Helvetica",tamanho)
        medida=stringWidth(palavra['texto'],"Helvetica",tamanho)
        texto.setHorizScale(100*(x1-x0)/max(.01,medida))
        texto.textOut(palavra['texto']);pdf.drawText(texto)
    linhas=[]
    for mask,horizontal in ((horizontais,True),(verticais,False)):
        contornos,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        for contorno in contornos:
            x,y,w,h=cv2.boundingRect(contorno)
            if horizontal:
                pontos=(x*sx,(y+h/2)*sy,(x+w)*sx,(y+h/2)*sy)
            else:pontos=((x+w/2)*sx,y*sy,(x+w/2)*sx,(y+h)*sy)
            linhas.append(pontos)
            a,b,c,d=pontos;pdf.line(a,altura-b,c,altura-d)
    pdf.showPage();pdf.save();memoria.seek(0)
    return memoria,{'palavras':palavras,'linhas_detectadas':len(linhas),
        'variante_ocr': variante, 'evidencias_estruturais_variantes': pontuacoes,
        'confianca_media':sum(p['confianca_ocr'] for p in palavras)/len(palavras) if palavras else None,
        'tesseract':str(pytesseract.get_tesseract_version())}


def preparar(origem: Path, destino: Path, config: ConfigOCR) -> list[dict]:
    import pypdfium2 as pdfium
    leitor=PdfReader(origem)
    escritor=PdfWriter()
    auditoria=[]
    quantidade_ocr = 0
    with pdfplumber.open(origem) as pdf, pdfium.PdfDocument(str(origem)) as renderizador:
        for indice,pagina in enumerate(pdf.pages):
            numero=indice+1
            usar,motivo=decidir(pagina,config,numero)
            registro={'pagina':numero,'metodo':'ocr' if usar else 'digital','motivo':motivo}
            if usar:
                quantidade_ocr += 1
                if quantidade_ocr > config.max_paginas_ocr:
                    raise RuntimeError('Limite de páginas OCR excedido; divida o PDF ou ajuste --max-paginas-ocr.')
                if pagina.width * pagina.height * (config.dpi / 72) ** 2 > config.max_megapixels * 1_000_000:
                    raise RuntimeError('Página excede o limite de pixels para OCR. Reduza o DPI.')
                print(f"  Página {numero}/{len(pdf.pages)}: OCR",flush=True)
                pagina_render=renderizador[indice]
                try:
                    bitmap=pagina_render.render(scale=config.dpi/72)
                    try:
                        imagem=bitmap.to_pil().copy()
                    finally:bitmap.close()
                finally:pagina_render.close()
                memoria,detalhes=reconhecer(imagem,pagina.width,pagina.height,config)
                imagem.close()
                escritor.add_page(PdfReader(memoria).pages[0])
                registro.update(detalhes)
            else:
                escritor.add_page(leitor.pages[indice])
            auditoria.append(registro)
            pagina.close()
        if any(p>len(pdf.pages) or p<1 for p in config.paginas_forcadas):
            raise ValueError("--paginas-ocr contém uma página fora do documento.")
    with destino.open('wb') as stream:escritor.write(stream)
    return auditoria
