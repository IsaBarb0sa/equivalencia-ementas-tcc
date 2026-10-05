"""Tabela presencial/não presencial verificada nos modelos da UNIUBE."""
from decimal import Decimal
from ementas_extracao.comum.celulas import chave, numero, celulas, abaixo, evidencia

def presencial_nao_presencial(tabela, pagina):
    linhas = celulas(tabela)
    todas = [c for linha in linhas for c in linha]

    def unica(rotulo):
        itens = [
            c for c in todas
            if chave(c["texto"]) == rotulo
        ]
        return itens[0] if len(itens) == 1 else None

    def valor_direita(rotulo):
        if rotulo is None:
            return None

        itens = [
            c for c in todas
            if abs(c["bbox"][1] - rotulo["bbox"][1]) < 1
            and abs(c["bbox"][0] - rotulo["bbox"][2]) < 1
        ]
        return itens[0] if len(itens) == 1 else None

    nome = valor_direita(unica("codigodisciplina"))
    total = valor_direita(unica("cargahorariaha"))

    grupos = {
        "presencial": unica("cargahorariapresencial"),
        "nao_presencial": unica("cargahorarianaopresencial"),
    }
    extensao = unica("cargahorariaextensao")

    if nome is None or total is None or extensao is None:
        return []

    if not nome["texto"] or any(g is None for g in grupos.values()):
        return []

    esperadas = {
        "presencial": {
            "teorica",
            "pratica",
            "atividadeautonoma",
            "atividadeassistida",
            "total",
        },
        "nao_presencial": {
            "teorica",
            "pratica",
            "atividade",
            "total",
        },
    }

    colunas = {}

    for grupo, caixa in grupos.items():
        filhas = [
            c for c in todas
            if abs(c["bbox"][1] - caixa["bbox"][3]) < 1
            and c["bbox"][0] >= caixa["bbox"][0] - 1
            and c["bbox"][2] <= caixa["bbox"][2] + 1
        ]

        rotulos = {chave(c["texto"]) for c in filhas}
        obrigatorias = esperadas[grupo]
        permitidas = obrigatorias | {"teoricapratica"}

        if (
                len(rotulos) != len(filhas)
                or not obrigatorias.issubset(rotulos)
                or not rotulos.issubset(permitidas)
        ):
            return []

        for c in filhas:
            colunas[grupo + "." + chave(c["texto"])] = c

    colunas["extensao"] = extensao

    fim = max(c["bbox"][3] for c in colunas.values())

    candidatas = [
        linha for linha in linhas
        if linha
        and all(abs(c["bbox"][1] - fim) < 1 for c in linha)
    ]

    if len(candidatas) != 1:
        return []

    valores = {}
    fontes = [
        evidencia(pagina, nome),
        evidencia(pagina, total),
    ]

    for campo, coluna in colunas.items():
        c = abaixo(coluna, candidatas[0])
        valores[campo] = numero(c["texto"]) if c else None

        if c:
            fontes.append(evidencia(pagina, c, coluna))

    declarado = numero(total["texto"])

    # Célula vazia não é automaticamente zero.
    if declarado is None or any(v is None for v in valores.values()):
        return []

    def soma(campos):
        return sum(
            Decimal(str(valores[c]))
            for c in campos
        )

    avisos = []

    for grupo in grupos:
        campos = [
            campo
            for campo in valores
            if campo.startswith(grupo + ".")
               and campo != grupo + ".total"
        ]

        if soma(campos) != Decimal(str(valores[grupo + ".total"])):
            avisos.append("subtotal_divergente:" + grupo)

    if soma([
        "presencial.total",
        "nao_presencial.total",
        "extensao",
    ]) != Decimal(str(declarado)):
        avisos.append("total_modalidades_divergente")

    teorica = float(soma([
        "presencial.teorica",
        "nao_presencial.teorica",
    ]))

    pratica = float(soma([
        "presencial.pratica",
        "nao_presencial.pratica",
    ]))

    campos_mistos = [
        campo
        for campo in valores
        if campo.endswith(".teoricapratica")
    ]

    carga_mista = soma(campos_mistos)

    if carga_mista > 0:
        avisos.append(
            "carga_teorico_pratica_sem_divisao_declarada"
        )

    return [{
        "tipo": "presencial_nao_presencial",
        "disciplina": nome["texto"],
        "pagina": pagina,
        "bbox": list(tabela.bbox),
        "fontes": fontes,
        "avisos": avisos,
        "carga": {
            "total": declarado,
            "unidade": "hora_aula",
            "teorica": None if avisos else teorica,
            "pratica": None if avisos else pratica,
            "teorico_pratica": (
                float(carga_mista)
                if campos_mistos
                else None
            ),
            "modalidades": valores,
            "origem_total": "celula_total_declarado",
            "observacao": (
                "Atividades e extensão preservadas separadamente; "
                "sem conversão para hora-relógio."
            ),
        },
    }]

