"""Projeção acadêmica; conserva evidências e exclusões na auditoria."""
import re
from .estrutural import normalizar


def limpar(t):
    return re.sub(r"\s+"," ",t or "").strip()


def consolidar(dados):
    explicito = dados['campos']['conteudo_programatico']['valor']
    auditoria, itens, vistos = [], [], {}

    if explicito:
        partes = re.split(r'(?m)^\s*\d+[.)]\s+', explicito)
        return {
            'itens': [limpar(p) for p in partes if limpar(p)],
            'origem': 'secao_explicita',
            'status': 'pendente_revisao',
        }, auditoria

    registros = []

    # Reconhece o início de uma nova atividade, inclusive no plural.
    inicio_registro = (
        r'^(?:Aulas?\s+\d+|Unidades?\b|Provas?\b|Exames?\b|Atividades?\b|'
        r'Semanas?|Correções|Correção)\b'
    )

    for fragmento in dados['cronograma_fragmentos']:
        identificacao = limpar(fragmento.get('identificacao'))
        novo = re.match(inicio_registro, identificacao, re.I)

        if novo or not registros:
            registros.append({
                'identificacao': identificacao,
                'texto': fragmento['texto'],
                'fontes': [fragmento['fonte']],
            })
        else:
            # Continuações da mesma célula permanecem juntas.
            registros[-1]['texto'] += ' ' + fragmento['texto']
            registros[-1]['fontes'].append(fragmento['fonte'])

    for registro in registros:
        texto = limpar(registro['texto'])

        identidade = normalizar(registro.get('identificacao', ''))
        generico = normalizar(texto).strip(' .;:')

        avaliacao = re.match(
            r'^(?:exames?|provas?)\b',
            identidade,
        )

        atividade_sem_tema = generico in {
            'grupos de estudos',
            'grupo de estudos',
            'semana da odontologia',
        }

        somente_pontuacao = re.fullmatch(
            r'(?:\d+(?:[.,]\d+)?\s*)?pontos?[.;]?',
            generico,
        )

        if avaliacao or atividade_sem_tema or somente_pontuacao:
            registro.update(
                decisao='revisar_ou_excluir',
                motivo='Avaliação ou atividade sem tema delimitado.',
            )
            auditoria.append(registro)
            continue

        # Uma célula pode começar com uma correção de prova
        # e apresentar um tema acadêmico logo depois.
        texto = re.sub(
            r'^Correção\s+da\s+Avaliação\s+'
            r'(?:Teórica|Prática)\s*[.;:]\s*',
            '',
            texto,
            flags=re.I,
        )

        # Retira a apresentação administrativa quando ela termina
        # uma frase, preservando o assunto que aparece em seguida.
        texto = re.sub(
            r'^Apresentação\s+do\s+Plano\s+de\s+'
            r'(?:Ensino|Aprendizagem)(?:\s+da\s+Disciplina)?\s*[.;:]\s*',
            '',
            texto,
            flags=re.I,
        )

        # Não excluir genericamente "Avaliação" ou "Exames":
        # essas palavras também fazem parte de temas acadêmicos.
        administrativo = re.match(
            r'^(?:Trabalho\s+de\s+revisão\b|'
            r'Realização\s+de\s+avaliação\b|Provas?\b|'
            r'Exames?\s+(?:especial|final|de\s+recuperação)\b|'
            r'Revisão\b|Correção\b|'
            r'Avaliação\s+(?:teórica|prática|individual|final|'
            r'da\s+\d|de\s+aprendizagem|\d))',
            texto,
            re.I,
        )

        if not texto or administrativo:
            registro.update(
                decisao='revisar_ou_excluir',
                motivo='Atividade administrativa; original preservado.',
            )
            auditoria.append(registro)
            continue

        capitulos = list(re.finditer(
            r'Cap[ií]tulo\s+[IVXLCDM]+\s*[–—-]\s*',
            texto,
            re.I,
        ))

        if re.match(r'^Trabalho\s+de\s+pesquisa\b', texto, re.I):
            # Aproveita o assunto explícito, não as instruções do trabalho.
            tema = re.search(r'\bTema\s*:\s*(.+)', texto, re.I)
            candidatos = [tema.group(1)] if tema else []

        elif capitulos:
            candidatos = [
                texto[
                    m.end():
                    capitulos[i + 1].start()
                    if i + 1 < len(capitulos)
                    else len(texto)
                ]
                for i, m in enumerate(capitulos)
            ]

        elif re.search(r'\bEbook\s*[–—-]', texto, re.I):
            candidatos = [
                re.split(
                    r'\bEbook\s*[–—-]',
                    texto,
                    flags=re.I,
                )[-1]
            ]

        elif re.match(r'^(?:Leitura|Apresentação)\b', texto, re.I):
            candidatos = []

        else:
            candidatos = [texto]

        for candidato in candidatos:
            candidato = re.split(
                r'\b(?:Enviar\s+via\s+portal|Trabalho\s+Prático|'
                r'Valor\s*:|Entrega\s*:)',
                candidato,
                flags=re.I,
            )[0]

            candidato = re.sub(
                r'\((?:Continua[çc][aã]o|Aula\s+Pr[aá]tica|Pr[aá]tica)\)',
                '',
                candidato,
                flags=re.I,
            )

            candidato = re.split(
                r'\s*[–—-]\s*Resenha\b',
                candidato,
                flags=re.I,
            )[0]

            candidato = limpar(candidato).strip(' .;:–—-"“”')

            # Ex.: "pré- operatória" passa a "pré-operatória".
            candidato = re.sub(r'-\s+', '-', candidato)

            if not candidato:
                continue

            chave = normalizar(candidato).strip(' .;')

            # Elimina apenas repetições iguais após normalização.
            if chave not in vistos:
                vistos[chave] = len(itens)
                itens.append(candidato)

            registro.setdefault('indices_itens', []).append(vistos[chave])

        registro['decisao'] = (
            'candidato_extraido'
            if registro.get('indices_itens')
            else 'revisar'
        )
        auditoria.append(registro)

    return {
        'itens': itens,
        'origem': 'temas_cronograma' if registros else 'nao_localizado',
        'status': 'pendente_revisao' if registros else 'nao_localizado',
    }, auditoria

def limpar_marcadores(texto):
    if not texto:
        return texto

    texto = re.sub(
        r'(?m)^[ \t]*[\u2022\u2023\u25e6\u2043\u2219\uf0b7\uf0a7]+[ \t]*',
        '',
        texto,
    )

    return texto.strip() or None

def projetar(dados):
    def valor(nome):
        return limpar_marcadores(dados['campos'][nome]['valor'])
    conteudo,auditoria=consolidar(dados)
    competencias = valor('competencias_habilidades')

    if competencias:
        competencias = '\n'.join(
            linha
            for linha in competencias.splitlines()
            if not re.match(
                r'^\s*(?:'
                r'\(?Art\b|'
                r'Resolução\s+CNE|'
                r'Curso de Odontologia:\s*CNE|'
                r'CNE\s*/\s*CES\b'
                r')',
                linha,
                re.I,
            )
        ).strip() or None
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
