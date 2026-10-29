from equivalencia_ementas.equivalencia.domain.entities import (
    DisciplinaParaEquivalencia,
)

from equivalencia_ementas.equivalencia.application.preparar_trechos import (
    preparar_trechos,
)


def contador_falso(texto: str) -> int:
    return len(texto.split())


def test_preparar_ementa():
    disciplina = DisciplinaParaEquivalencia(
        nome="Disciplina A",
        ementa="Introdução aos conceitos fundamentais.",
    )

    trechos = preparar_trechos(
        disciplina,
        contador_falso,
        10,
    )

    assert len(trechos) == 1
    assert trechos[0].secao == "ementa"
    assert trechos[0].indice == 0
    assert trechos[0].texto == (
        "Introdução aos conceitos fundamentais."
    )


def test_identificar_secoes():
    disciplina = DisciplinaParaEquivalencia(
        nome="Disciplina A",
        ementa="Conteúdo da ementa.",
        conteudo_programatico="Tema um. Tema dois.",
        objetivo_geral="Compreender os conceitos.",
    )

    trechos = preparar_trechos(
        disciplina,
        contador_falso,
        20,
    )

    assert [trecho.secao for trecho in trechos] == [
        "ementa",
        "conteudo_programatico",
        "objetivo_geral",
    ]


def test_dividir_secao_longa():
    disciplina = DisciplinaParaEquivalencia(
        nome="Disciplina A",
        conteudo_programatico=(
            "um dois três quatro cinco seis"
        ),
    )

    trechos = preparar_trechos(
        disciplina,
        contador_falso,
        3,
    )

    assert len(trechos) == 2
    assert trechos[0].indice == 0
    assert trechos[1].indice == 1

    assert trechos[0].texto == "um dois três"
    assert trechos[1].texto == "quatro cinco seis"


def test_ignorar_campos_ausentes():
    disciplina = DisciplinaParaEquivalencia(
        nome="Disciplina A",
    )

    trechos = preparar_trechos(
        disciplina,
        contador_falso,
        10,
    )

    assert trechos == []


def test_preservar_quantidade_tokens():
    disciplina = DisciplinaParaEquivalencia(
        nome="Disciplina A",
        ementa="um dois três",
    )

    trechos = preparar_trechos(
        disciplina,
        contador_falso,
        10,
    )

    assert trechos[0].quantidade_tokens == 3


def test_nao_utilizar_nome_como_conteudo():
    disciplina = DisciplinaParaEquivalencia(
        nome="Banco de Dados",
    )

    trechos = preparar_trechos(
        disciplina,
        contador_falso,
        10,
    )

    assert trechos == []