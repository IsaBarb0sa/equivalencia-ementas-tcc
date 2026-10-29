from __future__ import annotations

from collections.abc import Callable

from equivalencia_ementas.equivalencia.domain.entities import (
    DisciplinaParaEquivalencia,
    TrechoAcademico,
)

from equivalencia_ementas.equivalencia.application.segmentar_texto import (
    segmentar_texto,
)


def preparar_trechos(
    disciplina: DisciplinaParaEquivalencia,
    contar_tokens: Callable[[str], int],
    limite_tokens: int,
) -> list[TrechoAcademico]:
    """
    Prepara os conteúdos acadêmicos para comparação semântica.

    Mantém a identificação das seções e a ordem dos trechos.
    """

    secoes = {
        "ementa": disciplina.ementa,
        "conteudo_programatico": disciplina.conteudo_programatico,
        "objetivo_geral": disciplina.objetivo_geral,
        "objetivos_especificos": disciplina.objetivos_especificos,
        "objetivos_nao_classificados": (
            disciplina.objetivos_nao_classificados
        ),
        "competencias_habilidades": (
            disciplina.competencias_habilidades
        ),
    }

    resultado = []

    for nome_secao, texto in secoes.items():
        if not texto or not texto.strip():
            continue

        segmentos = segmentar_texto(
            texto=texto,
            contar_tokens=contar_tokens,
            limite_tokens=limite_tokens,
        )

        for indice, segmento in enumerate(segmentos):
            resultado.append(
                TrechoAcademico(
                    secao=nome_secao,
                    indice=indice,
                    texto=segmento,
                    quantidade_tokens=contar_tokens(segmento),
                )
            )

    return resultado