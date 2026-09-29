"""Extração determinística orientada a evidências; não estima probabilidade."""
from __future__ import annotations
import re
from .documento import normalizar, fonte
from .segmentacao import cabecalho, encontrar_inicios, inicio_contexto, IDENTIDADE, SECOES

INSTITUICAO = re.compile(r'^(?:funda[cç][aã]o\s+)?(?:universidade|faculdade|centro universit[aá]rio|instituto universit[aá]rio)\b', re.I)
RODAPE = re.compile(r'^(?:documento assinado|este documento [ée] assinado|a autenticidade|sua autenticidade|'
    r'c[oó]digo de controle|refer[eê]ncia: processo|style=|secretaria setorial|fonte: sia)', re.I)
ADMINISTRATIVO = re.compile(r'^(?:hist[oó]rico escolar|diploma|certificado de conclus[aã]o|declara[cç][aã]o de matr[ií]cula)\b', re.I)


def vazio():
    return {'instituicao': None, 'curso': None, 'disciplina': None,
        'carga_horaria': {'total': None, 'teorica': None, 'pratica': None, 'unidade': None},
        'objetivos': {'geral': None, 'especificos': None, 'nao_classificados': None},
        'competencias_habilidades': None, 'ementa': None, 'conteudo_programatico': None,
        'bibliografia': {'basica': None, 'complementar': None, 'nao_classificada': None}}


def atribuir(dados, caminho, valor):
    partes = caminho.split('.')
    atual = dados
    for parte in partes[:-1]:
        atual = atual[parte]
    atual[partes[-1]] = valor


def metadados(linhas, dados, evidencias, avisos):
    encontrados = {'instituicao': [], 'curso': [], 'carga_horaria.total': [],
                   'carga_horaria.teorica': [], 'carga_horaria.pratica': []}
    brutos = []
    def registrar(campo, valor, linha):
        encontrados[campo].append((valor, fonte(linha)))
    for i, linha in enumerate(linhas):
        t, n = linha['texto'], normalizar(linha['texto'])
        if INSTITUICAO.match(t) and len(t) < 180:
            registrar('instituicao', t, linha)
        m = re.match(r'^institui[cç][aã]o\s*:\s*(.+)', t, re.I)
        if m:
            registrar('instituicao', m.group(1), linha)
        m = re.match(r'^curso(?:\(s\))?\s*(?::|\s)\s*(.+)', t, re.I)
        if m and not re.match(r'(?i)^(de odontologia: cne|de graduacao|e disciplina)', m.group(1)):
            registrar('curso', m.group(1).strip(' |'), linha)
        if 'carga horaria' in n or re.match(r'^(?:parte |ch )?(?:teorica|pratica)\b', n):
            brutos.append(fonte(linha))
            for prox in linhas[i+1:i+4]:
                if cabecalho(prox['texto']):
                    break
                brutos.append(fonte(prox))
        # Valores na mesma linha com rótulo explícito. Duas colunas numéricas
        # ou subtotais presencial/EAD exigem interpretação própria e revisão.
        padroes = {
            'carga_horaria.total': r'carga\s+hor[aá]ria(?:\s+total)?(?:\s*\(h/a\))?\s*:?\s*(\d+(?:[,.]\d+)?)\s*(horas?|h/a|h)?\s*$',
            'carga_horaria.teorica': r'^(?:parte\s+|ch\s+)?te[oó]rica\s*:?\s*(\d+(?:[,.]\d+)?)\s*(horas?|h/a|h)?\s*$',
            'carga_horaria.pratica': r'^(?:parte\s+|ch\s+)?pr[aá]tica\s*:?\s*(\d+(?:[,.]\d+)?)\s*(horas?|h/a|h)?\s*$',
        }
        for campo, regex in padroes.items():
            m = re.search(regex, t, re.I)
            if m:
                valor = float(m.group(1).replace(',', '.'))
                registrar(campo, int(valor) if valor.is_integer() else valor, linha)
                unidade = 'hora_aula' if 'h/a' in n else 'hora_declarada' if m.group(2) else None
                if unidade:
                    dados['carga_horaria']['unidade'] = unidade
        if n == 'carga horaria turmas' and i + 1 < len(linhas):
            m = re.fullmatch(r'(\d+)\s+(\d+)', linhas[i+1]['texto'])
            if m:
                registrar('carga_horaria.total', int(m.group(1)), linhas[i+1])
        if re.search(r'(?:nao\s*-?\s*presencial|horaria semanal|teorica ead)', n):
            avisos.add('tabela_carga_multiplas_modalidades_requer_revisao')
    for campo, itens in encontrados.items():
        valores = {str(v) for v, _ in itens}
        if len(valores) == 1:
            atribuir(dados, campo, itens[0][0])
            evidencias[campo] = [f for _, f in itens]
        elif len(valores) > 1:
            avisos.add('valores_conflitantes:' + campo)
            evidencias[campo] = [f for _, f in itens]
    return brutos


def extrair_segmento(linhas, inicio, fim, numero):
    pos = inicio['indice']
    trecho = linhas[pos:fim]
    dados, evidencias, avisos = vazio(), {}, set()
    dados['disciplina'] = inicio['nome']
    evidencias['disciplina'] = [fonte(linhas[i]) for i in inicio.get('fontes_nome', [pos])]
    # Contexto local: nenhum dado da primeira instituição se propaga pelo PDF.
    antes = []
    for linha in reversed(linhas[max(0, pos - 18):pos]):
        if linha['pagina'] != linhas[pos]['pagina'] or cabecalho(linha['texto']):
            break
        antes.insert(0, linha)
    primeira_secao = next((i for i, l in enumerate(trecho) if cabecalho(l['texto'])), len(trecho))
    carga_bruta = metadados(antes + trecho[:primeira_secao], dados, evidencias, avisos)
    buffers = {k: [] for k in SECOES if k != '_parar'}
    ativo, rodape_pagina, pagina_anterior = None, None, trecho[0]['pagina']
    rotulos = {}
    paginas_usadas = {trecho[0]['pagina']}
    termino = None
    ultimo_limite = trecho[-1]
    for linha in trecho:
        t, n = linha['texto'], normalizar(linha['texto'])
        # No ementário sem rótulo de identidade, um novo capítulo institucional
        # encerra o último bloco, em vez de anexar o restante do PPC à ementa.
        if inicio['metodo'] == 'titulo_antes_da_ementa' and re.match(
            r'^\d+(?:\.\d+)*\s+(?:metodologia de ensino|estrutura administrativa|infraestrutura|avaliacao do curso)\s*$', n):
            termino = fonte(linha)
            anteriores = [l for l in trecho if l['indice'] < linha['indice']]
            ultimo_limite = anteriores[-1] if anteriores else trecho[0]
            break
        if linha['pagina'] > pagina_anterior + 1:
            ativo = None
            avisos.add('lacuna_de_paginas_interrompeu_continuidade')
        pagina_anterior = linha['pagina']
        if rodape_pagina == linha['pagina']:
            continue
        if RODAPE.match(t):
            rodape_pagina = linha['pagina']
            continue
        if ADMINISTRATIVO.match(t):
            ativo = None
            continue
        if linha['margem_repetida'] or re.fullmatch(r'(?:p[aá]gina\s*:?\s*)?\d+', t, re.I):
            continue
        if INSTITUICAO.match(t) or linha['indice'] in [pos, *inicio['repeticoes']] or n in ('ementa de disciplina', 'plano de ensino', 'ementa - plano de ensino'):
            continue
        if re.match(r'^https?://(?:www\.)?uninter\.com/documentosdigitais/', n) or re.fullmatch(r'[-_]{5,}', n):
            continue
        if re.match(r'^(?:nome:|ra:|professor:|docente|nota/situacao:|sigla/codigo|periodo letivo:|codigo de controle:)', n):
            continue
        h = cabecalho(t)
        if ativo and ativo.startswith('objetivos.'):
            sub = normalizar(t).strip(' :')
            if sub in ('geral', 'especificos'):
                h = ('objetivos.' + ('geral' if sub == 'geral' else 'especificos'), '')
        if re.match(r'^(?:cronograma\b|aula\s+data\b|data\s+aula\b|aulas?\s+conteudo\b)', n):
            h = ('_parar', '')
        if h:
            campo, valor = h
            ativo = None if campo == '_parar' else campo
            if ativo:
                rotulos.setdefault(ativo, []).append(fonte(linha))
                if valor:
                    buffers[ativo].append(valor)
                    evidencias.setdefault(ativo, []).append(fonte(linha))
                    paginas_usadas.add(linha['pagina'])
            continue
        if ativo:
            buffers[ativo].append(t)
            evidencias.setdefault(ativo, []).append(fonte(linha))
            paginas_usadas.add(linha['pagina'])
    for campo, valores in buffers.items():
        atribuir(dados, campo, '\n'.join(valores).strip() or None)
    academicos = [k for k, v in buffers.items() if len(' '.join(v)) >= 30]
    conteudo = any(k in academicos for k in ('ementa', 'conteudo_programatico'))
    auxiliares = [k for k in academicos if k not in ('ementa', 'conteudo_programatico')]
    suficiente = conteudo and (bool(auxiliares) or dados['carga_horaria']['total'] is not None)
    if not dados['ementa']:
        avisos.add('ementa_nao_localizada')
    for campo in ('instituicao', 'curso', 'conteudo_programatico'):
        if not dados[campo]:
            avisos.add(campo + '_nao_localizado')
    if dados['carga_horaria']['teorica'] is None or dados['carga_horaria']['pratica'] is None:
        avisos.add('carga_teorica_ou_pratica_nao_localizada')
    if inicio['metodo'] == 'titulo_antes_da_ementa':
        avisos.add('nome_inferido_da_posicao_do_titulo')
    if len(rotulos.get('ementa', [])) > 1:
        avisos.add('multiplas_secoes_ementa_conferir_segmentacao')
    return {'numero': numero, 'status': 'pendente_revisao', 'dados': dados,
        'identificacao': 'ementa_identificada' if suficiente else 'candidato_inconclusivo',
        'paginas_com_evidencias': sorted(paginas_usadas),
        'inicio': fonte(trecho[0]), 'fim_do_intervalo': fonte(ultimo_limite),
        'encerramento_por_capitulo': termino,
        'metodo_segmentacao': inicio['metodo'], 'avisos': sorted(avisos),
        'evidencias': evidencias, 'rotulos': rotulos, 'carga_horaria_bruta': carga_bruta,
        'criterios': {'identidade': True, 'conteudo_academico': conteudo, 'secoes_auxiliares': auxiliares}}


def analisar(linhas, paginas):
    inicios = encontrar_inicios(linhas)
    contextos = [inicio_contexto(linhas, inicio['indice'], inicios[i-1]['indice'] + 1 if i else 0)
                for i, inicio in enumerate(inicios)]
    registros, inconclusivos = [], []
    for i, inicio in enumerate(inicios):
        fim = contextos[i+1] if i + 1 < len(inicios) else len(linhas)
        fim = max(fim, inicio['indice'] + 1)
        registro = extrair_segmento(linhas, inicio, fim, len(registros) + 1)
        (registros if registro['identificacao'] == 'ementa_identificada' else inconclusivos).append(registro)
    sinais = []
    for l in linhas:
        if ADMINISTRATIVO.match(l['texto']):
            sinais.append({'pagina': l['pagina'], 'tipo': normalizar(l['texto']).split(':')[0][:60]})
    sem_texto = [p['pagina'] for p in paginas if p['caracteres'] < 30]
    if registros:
        classe = 'contem_ementas'
        motivo = 'Identidade, conteúdo acadêmico e evidências auxiliares encontrados nos segmentos.'
    elif all(p['caracteres'] < 30 for p in paginas):
        classe, motivo = 'ilegivel', 'Texto insuficiente; não é possível concluir qual é o tipo documental.'
    elif sinais and not inicios and not any(cabecalho(l['texto']) for l in linhas):
        classe, motivo = 'nao_identificado_como_ementa', 'Sinais de documento administrativo, sem estrutura de ementa identificada.'
    else:
        classe, motivo = 'revisao_necessaria', 'Evidências insuficientes ou estrutura desconhecida; não equivale a documento inválido.'
    usadas = {p for r in registros for p in r['paginas_com_evidencias']}
    return {'classificacao': {'resultado': classe, 'motivo': motivo,
        'sinais_administrativos': sinais, 'paginas_sem_texto_suficiente': sem_texto,
        'paginas_sem_campos_extraidos': [p['pagina'] for p in paginas if p['pagina'] not in usadas]},
        'ementas': registros, 'candidatos_inconclusivos': inconclusivos,
        'status': 'pendente_revisao', 'gravacao_no_banco_autorizada': False}
