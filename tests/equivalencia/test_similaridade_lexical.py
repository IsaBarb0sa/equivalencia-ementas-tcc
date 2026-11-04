import pytest

from equivalencia_ementas.equivalencia.domain.services.similaridade_lexical import (
    calcular_similaridade_lexical,
)


def test_textos_identicos():
    resultado = calcular_similaridade_lexical(
        textos_destino=["Álgebra Relacional"],
        textos_origem=["Álgebra Relacional"],
    )

    assert resultado[0][0] == pytest.approx(1.0)


def test_textos_relacionados():
    resultado = calcular_similaridade_lexical(
        textos_destino=["Normalização de Banco de Dados"],
        textos_origem=[
            "Dependência funcional e normalização",
            "Anatomia do sistema respiratório",
        ],
    )

    assert resultado[0][0] > resultado[0][1]


def test_preservar_dimensoes():
    resultado = calcular_similaridade_lexical(
        textos_destino=[
            "Álgebra Relacional",
            "Linguagem SQL",
        ],
        textos_origem=[
            "Modelo Relacional",
            "Consultas SQL",
            "Normalização",
        ],
    )

    assert len(resultado) == 2
    assert len(resultado[0]) == 3
    assert len(resultado[1]) == 3


def test_sem_origem():
    resultado = calcular_similaridade_lexical(
        textos_destino=["Banco de Dados"],
        textos_origem=[],
    )

    assert resultado == [[]]


def test_sem_destino():
    resultado = calcular_similaridade_lexical(
        textos_destino=[],
        textos_origem=["Banco de Dados"],
    )

    assert resultado == []


def test_textos_vazios():
    resultado = calcular_similaridade_lexical(
        textos_destino=[""],
        textos_origem=[""],
    )

    assert resultado == [[0.0]]


def test_similaridade_entre_zero_e_um():
    resultado = calcular_similaridade_lexical(
        textos_destino=["Modelagem de dados"],
        textos_origem=["Modelo entidade-relacionamento"],
    )

    assert 0 <= resultado[0][0] <= 1