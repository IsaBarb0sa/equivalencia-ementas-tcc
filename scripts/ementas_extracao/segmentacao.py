"""Inícios por identidade explícita ou título imediatamente anterior a EMENTA."""
from __future__ import annotations
import re
from .documento import normalizar

SECOES = {
    'ementa': ('ementa', 'ementario', 'ementa da disciplina', 'ementa da disciplina no curso'),
    'objetivos.geral': ('objetivo geral', 'objetivos gerais', 'objetivo geral / *topico gerador'),
    'objetivos.especificos': ('objetivos especificos', 'objetivo especifico', 'objetivos especificos / *metas de compreensao'),
    'objetivos.nao_classificados': ('objetivos', 'objetivos da disciplina', 'objetivos de aprendizagem', 'objetivo', 'objetivos da disciplina no curso'),
    'competencias_habilidades': ('competencias e habilidades', 'competencias/habilidades', 'habilidades e competencias',
        'competencias', 'competencias especificas', 'habilidades', 'habilidades a serem desenvolvidas'),
     'conteudo_programatico': (
        'conteudo programatico',
        'conteudos programaticos',
        'programa',
        'unidades de ensino',
        'estrutura da disciplina',
        'conteudo de ensino',
    ),
    'bibliografia.basica': ('bibliografia basica', 'referencias basicas', 'referencia basica', 'bibliografia obrigatoria'),
    'bibliografia.complementar': ('bibliografia complementar', 'referencias complementares', 'referencia complementar'),
    'bibliografia.nao_classificada': ('bibliografia', 'referencias', 'referencias bibliograficas'),
    '_parar': ('metodologia', 'metodologia de ensino', 'metodologia de ensino e aprendizagem', 'procedimentos metodologicos',
        'avaliacao', 'avaliacao da aprendizagem', 'criterios de avaliacao', 'sistema de avaliacao', 'perfil do egresso',
        'cronograma', 'cronograma de aulas', 'cronograma de atividades', 'estrategias de ensinagem', 'recursos didaticos',
        'objetivos do curso', 'objetivo geral do curso', 'objetivos especificos do curso', 'justificativa', 'contextualizacao',
        'procedimentos metodologico', 'procedimentos metodologicos', 'procedimento metodologico', 'pesquisar novamente'),
}


def cabecalho(texto: str) -> tuple[str, str] | None:
    texto = re.sub(r'^\s*(?:\d+(?:\.\d+)*(?:\s*[.\-–):]\s*|\s+))', '', texto).strip()
    n = normalizar(texto).strip(' :;().')
    for campo, rotulos in SECOES.items():
        for rotulo in rotulos:
            if n == rotulo:
                return campo, ''
            if ':' in texto and normalizar(texto.split(':', 1)[0]).strip(' ()') == rotulo:
                return campo, texto.split(':', 1)[1].strip()
    return None


IDENTIDADE = re.compile(r'^(?:\d+[º°ª]?\s+)?(?:c[oó]digo\s*/\s*disciplina|nome\s+da\s+disciplina|'
    r'componente\s+curricular|disciplina(?:\s*/\s*\*?unidade\s+curricular)?)\s*(?::|[-–]|\s)\s*(.*)$', re.I)


def nome_valido(texto: str) -> bool:
    n = normalizar(texto)
    return (3 <= len(texto) <= 180 and bool(re.search(r'[a-z]{3}', n)) and not cabecalho(texto)
        and not re.search(r'^(?:carga horaria|periodo|codigo|professor|docente|nota|nome:|turma|ementa de|plano de|curso\b)', n)
        and n not in ('teorica', 'pratica', 'hibrida', 'teorico pratica', 'nome', 'nota carga horaria')
        and not re.search(r'(?:\s+\d+(?:[,.]\d+)?){3,}\s*$', n)
        and not re.fullmatch(r'[\d\W]+', n))


def limpar_nome(texto: str) -> str:
    texto = re.split(r'\b(?:Carga\s+Hor[aá]ria|Per[ií]odo\s+Letivo|Docente|Professor|Turmas?)\s*:', texto, flags=re.I)[0]
    return re.sub(r'\s+TURMAS?\s*$', '', texto).strip(' |:–-')

def identidade_em_colunas(linhas, indice):
    """Reconstrói código/nome à direita de um rótulo isolado."""
    rotulo = linhas[indice]

    if normalizar(rotulo["texto"]).strip(" :") != "codigo/disciplina":
        return None

    x0, y0, x1, y1 = rotulo["bbox"]
    altura = max(y1 - y0, 1)

    proximas = [
        (j, linhas[j])
        for j in range(
            max(0, indice - 6),
            min(len(linhas), indice + 9),
        )
        if linhas[j]["pagina"] == rotulo["pagina"]
    ]

    primeiras = [
        (j, linha)
        for j, linha in proximas
        if linha["bbox"][0] > x1
        and abs(linha["bbox"][1] - y0) <= 2 * altura
        and re.match(
            r"^\d{4,}\s*[-–]\s*\S",
            linha["texto"],
        )
    ]

    # Só associamos quando existe um candidato inequívoco.
    if len(primeiras) != 1:
        return None

    j, primeira = primeiras[0]
    partes = [primeira["texto"]]
    fontes = [indice, j]
    ultima = primeira

    for k, linha in sorted(
        proximas,
        key=lambda par: par[1]["bbox"][1],
    ):
        if k == j or linha["bbox"][1] <= primeira["bbox"][1]:
            continue

        caixa = linha["bbox"]

        if caixa[0] <= x1:
            continue

        if caixa[1] > y1 + 2 * altura:
            break

        texto = linha["texto"].strip()

        if (
            abs(caixa[0] - primeira["bbox"][0]) > altura
            or caixa[1] - ultima["bbox"][3] > altura
            or not texto.isupper()
            or not nome_valido(texto)
            or re.match(r"^\d{4,}\s*[-–]", texto)
        ):
            break

        partes.append(texto)
        fontes.append(k)
        ultima = linha

    nome = limpar_nome(" ".join(partes))

    if not nome_valido(nome):
        return None

    return nome, min(fontes), sorted(set(fontes))

def encontrar_inicios(linhas: list[dict]) -> list[dict]:
    candidatos = []
    for i, linha in enumerate(linhas):
        t, n = linha['texto'], normalizar(linha['texto'])
        nome, inicio, metodo = None, i, None
        fontes_colunas = None
        identidade_colunas = identidade_em_colunas(linhas, i)
        m = IDENTIDADE.match(t)

        if identidade_colunas is not None:
            nome, inicio, fontes_colunas = identidade_colunas
            metodo = "identidade_em_colunas"

        elif n.strip(" :") == "codigo/disciplina":
            # Sem associação segura, não capturar qualquer linha seguinte.
            continue

        elif m:
            # "A disciplina..." / "disciplina diferencia..." são prosa.
            # Sem delimitador explícito, exigir aparência de rótulo + título.
            prefixo = t[:m.start(1)]
            valor_bruto = m.group(1).strip(' |')
            if ':' not in prefixo and valor_bruto and not valor_bruto[0].isupper() and not valor_bruto[0].isdigit():
                continue
            nome = limpar_nome(m.group(1))
            if not nome_valido(nome) and i + 1 < len(linhas):
                if linhas[i + 1]['pagina'] == linha['pagina']:
                    nome = limpar_nome(linhas[i + 1]['texto'])
            metodo = 'rotulo_de_disciplina'
        elif n == 'ementa de disciplina' and i + 1 < len(linhas):
            nome = limpar_nome(linhas[i + 1]['texto'])
            metodo = 'titulo_apos_ementa_de_disciplina'
        elif cabecalho(t) == ('ementa', '') and i:
            anterior = linhas[i - 1]
            titulo = anterior['texto']
            if (anterior['pagina'] == linha['pagina'] and titulo.isupper() and nome_valido(titulo)
                and ':' not in titulo and len(titulo) <= 140
                and not re.search(r'\b(?:DOCENTE|HORÁRIA|SEMESTRE|PROFESSOR|BIBLIOGRAFIA|PRÉ.REQUISITO)\b', titulo)):
                nome, inicio, metodo = titulo, i - 1, 'titulo_antes_da_ementa'
                # Títulos longos do ementário podem ocupar várias linhas.
                while inicio > 0:
                    anterior_titulo = linhas[inicio - 1]
                    texto_anterior = anterior_titulo['texto']
                    atual = linhas[inicio]
                    altura = max(atual['bbox'][3] - atual['bbox'][1], anterior_titulo['bbox'][3] - anterior_titulo['bbox'][1])
                    centro_atual = (atual['bbox'][0] + atual['bbox'][2]) / 2
                    centro_anterior = (anterior_titulo['bbox'][0] + anterior_titulo['bbox'][2]) / 2
                    if (anterior_titulo['pagina'] != linha['pagina'] or not texto_anterior.isupper()
                        or cabecalho(texto_anterior) or re.search(r'[.;:]', texto_anterior)
                        or not nome_valido(texto_anterior)
                        or atual['bbox'][1] - anterior_titulo['bbox'][3] > altura
                        or abs(centro_atual - centro_anterior) > 2 * altura
                        or len(texto_anterior + ' ' + nome) > 180):
                        break
                    nome = texto_anterior + ' ' + nome
                    inicio -= 1
        if nome and nome_valido(nome):
            if candidatos and inicio - candidatos[-1]['indice'] < 18:
                entre = linhas[candidatos[-1]['indice']:inicio]
                if not any(cabecalho(l['texto']) and cabecalho(l['texto'])[0] == 'ementa' for l in entre):
                    if metodo == 'titulo_antes_da_ementa':
                        continue
            if candidatos:
                anterior = candidatos[-1]
                a, b = normalizar(anterior['nome']), normalizar(nome)
                sufixo = b[len(a):].strip() if b.startswith(a + ' ') else ''
                codigo_proximo = (0 < len(sufixo) <= 8 and re.fullmatch(r'[a-z0-9 ]+', sufixo)
                    and i - anterior['indice'] < 18 and linhas[anterior['indice']]['pagina'] == linha['pagina'])
                if a == b or codigo_proximo:
                    anterior['repeticoes'].append(i)
                    continue
            fontes_nome = list(range(inicio, i)) if metodo == 'titulo_antes_da_ementa' else [i]
            if metodo != 'titulo_antes_da_ementa' and nome not in t and i+1 < len(linhas):
                fontes_nome.append(i+1)
            if fontes_colunas is not None:
                fontes_nome = fontes_colunas
            candidatos.append({'indice': inicio, 'nome': nome, 'metodo': metodo, 'repeticoes': [], 'fontes_nome': fontes_nome})
    return candidatos


def inicio_contexto(linhas: list[dict], indice: int, minimo: int) -> int:
    """Inclui cabeçalho do NOVO documento, evitando anexá-lo à bibliografia anterior."""
    pagina = linhas[indice]['pagina']
    candidatos = []
    for i in range(max(minimo, indice - 18), indice):
        if linhas[i]['pagina'] != pagina:
            continue
        n = normalizar(linhas[i]['texto'])
        if re.match(r'^(?:ministerio da educacao|fundacao universidade|universidade |faculdade |centro universitario |'
                    r'instituto universitario |ementa do curso|ementa - plano de ensino|planos? de ensino|instituicao:)', n):
            candidatos.append(i)
    return min(candidatos, default=indice)
