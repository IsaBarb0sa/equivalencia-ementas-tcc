"""Tabelas por geometria e significado dos cabeçalhos, nunca por índice fixo.

Dois formatos reconhecidos: matriz semanal com totais em hora-aula/relógio;
quadro local com teoria/prática presencial/EaD e extensão. Outros preservam null.
"""
from __future__ import annotations
from collections import defaultdict
from decimal import Decimal
import re
import pdfplumber
from .documento import normalizar, fonte


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


def matriz(tabela, pagina):
    linhas = celulas(tabela)
    todas = [c for r in linhas for c in r]
    # Linhas vetoriais espúrias podem repartir um cabeçalho em duas células
    # ("PRÁTIC" + "A", ou "COMPONENTES" acima de "CURRICULARES").
    for alvo in ('componentescurriculares', 'pratica', 'teorica', 'total'):
        if any(chave(c['texto']) == alvo for c in todas):
            continue
        iniciais = [c for c in todas if chave(c['texto']) and alvo.startswith(chave(c['texto']))]
        for a in iniciais:
            for b in list(todas):
                if a is b or chave(a['texto'] + b['texto']) != alvo:
                    continue
                ax, ay, bx, by = a['bbox']; cx, cy, dx, dy = b['bbox']
                horizontal = abs(bx-cx) < 5 and min(by,dy) > max(ay,cy)
                vertical = abs(by-cy) < 5 and min(bx,dx) > max(ax,cx)
                if horizontal or vertical:
                    todas.append({'texto': a['texto'] + ' ' + b['texto'],
                                  'bbox': [min(ax,cx), min(ay,cy), max(bx,dx), max(by,dy)]})
                    break
    def localizar(rotulo):
        return next((c for c in todas if chave(c['texto']) == rotulo), None)
    nome = localizar('componentescurriculares')
    semanal = localizar('cargahorariasemanal')
    aula, relogio = localizar('horaaula'), localizar('horarelogio')
    if not all((nome, semanal, aula, relogio)):
        return []
    fim_cabecalho = max(nome['bbox'][3], aula['bbox'][3], relogio['bbox'][3])
    colunas = {'total_hora_aula': aula, 'total_hora_relogio': relogio}
    for rotulo, campo in [('teorica', 'teorica'), ('pratica', 'pratica'), ('total', 'total')]:
        candidatos = [c for c in todas if chave(c['texto']) == rotulo
            and c['bbox'][1] >= semanal['bbox'][3] - 1
            and c['bbox'][3] <= fim_cabecalho + 1
            and c['bbox'][0] >= semanal['bbox'][0] - 1
            and c['bbox'][2] <= semanal['bbox'][2] + 1]
        if len(candidatos) != 1:
            return []
        colunas['semanal.' + campo] = candidatos[0]
    registros = []
    for linha in linhas:
        if not linha or min(c['bbox'][1] for c in linha) < fim_cabecalho - 1:
            continue
        celula_nome = abaixo(nome, linha)
        if not celula_nome or not celula_nome['texto'] or chave(celula_nome['texto']) == 'total':
            continue
        valores, fontes = {}, [evidencia(pagina, celula_nome, nome)]
        for campo, coluna in colunas.items():
            c = abaixo(coluna, linha)
            valores[campo] = numero(c['texto']) if c else None
            if c:
                fontes.append(evidencia(pagina, c, coluna))
        if valores['total_hora_aula'] is None or valores['total_hora_relogio'] is None:
            continue
        sem = {k: valores['semanal.' + k] for k in ('teorica', 'pratica', 'total')}
        sem['unidade'] = 'nao_declarada'
        avisos = []
        if all(sem[k] is not None for k in ('teorica', 'pratica', 'total')) and abs(sem['teorica'] + sem['pratica'] - sem['total']) > .001:
            avisos.append('soma_semanal_divergente')
        registros.append({'tipo': 'matriz_semanal', 'disciplina': celula_nome['texto'], 'pagina': pagina,
            'bbox': list(tabela.bbox), 'fontes': fontes, 'avisos': avisos,
            'carga': {'total': valores['total_hora_relogio'], 'unidade': 'hora_relogio',
                'teorica': None, 'pratica': None, 'total_hora_aula': valores['total_hora_aula'],
                'total_hora_relogio': valores['total_hora_relogio'], 'semanal': sem,
                'origem_total': 'coluna_hora_relogio',
                'observacao': 'Teoria/prática semanais não foram convertidas em totais. Célula vazia não equivale a zero.'}})
    return registros


def modalidades(tabela, pagina):
    linhas = celulas(tabela)
    todas = [c for r in linhas for c in r]
    nomes = [c for c in todas if re.match(r'^disciplina\s*:', normalizar(c['texto']))]
    if len(nomes) != 1:
        return []
    totais_simples = [c for c in todas if re.match(r'^carga horaria\s*:', normalizar(c['texto']))]
    if len(totais_simples) == 1:
        total = numero(totais_simples[0]['texto'].split(':', 1)[1])
        if total is not None:
            return [{'tipo': 'total_local', 'disciplina': nomes[0]['texto'].split(':', 1)[1].strip(),
                'pagina': pagina, 'bbox': list(tabela.bbox), 'avisos': [],
                'fontes': [evidencia(pagina, nomes[0]), evidencia(pagina, totais_simples[0])],
                'carga': {'total': total, 'teorica': None, 'pratica': None, 'unidade': 'hora_declarada',
                    'origem_total': 'celula_carga_horaria',
                    'observacao': 'O quadro informa somente o total; o nome da disciplina não determina a divisão teórica/prática.'}}]
    rotulos = {'teoricapresencial': 'teorica_presencial', 'teoricaead': 'teorica_ead',
               'praticapresencial': 'pratica_presencial', 'praticaead': 'pratica_ead',
               'atividadespraticasinterdisciplinaresdeextensao': 'extensao'}
    colunas = {rotulos[chave(c['texto'])]: c for c in todas if chave(c['texto']) in rotulos}
    if len(colunas) != 5:
        return []
    fim = max(c['bbox'][3] for c in colunas.values())
    candidatas = [r for r in linhas if r and min(c['bbox'][1] for c in r) >= fim - 1]
    if len(candidatas) != 1:
        return []
    linha = candidatas[0]
    valores, fontes = {}, [evidencia(pagina, nomes[0])]
    for campo, coluna in colunas.items():
        c = abaixo(coluna, linha)
        valores[campo] = numero(c['texto']) if c else None
        if c:
            fontes.append(evidencia(pagina, c, coluna))
    def somar(*campos):
        itens = [valores[c] for c in campos]
        return sum(itens) if all(v is not None for v in itens) else None
    return [{'tipo': 'modalidades_locais', 'disciplina': nomes[0]['texto'].split(':', 1)[1].strip(),
        'pagina': pagina, 'bbox': list(tabela.bbox), 'fontes': fontes, 'avisos': [],
        'carga': {'total': somar(*valores), 'teorica': somar('teorica_presencial', 'teorica_ead'),
            'pratica': somar('pratica_presencial', 'pratica_ead'), 'unidade': 'hora_declarada',
            'modalidades': valores, 'origem_total': 'soma_das_cinco_colunas',
            'observacao': 'Extensão preservada separadamente; não foi somada à prática. Unidade h não comprova duração de hora-aula.'}}]


def ler_tabelas(caminho, linhas):
    por_pagina = defaultdict(list)
    for l in linhas:
        por_pagina[l['pagina']].append(l['texto'])
    candidatas = set()
    for pagina, textos in por_pagina.items():
        n = chave(' '.join(textos))
        if ('cargahorariasemanal' in n and 'componentes' in n and 'curriculares' in n) or ('teoricaead' in n and 'praticaead' in n) or ('planosdeensino' in n and 'disciplina' in n and 'cargahoraria' in n):
            candidatas.add(pagina)
    registros = []
    with pdfplumber.open(caminho) as pdf:
        for numero_pagina in sorted(candidatas):
            pagina = pdf.pages[numero_pagina - 1]
            for tabela in pagina.find_tables():
                registros.extend(matriz(tabela, numero_pagina))
                registros.extend(modalidades(tabela, numero_pagina))
            pagina.close()
    return registros


def metadados_contextuais(linhas):
    """Somente rótulos explícitos da capa/identificação, com escopo auditado."""
    iniciais = [l for l in linhas if l['pagina'] <= 4]
    textos = ' '.join(normalizar(l['texto']) for l in iniciais)
    ppc = 'projeto pedagogico do curso' in textos
    formulario = 'formulario de programa de' in textos and 'disciplinas cursadas' in textos
    dados = defaultdict(list)
    if not ppc and not formulario:
        return {}
    for l in iniciais:
        if formulario and l['pagina'] != 1:
            continue
        t = l['texto']
        m = re.match(r'^Institui[cç][aã]o de Ensino Superior:\s*(.+)$', t, re.I)
        if m:
            dados['instituicao'].append((m.group(1), fonte(l)))
        elif formulario and re.match(r'^(?:FACULDADE|UNIVERSIDADE|CENTRO UNIVERSITÁRIO)\s', t):
            dados['instituicao'].append((t, fonte(l)))
        m = re.match(r'^Curso:\s*(.+?)(?:\s+MATRIZ CURRICULAR:.*)?$', t, re.I)
        if m:
            dados['curso'].append((m.group(1), fonte(l)))
    return {k: {'valor': vs[0][0], 'fontes': [f for _, f in vs],
                'escopo': 'identificacao_ppc' if ppc else 'capa_programas_disciplinas'}
            for k, vs in dados.items() if len({chave(v) for v, _ in vs}) == 1}


def enriquecer(caminho, linhas, analise):
    tabelas = ler_tabelas(caminho, linhas)
    analise['tabelas_academicas'] = tabelas
    contexto = metadados_contextuais(linhas)
    # Capa só pode fornecer contexto se não houver outro curso/IES explicitamente
    # identificado nos registros. Continua sendo uma associação para revisão.
    todos = analise['ementas'] + analise['candidatos_inconclusivos']
    for campo in tuple(contexto):
        existentes = {chave(r['dados'][campo]) for r in todos if r['dados'][campo]}
        if existentes - {chave(contexto[campo]['valor'])}:
            del contexto[campo]
    for registro in todos:
        dados = registro['dados']
        nome = chave(dados['disciplina'])
        pagina = registro.get('inicio', {}).get('pagina', min(registro['paginas_com_evidencias'], default=1))
        locais = [t for t in tabelas if t['tipo'] in ('modalidades_locais', 'total_local') and t['pagina'] == pagina
                  and (chave(t['disciplina']) == nome or chave(t['disciplina']).startswith(nome))]
        escopo_ppc = contexto.get('curso', {}).get('escopo') == 'identificacao_ppc'
        exatas = [t for t in tabelas if t['tipo'] == 'matriz_semanal' and chave(t['disciplina']) == nome
                  and (escopo_ppc or t['pagina'] == pagina)]
        candidatas = locais or exatas
        if len(candidatas) == 1:
            tabela = candidatas[0]
            if tabela['tipo'] in ('modalidades_locais', 'total_local'):
                dados['disciplina'] = tabela['disciplina']
            anterior = dict(dados['carga_horaria'])
            tabela_valor = tabela['carga']
            # Não misturar medidas previamente extraídas em unidades distintas.
            registro['carga_horaria_anterior'] = anterior
            dados['carga_horaria'] = dict(tabela_valor)
            registro.setdefault('evidencias', {})['tabela_carga_horaria'] = tabela['fontes']
            registro['associacao_tabela'] = {'metodo': 'nome_exato_normalizado' if exatas and not locais else 'identidade_da_tabela_local',
                'pagina': tabela['pagina'], 'disciplina_na_tabela': tabela['disciplina']}
            registro['avisos'].extend(tabela['avisos'])
            if tabela['tipo'] == 'matriz_semanal':
                registro['avisos'].append('teoria_pratica_disponiveis_em_base_semanal')
                registro['avisos'].append('totais_teorica_pratica_nao_declarados')
                registro['avisos'] = [v for v in registro['avisos'] if v != 'carga_teorica_ou_pratica_nao_localizada']
            if anterior.get('total') is not None and anterior['total'] != tabela_valor['total']:
                registro['avisos'].append('carga_anterior_diferente_conferir_unidade_e_evidencias')
        elif len(candidatas) > 1:
            registro['avisos'].append('associacao_tabela_ambigua_nao_aplicada')
        # Curso local a partir do cabeçalho da mesma página da identidade.
        locais_curso = []
        for l in linhas:
            if l['pagina'] != pagina:
                continue
            m = re.match(r'^PLANOS? DE ENSINO\s*[–—-]\s*(.+?)(?:\s*\([^)]*\))?$', l['texto'], re.I)
            if m:
                locais_curso.append((m.group(1), fonte(l)))
        if not dados['curso'] and len({chave(v) for v, _ in locais_curso}) == 1:
            dados['curso'] = locais_curso[0][0]
            registro['evidencias']['curso_cabecalho'] = [f for _, f in locais_curso]
        for campo, meta in contexto.items():
            # Instituição da capa depende também da concordância do curso local.
            if campo == 'instituicao' and dados.get('curso') and contexto.get('curso') and chave(dados['curso']) != chave(contexto['curso']['valor']):
                continue
            if dados[campo] is None:
                dados[campo] = meta['valor']
                registro['evidencias'][campo + '_contextual'] = meta['fontes']
                registro['avisos'].append(campo + '_associado_por_' + meta['escopo'] + '_conferir')
        resolvidos = {k + '_nao_localizado' for k in ('instituicao', 'curso') if dados[k]}
        if dados['carga_horaria']['teorica'] is not None and dados['carga_horaria']['pratica'] is not None:
            resolvidos.add('carga_teorica_ou_pratica_nao_localizada')
        registro['avisos'] = sorted(set(registro['avisos']) - resolvidos)
        if (registro['identificacao'] == 'candidato_inconclusivo'
                and registro.get('criterios', {}).get('conteudo_academico')
                and dados['carga_horaria']['total'] is not None):
            registro['identificacao'] = 'ementa_identificada'
            registro['avisos'].append('identificacao_complementada_por_tabela')
    analise['ementas'] = [r for r in todos if r['identificacao'] == 'ementa_identificada']
    analise['candidatos_inconclusivos'] = [r for r in todos if r['identificacao'] != 'ementa_identificada']
    analise['ementas'].sort(key=lambda r: (r.get('inicio', {}).get('pagina', 0), r.get('inicio', {}).get('bbox', [0, 0])[1]))
    for i, r in enumerate(analise['ementas'], 1):
        r['numero'] = i
    if analise['ementas']:
        analise['classificacao']['resultado'] = 'contem_ementas'
    return analise
