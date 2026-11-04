from equivalencia_ementas.equivalencia.application.comparar_trechos import (
    CompararTrechos,
)
from equivalencia_ementas.equivalencia.domain.entities import (
    TrechoAcademico,
)


class GeradorFalso:
    nome_modelo = "modelo-falso"

    def gerar(self, textos):
        vetores = {
            "Destino A": [1.0, 0.0],
            "Destino B": [0.0, 1.0],
            "Origem A": [0.9, 0.1],
            "Origem B": [0.1, 0.9],
        }

        return [vetores[texto] for texto in textos]


def criar_trecho(texto):
    return TrechoAcademico(
        secao="conteudo_programatico",
        indice=0,
        texto=texto,
        quantidade_tokens=2,
    )


def test_identificar_melhores_correspondencias():
    comparador = CompararTrechos(GeradorFalso())

    destino = [
        criar_trecho("Destino A"),
        criar_trecho("Destino B"),
    ]

    origem = [
        criar_trecho("Origem A"),
        criar_trecho("Origem B"),
    ]

    resultado = comparador.executar(
        trechos_origem=origem,
        trechos_destino=destino,
        quantidade_melhores=1,
    )

    assert len(resultado.correspondencias) == 2

    assert (
        resultado.correspondencias[0].trecho_origem.texto
        == "Origem A"
    )

    assert (
        resultado.correspondencias[1].trecho_origem.texto
        == "Origem B"
    )


def test_preservar_identificacao_do_modelo():
    comparador = CompararTrechos(GeradorFalso())

    resultado = comparador.executar(
        trechos_origem=[criar_trecho("Origem A")],
        trechos_destino=[criar_trecho("Destino A")],
    )

    assert resultado.modelo == "modelo-falso"


def test_sem_trechos_de_origem():
    comparador = CompararTrechos(GeradorFalso())

    resultado = comparador.executar(
        trechos_origem=[],
        trechos_destino=[criar_trecho("Destino A")],
    )

    assert resultado.correspondencias == ()
    assert resultado.quantidade_trechos_destino == 1
    assert resultado.quantidade_trechos_origem == 0


def test_sem_trechos_de_destino():
    comparador = CompararTrechos(GeradorFalso())

    resultado = comparador.executar(
        trechos_origem=[criar_trecho("Origem A")],
        trechos_destino=[],
    )

    assert resultado.correspondencias == ()


def test_preservar_pontuacao():
    comparador = CompararTrechos(GeradorFalso())

    resultado = comparador.executar(
        trechos_origem=[criar_trecho("Origem A")],
        trechos_destino=[criar_trecho("Destino A")],
    )

    assert 0 <= resultado.correspondencias[0].similaridade <= 1

def test_retornar_tres_melhores_correspondencias():
    comparador = CompararTrechos(GeradorFalso())

    origem = [
        criar_trecho("Origem A"),
        criar_trecho("Origem B"),
    ]

    destino = [
        criar_trecho("Destino A"),
    ]

    resultado = comparador.executar(
        trechos_origem=origem,
        trechos_destino=destino,
        quantidade_melhores=3,
    )

    # Existem apenas dois trechos de origem.
    assert len(resultado.correspondencias) == 2

    assert (
        resultado.correspondencias[0].similaridade
        >= resultado.correspondencias[1].similaridade
    )


def test_limitar_quantidade_correspondencias():
    comparador = CompararTrechos(GeradorFalso())

    origem = [
        criar_trecho("Origem A"),
        criar_trecho("Origem B"),
    ]

    destino = [
        criar_trecho("Destino A"),
    ]

    resultado = comparador.executar(
        trechos_origem=origem,
        trechos_destino=destino,
        quantidade_melhores=1,
    )

    assert len(resultado.correspondencias) == 1


def test_rejeitar_quantidade_invalida():
    import pytest

    comparador = CompararTrechos(GeradorFalso())

    with pytest.raises(ValueError):
        comparador.executar(
            trechos_origem=[criar_trecho("Origem A")],
            trechos_destino=[criar_trecho("Destino A")],
            quantidade_melhores=0,
        )


def test_preservar_ordem_dos_trechos_destino():
    comparador = CompararTrechos(GeradorFalso())

    destino = [
        criar_trecho("Destino A"),
        criar_trecho("Destino B"),
    ]

    origem = [
        criar_trecho("Origem A"),
        criar_trecho("Origem B"),
    ]

    resultado = comparador.executar(
        trechos_origem=origem,
        trechos_destino=destino,
        quantidade_melhores=2,
    )

    assert len(resultado.correspondencias) == 4

    assert [
        item.trecho_destino.texto
        for item in resultado.correspondencias
    ] == [
        "Destino A",
        "Destino A",
        "Destino B",
        "Destino B",
    ]

def test_calcular_similaridade_lexical():
    comparador = CompararTrechos(GeradorFalso())

    resultado = comparador.executar(
        trechos_origem=[criar_trecho("Origem A")],
        trechos_destino=[criar_trecho("Destino A")],
    )

    correspondencia = resultado.correspondencias[0]

    assert correspondencia.similaridade_lexical is not None

    assert (
        0 <= correspondencia.similaridade_lexical <= 1
    )


def test_preservar_ordenacao_semantica():
    comparador = CompararTrechos(GeradorFalso())

    resultado = comparador.executar(
        trechos_origem=[
            criar_trecho("Origem A"),
            criar_trecho("Origem B"),
        ],
        trechos_destino=[
            criar_trecho("Destino A"),
        ],
        quantidade_melhores=2,
    )

    correspondencias = resultado.correspondencias

    assert (
        correspondencias[0].similaridade
        >= correspondencias[1].similaridade
    )

    assert all(
        item.similaridade_lexical is not None
        for item in correspondencias
    )

def test_recuperacao_hibrida_inclui_candidato_lexical(
    monkeypatch,
):
    import equivalencia_ementas.equivalencia.application.comparar_trechos as modulo

    class GeradorControlado:
        nome_modelo = "modelo-controlado"

        def gerar(self, textos):
            vetores = {
                "Destino A": [1.0, 0.0],
                "Origem A": [1.0, 0.0],
                "Origem B": [0.0, 1.0],
            }
            return [vetores[texto] for texto in textos]

    # O candidato A vence semanticamente.
    # O candidato B vence lexicalmente.
    monkeypatch.setattr(
        modulo,
        "calcular_similaridade_lexical",
        lambda textos_destino, textos_origem: [
            [0.1, 0.9]
        ],
    )

    comparador = CompararTrechos(GeradorControlado())

    resultado = comparador.executar(
        trechos_origem=[
            criar_trecho("Origem A"),
            criar_trecho("Origem B"),
        ],
        trechos_destino=[
            criar_trecho("Destino A"),
        ],
        quantidade_melhores=1,
        recuperacao_hibrida=True,
    )

    nomes = {
        correspondencia.trecho_origem.texto
        for correspondencia in resultado.correspondencias
    }

    assert nomes == {"Origem A", "Origem B"}
    assert len(resultado.correspondencias) == 2

def test_recuperacao_hibrida_nao_duplica_candidatos():
    comparador = CompararTrechos(GeradorFalso())

    resultado = comparador.executar(
        trechos_origem=[
            criar_trecho("Origem A"),
            criar_trecho("Origem B"),
        ],
        trechos_destino=[
            criar_trecho("Destino A"),
        ],
        quantidade_melhores=2,
        recuperacao_hibrida=True,
    )

    assert len(resultado.correspondencias) == 2

    nomes = [
        item.trecho_origem.texto
        for item in resultado.correspondencias
    ]

    assert len(nomes) == len(set(nomes))