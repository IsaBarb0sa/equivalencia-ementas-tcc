import equivalencia_ementas.equivalencia.application.comparar_disciplina_com_matriz as modulo

from equivalencia_ementas.equivalencia.application.comparar_disciplina_com_matriz import (
    CompararDisciplinaComMatriz,
)
from equivalencia_ementas.equivalencia.domain.entities import (
    DisciplinaParaEquivalencia,
    ResultadoComparacaoTrechos,
    TrechoAcademico,
)


class ComparadorFalso:
    def __init__(self):
        self.chamadas = []

    def executar(
        self,
        trechos_origem,
        trechos_destino,
        quantidade_melhores=3,
        recuperacao_hibrida=False,
    ):
        self.chamadas.append({
            "origem": trechos_origem,
            "destino": trechos_destino,
            "quantidade_melhores": quantidade_melhores,
            "recuperacao_hibrida": recuperacao_hibrida,
        })

        return ResultadoComparacaoTrechos(
            modelo="modelo-falso",
            correspondencias=(),
            quantidade_trechos_origem=len(trechos_origem),
            quantidade_trechos_destino=len(trechos_destino),
        )


def criar_disciplina(nome, ementa="Conteúdo acadêmico"):
    return DisciplinaParaEquivalencia(
        nome=nome,
        ementa=ementa,
    )


def preparar_trechos_falso(
    disciplina,
    contar_tokens,
    limite_tokens,
):
    if not disciplina.ementa:
        return []

    return [
        TrechoAcademico(
            secao="ementa",
            indice=0,
            texto=disciplina.ementa,
            quantidade_tokens=2,
        )
    ]


def criar_caso_de_uso(monkeypatch):
    monkeypatch.setattr(
        modulo,
        "preparar_trechos",
        preparar_trechos_falso,
    )

    comparador = ComparadorFalso()

    caso_de_uso = CompararDisciplinaComMatriz(
        comparador=comparador,
        contar_tokens=lambda texto: len(texto.split()),
        limite_tokens=128,
    )

    return caso_de_uso, comparador


def test_comparar_todas_disciplinas_da_matriz(monkeypatch):
    caso_de_uso, comparador = criar_caso_de_uso(
        monkeypatch
    )

    origem = criar_disciplina("Disciplina de origem")

    matriz = [
        criar_disciplina("Disciplina A"),
        criar_disciplina("Disciplina B"),
        criar_disciplina("Disciplina C"),
    ]

    resultados = caso_de_uso.executar(
        disciplina_origem=origem,
        disciplinas_matriz=matriz,
    )

    assert len(resultados) == 3
    assert len(comparador.chamadas) == 3

    assert [
        item.disciplina_destino.nome
        for item in resultados
    ] == [
        "Disciplina A",
        "Disciplina B",
        "Disciplina C",
    ]


def test_utilizar_recuperacao_hibrida(monkeypatch):
    caso_de_uso, comparador = criar_caso_de_uso(
        monkeypatch
    )

    caso_de_uso.executar(
        disciplina_origem=criar_disciplina("Origem"),
        disciplinas_matriz=[
            criar_disciplina("Destino"),
        ],
    )

    assert comparador.chamadas[0]["recuperacao_hibrida"] is True


def test_matriz_vazia(monkeypatch):
    caso_de_uso, comparador = criar_caso_de_uso(
        monkeypatch
    )

    resultados = caso_de_uso.executar(
        disciplina_origem=criar_disciplina("Origem"),
        disciplinas_matriz=[],
    )

    assert resultados == ()
    assert comparador.chamadas == []


def test_destino_sem_conteudo(monkeypatch):
    caso_de_uso, comparador = criar_caso_de_uso(
        monkeypatch
    )

    resultados = caso_de_uso.executar(
        disciplina_origem=criar_disciplina("Origem"),
        disciplinas_matriz=[
            criar_disciplina("Destino", ementa=None),
        ],
    )

    assert len(resultados) == 1
    assert resultados[0].status == "destino_sem_conteudo"
    assert resultados[0].resultado is None
    assert comparador.chamadas == []


def test_origem_sem_conteudo(monkeypatch):
    caso_de_uso, comparador = criar_caso_de_uso(
        monkeypatch
    )

    resultados = caso_de_uso.executar(
        disciplina_origem=criar_disciplina(
            "Origem",
            ementa=None,
        ),
        disciplinas_matriz=[
            criar_disciplina("Destino A"),
            criar_disciplina("Destino B"),
        ],
    )

    assert len(resultados) == 2

    assert all(
        item.status == "origem_sem_conteudo"
        for item in resultados
    )

    assert comparador.chamadas == []


def test_preservar_indice_da_matriz(monkeypatch):
    caso_de_uso, _ = criar_caso_de_uso(
        monkeypatch
    )

    resultados = caso_de_uso.executar(
        disciplina_origem=criar_disciplina("Origem"),
        disciplinas_matriz=[
            criar_disciplina("Mesmo nome"),
            criar_disciplina("Mesmo nome"),
        ],
    )

    assert [
        item.indice_matriz
        for item in resultados
    ] == [0, 1]


def test_integrar_consolidacao_de_evidencias(monkeypatch):
    caso_de_uso, _ = criar_caso_de_uso(
        monkeypatch
    )

    resultados = caso_de_uso.executar(
        disciplina_origem=criar_disciplina("Origem"),
        disciplinas_matriz=[
            criar_disciplina("Destino"),
        ],
    )

    assert len(resultados) == 1

    comparacao = resultados[0]

    assert comparacao.status == "comparado"
    assert comparacao.consolidacao is not None

    assert (
        comparacao.consolidacao.total_correspondencias_originais
        == 0
    )


def test_destino_sem_conteudo_nao_possui_consolidacao(
    monkeypatch,
):
    caso_de_uso, _ = criar_caso_de_uso(
        monkeypatch
    )

    resultados = caso_de_uso.executar(
        disciplina_origem=criar_disciplina("Origem"),
        disciplinas_matriz=[
            criar_disciplina(
                "Destino",
                ementa=None,
            ),
        ],
    )

    assert resultados[0].status == "destino_sem_conteudo"
    assert resultados[0].consolidacao is None