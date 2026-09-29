"""Cobertura observada não é uma classificação negativa do conteúdo da página."""
import re
from collections import defaultdict
from .documento import normalizar
from .segmentacao import cabecalho


def paginas_fontes(obj):
    paginas = set()
    if isinstance(obj, dict):
        if isinstance(obj.get('pagina'), int):
            paginas.add(obj['pagina'])
        for v in obj.values():
            paginas.update(paginas_fontes(v))
    elif isinstance(obj, list):
        for v in obj:
            paginas.update(paginas_fontes(v))
    return paginas


def atualizar_cobertura(analise, linhas, paginas):
    campos = defaultdict(set)
    sinais = defaultdict(set)
    for r in analise['ementas']:
        usadas = paginas_fontes(r.get('evidencias', {})) | paginas_fontes(r.get('rotulos', {}))
        perfil = r.get('auditoria_perfil', {})
        for item in perfil.get('consolidacao_conteudo', []):
            if item.get('decisao') == 'candidato_extraido' and item.get('indices_itens'):
                usadas.update(paginas_fontes(item.get('fontes', [])))
        usadas.update(paginas_fontes(perfil.get('carga_horaria', {})))
        r['paginas_com_evidencias'] = sorted(usadas)
        r['paginas_com_campos_extraidos'] = sorted(usadas)
        for pagina in usadas:
            campos[pagina].add(r['numero'])
            sinais[pagina].add('fonte_de_campo_extraido')
    for r in analise['candidatos_inconclusivos']:
        for pagina in paginas_fontes(r.get('evidencias', {})) | paginas_fontes(r.get('rotulos', {})):
            sinais[pagina].add('candidato_inconclusivo')
    for t in analise.get('tabelas_academicas', []):
        sinais[t['pagina']].add('tabela_academica')
    for l in linhas:
        t = normalizar(l['texto'])
        if cabecalho(l['texto']):
            sinais[l['pagina']].add('rotulo_de_secao_academica')
        if re.search(r'^(?:planos? de (?:ensino|aprendizagem)|projeto pedagogico do curso|curso\s*:|ementa de disciplina|ementa do curso|disciplinas cursadas|'
                     r'(?:[a-z]\)\s*)?(?:metodologia|recursos)\s*:|cronograma\b)', t):
            sinais[l['pagina']].add('cabecalho_ou_contexto_academico')
    numeros = {p['pagina'] for p in paginas}
    classificacao = analise['classificacao']
    classificacao.pop('paginas_sem_evidencias_de_ementa', None)
    classificacao.update({
        'paginas_com_campos_extraidos': sorted(campos),
        'paginas_sem_campos_extraidos': sorted(numeros - set(campos)),
        'paginas_com_sinais_academicos': sorted(sinais),
        'paginas_sem_sinais_academicos_detectados': sorted(numeros - set(sinais)),
        'nota_cobertura': 'Sem campos extraídos ou sem sinais detectados não significa ausência de ementa. Nenhuma página é descartada por essas listas.',
        'cobertura_por_pagina': [
            {'pagina': n, 'ementas_com_campos_nesta_pagina': sorted(campos.get(n, set())),
             'sinais_detectados': sorted(sinais.get(n, set()))} for n in sorted(numeros)]})
    return analise
