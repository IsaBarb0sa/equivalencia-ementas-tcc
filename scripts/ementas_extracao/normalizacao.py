"""Projeção acadêmica; conserva evidências e exclusões na auditoria."""
import re
from .estrutural import normalizar


def limpar(t):
    return re.sub(r"\s+"," ",t or "").strip()


def consolidar(dados):
    explicito=dados['campos']['conteudo_programatico']['valor']
    auditoria=[]
    itens=[]
    vistos={}
    if explicito:
        # Linhas numeradas são itens; texto sem numeração permanece íntegro.
        partes=re.split(r"(?m)^\s*\d+[.)]\s+",explicito)
        itens=[limpar(p) for p in partes if limpar(p)]
        return {'itens':itens,'origem':'secao_explicita','status':'pendente_revisao'},auditoria
    registros=[]
    for fragmento in dados['cronograma_fragmentos']:
        identificacao=limpar(fragmento['identificacao'])
        novo=bool(re.match(r"^(?:Aulas?\b|Unidade\s+\d|Prova\b|Exame\b|Atividade\b|Semana\b|Correção\b)",identificacao,re.I))
        if novo or not registros:
            registros.append({'texto':fragmento['texto'],'fontes':[fragmento['fonte']]})
        else:
            registros[-1]['texto']+=' '+fragmento['texto']
            registros[-1]['fontes'].append(fragmento['fonte'])
    for registro in registros:
        texto=limpar(registro['texto'])
        # Capítulos do programa têm prioridade sobre instruções administrativas.
        capitulos=list(re.finditer(r"Cap[ií]tulo\s+[IVXLCDM]+\s*[–—-]\s*",texto,re.I))
        candidatos=[]
        if capitulos:
            for idx,m in enumerate(capitulos):
                candidatos.append(texto[m.end():capitulos[idx+1].start() if idx+1<len(capitulos) else len(texto)])
        elif re.search(r"\bEbook\s*[–—-]",texto,re.I):
            candidatos=[re.split(r"\bEbook\s*[–—-]",texto,flags=re.I)[-1]]
        elif re.match(r"^(?:Prova|Avaliação|Exame|Revisão|Correção|Apresentação)\b",texto,re.I):
            registro.update(decisao='revisar_ou_excluir',motivo='Registro administrativo ou misto; preservado para revisão')
            auditoria.append(registro);continue
        elif re.match(r"^Leitura\b",texto,re.I):
            registro.update(decisao='revisar',motivo='Leitura sem tema delimitado; não inferir tema de uma referência')
            auditoria.append(registro);continue
        else:candidatos=[texto]
        for candidato in candidatos:
            candidato=re.split(r"\b(?:Trabalho Prático|Valor\s*:|Entrega\s*:)",candidato,flags=re.I)[0]
            candidato=re.sub(r"\((?:Continua[çc][aã]o|Aula Pr[aá]tica|Pr[aá]tica)\)","",candidato,flags=re.I)
            candidato=re.split(r"\s*[–—-]\s*Resenha\b",candidato,flags=re.I)[0]
            candidato=limpar(candidato).strip(' .;–-')
            if not candidato:continue
            chave=normalizar(candidato).strip(' .;')
            # Somente igualdade após limpeza explícita, nunca similaridade aproximada.
            if chave not in vistos:
                vistos[chave]=len(itens);itens.append(candidato)
            registro.setdefault('indices_itens',[]).append(vistos[chave])
        registro['decisao']='candidato_extraido';auditoria.append(registro)
    return {'itens':itens,'origem':'temas_cronograma' if registros else 'nao_localizado',
            'status':'pendente_revisao' if registros else 'nao_localizado'},auditoria


def projetar(dados):
    def valor(nome):return dados['campos'][nome]['valor']
    conteudo,auditoria=consolidar(dados)
    competencias=valor('competencias_habilidades')
    if competencias:
        competencias='\n'.join(l for l in competencias.splitlines()
            if not re.match(r"^\s*(?:\(?Art\b|Resolução\s+CNE|Curso de Odontologia:\s*CNE)",l,re.I)).strip() or None
    saida={
        'instituicao':valor('instituicao'),'curso':valor('curso'),'disciplina':valor('disciplina'),
        'carga_horaria':{k:f['valor'] for k,f in dados['carga_horaria']['valores'].items()},
        'objetivos':{'geral':valor('objetivo_geral_disciplina'),
                    'especificos':valor('objetivos_especificos_disciplina'),
                    'nao_classificados':valor('objetivos_aprendizagem')},
        'competencias_habilidades':competencias,'ementa':valor('ementa'),
        'conteudo_programatico':conteudo,
        'bibliografia':{'basica':valor('bibliografia_basica'),'complementar':valor('bibliografia_complementar')},
        'status':'pendente_revisao'}
    saida['carga_horaria']['unidade']=dados['carga_horaria']['unidade']
    dados['consolidacao_conteudo']=auditoria
    return saida
