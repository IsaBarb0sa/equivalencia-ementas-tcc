import pytest

from equivalencia_ementas.equivalencia.application.avaliar_recuperacao import (
    avaliar_recuperacao,
)
from equivalencia_ementas.equivalencia.domain.entities import (
    CorrespondenciaTrecho,
    ResultadoComparacaoTrechos,
    TrechoAcademico,
)


def trecho(texto, indice):
    return TrechoAcademico(
        secao="conteudo_programatico",
        indice=indice,
        texto=texto,
        quantidade_tokens=5,
    )


def resultado_com(correspondencias):
    return ResultadoComparacaoTrechos(
        modelo="modelo-teste",
        correspondencias=tuple(correspondencias),
        quantidade_trechos_destino=2,
        quantidade_trechos_origem=2,
    )


def test_recuperar_todas_as_referencias():
    destino = trecho("Modelo relacional", 0)
    origem = trecho("O modelo relacional", 1)

    resultado = resultado_com([
        CorrespondenciaTrecho(
            trecho_destino=destino,
            trecho_origem=origem,
            similaridade=0.9,
            similaridade_lexical=0.8,
        ),
    ])

    avaliacao = avaliar_recuperacao(
        resultado,
        referencias={
            destino: {origem},
        },
    )

    assert avaliacao.total_referencias == 1
    assert avaliacao.referencias_encontradas == 1
    assert avaliacao.revocacao == pytest.approx(1.0)


def test_identificar_referencia_nao_recuperada():
    destino = trecho("Normalização", 0)

    origem_correta = trecho(
        "Dependência funcional e normalização",
        1,
    )

    origem_recuperada = trecho(
        "Introdução a bancos de dados",
        2,
    )

    resultado = resultado_com([
        CorrespondenciaTrecho(
            trecho_destino=destino,
            trecho_origem=origem_recuperada,
            similaridade=0.7,
            similaridade_lexical=0.2,
        ),
    ])

    avaliacao = avaliar_recuperacao(
        resultado,
        referencias={
            destino: {origem_correta},
        },
    )

    assert avaliacao.total_referencias == 1
    assert avaliacao.referencias_encontradas == 0
    assert avaliacao.revocacao == pytest.approx(0.0)


def test_calcular_recuperacao_parcial():
    destino_a = trecho("Modelo relacional", 0)
    destino_b = trecho("Normalização", 1)

    origem_a = trecho("O modelo relacional", 0)
    origem_b = trecho("Dependência funcional", 1)

    resultado = resultado_com([
        CorrespondenciaTrecho(
            trecho_destino=destino_a,
            trecho_origem=origem_a,
            similaridade=0.95,
        ),
    ])

    avaliacao = avaliar_recuperacao(
        resultado,
        referencias={
            destino_a: {origem_a},
            destino_b: {origem_b},
        },
    )

    assert avaliacao.total_referencias == 2
    assert avaliacao.referencias_encontradas == 1
    assert avaliacao.revocacao == pytest.approx(0.5)


def test_rejeitar_avaliacao_sem_referencias():
    resultado = resultado_com([])

    with pytest.raises(ValueError):
        avaliar_recuperacao(
            resultado,
            referencias={},
        )