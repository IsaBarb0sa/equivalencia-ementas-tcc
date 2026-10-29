import pytest

from equivalencia_ementas.equivalencia.infrastructure.ia.sentence_transformer import (
    GeradorSentenceTransformer,
)


def test_identificar_modelo():
    gerador = GeradorSentenceTransformer(
        modelo="modelo-de-teste"
    )

    assert gerador.nome_modelo == "modelo-de-teste"


def test_lista_vazia_nao_carrega_modelo():
    gerador = GeradorSentenceTransformer()

    assert gerador.gerar([]) == []


def test_rejeitar_texto_vazio():
    gerador = GeradorSentenceTransformer()

    with pytest.raises(ValueError):
        gerador.gerar(["Texto válido", ""])


def test_rejeitar_texto_em_branco():
    gerador = GeradorSentenceTransformer()

    with pytest.raises(ValueError):
        gerador.gerar(["   "])