from equivalencia_ementas.equivalencia.application.consolidar_evidencias import (
    consolidar_evidencias,
    normalizar_texto_evidencia,
)
from equivalencia_ementas.equivalencia.domain.entities import (
    CorrespondenciaTrecho,
    ResultadoComparacaoTrechos,
    TrechoAcademico,
)


def criar_trecho(
    texto,
    indice=0,
    secao="ementa",
):
    return TrechoAcademico(
        secao=secao,
        indice=indice,
        texto=texto,
        quantidade_tokens=3,
    )


def criar_correspondencia(
    destino,
    origem,
    similaridade,
):
    return CorrespondenciaTrecho(
        trecho_destino=destino,
        trecho_origem=origem,
        similaridade=similaridade,
        similaridade_lexical=0.5,
    )


def criar_resultado(correspondencias):
    return ResultadoComparacaoTrechos(
        modelo="modelo-teste",
        correspondencias=tuple(correspondencias),
        quantidade_trechos_destino=2,
        quantidade_trechos_origem=3,
    )


def test_normalizar_textos_equivalentes():
    assert normalizar_texto_evidencia(
        "  ÁLGEBRA   RELACIONAL. "
    ) == normalizar_texto_evidencia(
        "álgebra relacional"
    )


def test_agrupar_correspondencias_por_destino():
    destino_a = criar_trecho("Modelo Relacional", 0)
    destino_b = criar_trecho("Normalização", 1)

    origem_a = criar_trecho("Modelo de dados", 0)
    origem_b = criar_trecho("Normalização de dados", 1)

    resultado = criar_resultado([
        criar_correspondencia(destino_a, origem_a, 0.9),
        criar_correspondencia(destino_b, origem_b, 0.8),
    ])

    consolidacao = consolidar_evidencias(resultado)

    assert len(consolidacao.topicos) == 2

    assert (
        consolidacao.topicos[0].trecho_destino
        == destino_a
    )

    assert (
        consolidacao.topicos[1].trecho_destino
        == destino_b
    )


def test_identificar_evidencias_repetidas():
    destino = criar_trecho("Álgebra Relacional")

    origem_a = criar_trecho(
        "Álgebra relacional.",
        secao="ementa",
    )

    origem_b = criar_trecho(
        "álgebra relacional",
        secao="conteudo_programatico",
    )

    resultado = criar_resultado([
        criar_correspondencia(destino, origem_a, 0.95),
        criar_correspondencia(destino, origem_b, 0.90),
    ])

    consolidacao = consolidar_evidencias(resultado)

    assert consolidacao.total_correspondencias_originais == 2
    assert consolidacao.total_correspondencias_unicas == 1
    assert consolidacao.total_repeticoes == 1

    assert len(
        consolidacao.topicos[0].correspondencias
    ) == 1


def test_preservar_melhor_pontuacao():
    destino = criar_trecho("Modelo Relacional")

    origem_a = criar_trecho(
        "Modelo relacional.",
        secao="ementa",
    )

    origem_b = criar_trecho(
        "modelo relacional",
        secao="conteudo_programatico",
    )

    resultado = criar_resultado([
        criar_correspondencia(destino, origem_a, 0.80),
        criar_correspondencia(destino, origem_b, 0.95),
    ])

    consolidacao = consolidar_evidencias(resultado)

    correspondencia = (
        consolidacao.topicos[0].correspondencias[0]
    )

    assert correspondencia.similaridade == 0.95
    assert correspondencia.trecho_origem == origem_b


def test_preservar_conteudos_diferentes():
    destino = criar_trecho("Álgebra Relacional")

    origem_a = criar_trecho("Álgebra Relacional")
    origem_b = criar_trecho(
        "Operações da Álgebra Relacional"
    )

    resultado = criar_resultado([
        criar_correspondencia(destino, origem_a, 0.95),
        criar_correspondencia(destino, origem_b, 0.85),
    ])

    consolidacao = consolidar_evidencias(resultado)

    assert consolidacao.total_correspondencias_unicas == 2
    assert consolidacao.total_repeticoes == 0


def test_resultado_sem_correspondencias():
    resultado = criar_resultado([])

    consolidacao = consolidar_evidencias(resultado)

    assert consolidacao.topicos == ()
    assert consolidacao.total_correspondencias_originais == 0
    assert consolidacao.total_correspondencias_unicas == 0
    assert consolidacao.total_repeticoes == 0