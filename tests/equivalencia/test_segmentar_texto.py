import pytest

from equivalencia_ementas.equivalencia.application.segmentar_texto import (
    ErroSegmentacao,
    segmentar_texto,
)


def contar_palavras(texto: str) -> int:
    """
    Contador artificial utilizado somente nos testes.
    Considera cada palavra como um token.
    """
    return len(texto.split()) if texto else 0


def test_texto_curto():
    resultado = segmentar_texto(
        "Introdução aos bancos de dados.",
        contar_palavras,
        10,
    )

    assert resultado == [
        "Introdução aos bancos de dados."
    ]


def test_texto_longo():
    resultado = segmentar_texto(
        "um dois três quatro cinco seis",
        contar_palavras,
        3,
    )

    assert resultado == [
        "um dois três",
        "quatro cinco seis",
    ]


def test_preservar_todas_as_palavras():
    texto = "um dois três quatro cinco seis sete"

    resultado = segmentar_texto(
        texto,
        contar_palavras,
        3,
    )

    assert " ".join(resultado) == texto


def test_texto_vazio():
    assert segmentar_texto(
        "",
        contar_palavras,
        10,
    ) == []


def test_texto_com_espacos():
    resultado = segmentar_texto(
        "  um   dois \n três  ",
        contar_palavras,
        10,
    )

    assert resultado == ["um dois três"]


def test_limite_invalido():
    with pytest.raises(ErroSegmentacao):
        segmentar_texto(
            "texto",
            contar_palavras,
            0,
        )


def test_palavra_maior_que_limite():
    def contador(texto: str) -> int:
        return len(texto)

    with pytest.raises(ErroSegmentacao):
        segmentar_texto(
            "palavra",
            contador,
            3,
        )