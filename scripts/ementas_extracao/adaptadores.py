"""Reutiliza a interpretação de tabelas já testada no layout de aprendizagem.

O perfil depende de marcadores de layout e não do nome do arquivo/instituição.
Nunca é executado sobre uma coletânea identificada como multidisciplina.
"""
from .documento import normalizar
from .estrutural import extrair
from .normalizacao import projetar


def aplicar_perfil_aprendizagem(caminho, linhas, analise):
    textos = [normalizar(l['texto']) for l in linhas]
    if (textos.count('plano de aprendizagem') != 1 or len(analise['ementas']) > 1
        or any(t in ('ementa de disciplina', 'plano de ensino', 'ementa do curso') for t in textos)
        or max((l['pagina'] for l in linhas), default=0) > 40):
        return analise
    if not any('componente curricular:' in t or 'disciplina:' in t for t in textos):
        return analise
    auditoria = extrair(caminho)
    dados = projetar(auditoria)
    if not dados['disciplina'] or len(dados['ementa'] or '') < 30:
        return analise
    if not (dados['carga_horaria']['total'] is not None or any(dados['objetivos'].values()) or any(dados['bibliografia'].values())):
        return analise
    dados.pop('status', None)
    dados['bibliografia']['nao_classificada'] = None
    conteudo = dados['conteudo_programatico']
    dados['conteudo_programatico'] = '\n'.join(conteudo['itens']) or None
    fontes = [f for c in auditoria['campos'].values() for f in c['fontes']]
    paginas = sorted({f['pagina'] for f in fontes})
    avisos = list(auditoria['avisos'])
    if conteudo['origem'] == 'temas_cronograma':
        avisos.append('conteudo_candidato_consolidado_de_temas_do_cronograma_conferir')
    registro = {'numero': 1, 'status': 'pendente_revisao', 'dados': dados,
        'identificacao': 'ementa_identificada', 'paginas_com_evidencias': paginas,
        'metodo_segmentacao': 'perfil_plano_aprendizagem_unico', 'avisos': avisos,
        'evidencias': auditoria['campos'], 'auditoria_perfil': auditoria}
    analise['ementas'] = [registro]
    analise['candidatos_inconclusivos'] = []
    analise['classificacao']['resultado'] = 'contem_ementas'
    analise['classificacao']['motivo'] = 'Perfil estrutural de plano de aprendizagem único, com identidade e conteúdo acadêmico.'
    analise['classificacao']['paginas_sem_campos_extraidos'] = sorted(set(l['pagina'] for l in linhas) - set(paginas))
    return analise
