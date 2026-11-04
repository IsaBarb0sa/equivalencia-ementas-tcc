from __future__ import annotations

import re

from equivalencia_ementas.equivalencia.application.segmentar_texto import (
    segmentar_texto,
)


def identificar_topicos(
    texto: str,
    secao: str,
) -> list[str]:
    """
    Identifica unidades textuais para análise semântica.

    Não utiliza regras específicas por instituição
    ou nome de disciplina.
    """

    if not texto or not texto.strip():
        return []

    texto = texto.strip()

    if secao == "conteudo_programatico":
        partes = re.split(r"\n+|;", texto)

    elif secao in (
        "objetivos_especificos",
        "objetivos_nao_classificados",
    ):
        partes = re.split(r"\n+|;", texto)

    elif secao == "ementa":
        partes = re.split(r"(?<=[.!?])\s+", texto)

    else:
        partes = [texto]

    return [
        parte.strip()
        for parte in partes
        if parte.strip()
    ]


def segmentar_topicos(
    texto: str,
    secao: str,
    contar_tokens,
    limite_tokens: int,
) -> list[str]:
    """
    Identifica tópicos e respeita o limite do modelo.
    """

    topicos = identificar_topicos(texto, secao)

    resultado = []

    for topico in topicos:
        segmentos = segmentar_texto(
            texto=topico,
            contar_tokens=contar_tokens,
            limite_tokens=limite_tokens,
        )

        resultado.extend(segmentos)

    return resultado