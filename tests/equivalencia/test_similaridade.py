import pytest

from equivalencia_ementas.equivalencia.domain.services.similaridade import (
    ErroSimilaridade,
    similaridade_cosseno,
)


def test_vetores_identicos():
    resultado = similaridade_cosseno(
        [1.0, 2.0, 3.0],
        [1.0, 2.0, 3.0],
    )

    assert resultado == pytest.approx(1.0)


def test_vetores_ortogonais():
    resultado = similaridade_cosseno(
        [1.0, 0.0],
        [0.0, 1.0],
    )

    assert resultado == pytest.approx(0.0)


def test_vetores_opostos():
    resultado = similaridade_cosseno(
        [1.0, 0.0],
        [-1.0, 0.0],
    )

    assert resultado == pytest.approx(-1.0)


def test_vetores_com_dimensoes_diferentes():
    with pytest.raises(ErroSimilaridade):
        similaridade_cosseno(
            [1.0, 2.0],
            [1.0, 2.0, 3.0],
        )


def test_vetor_nulo():
    with pytest.raises(ErroSimilaridade):
        similaridade_cosseno(
            [0.0, 0.0],
            [1.0, 2.0],
        )


def test_vetores_vazios():
    with pytest.raises(ErroSimilaridade):
        similaridade_cosseno([], [])


def test_rejeitar_valor_infinito():
    with pytest.raises(ErroSimilaridade):
        similaridade_cosseno(
            [float("inf"), 1.0],
            [1.0, 2.0],
        )