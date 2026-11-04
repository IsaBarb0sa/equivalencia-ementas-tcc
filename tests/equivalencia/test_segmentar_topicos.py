from equivalencia_ementas.equivalencia.application.segmentar_topicos import (
    identificar_topicos,
    segmentar_topicos,
)


def contador_falso(texto):
    return len(texto.split())


def test_conteudo_programatico_por_linhas():
    texto = (
        "Modelo relacional\n"
        "Álgebra relacional\n"
        "Normalização"
    )

    resultado = identificar_topicos(
        texto,
        "conteudo_programatico",
    )

    assert resultado == [
        "Modelo relacional",
        "Álgebra relacional",
        "Normalização",
    ]


def test_objetivos_por_ponto_e_virgula():
    texto = (
        "Compreender conceitos;"
        "Aplicar técnicas;"
        "Desenvolver projetos"
    )

    resultado = identificar_topicos(
        texto,
        "objetivos_especificos",
    )

    assert len(resultado) == 3


def test_ementa_por_frases():
    texto = (
        "Introdução aos bancos de dados. "
        "Modelo relacional. "
        "Linguagem SQL."
    )

    resultado = identificar_topicos(
        texto,
        "ementa",
    )

    assert len(resultado) == 3


def test_topico_longo_respeita_limite():
    texto = "um dois três quatro cinco seis"

    resultado = segmentar_topicos(
        texto,
        "conteudo_programatico",
        contador_falso,
        3,
    )

    assert resultado == [
        "um dois três",
        "quatro cinco seis",
    ]


def test_texto_vazio():
    assert identificar_topicos(
        "",
        "ementa",
    ) == []