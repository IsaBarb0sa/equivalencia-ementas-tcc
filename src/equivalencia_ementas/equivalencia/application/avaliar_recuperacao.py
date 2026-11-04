from __future__ import annotations

from dataclasses import dataclass

from equivalencia_ementas.equivalencia.domain.entities import (
    ResultadoComparacaoTrechos,
    TrechoAcademico,
)


@dataclass(frozen=True)
class AvaliacaoRecuperacao:
    total_referencias: int
    referencias_encontradas: int
    total_candidatos_recuperados: int
    revocacao: float


def avaliar_recuperacao(
    resultado: ResultadoComparacaoTrechos,
    referencias: dict[TrechoAcademico, set[TrechoAcademico]],
) -> AvaliacaoRecuperacao:
    """
    Mede quantas correspondências de referência foram recuperadas.

    As referências representam pares de trechos previamente
    identificados como relevantes por avaliação humana.

    Não interpreta pontuações como aprovação acadêmica.
    """

    total_referencias = sum(
        len(origens)
        for origens in referencias.values()
    )

    if total_referencias == 0:
        raise ValueError(
            "É necessário informar ao menos uma correspondência "
            "de referência para realizar a avaliação."
        )

    pares_recuperados = {
        (
            correspondencia.trecho_destino,
            correspondencia.trecho_origem,
        )
        for correspondencia in resultado.correspondencias
    }

    referencias_encontradas = sum(
        1
        for trecho_destino, origens in referencias.items()
        for trecho_origem in origens
        if (
            trecho_destino,
            trecho_origem,
        ) in pares_recuperados
    )

    revocacao = referencias_encontradas / total_referencias

    return AvaliacaoRecuperacao(
        total_referencias=total_referencias,
        referencias_encontradas=referencias_encontradas,
        total_candidatos_recuperados=len(pares_recuperados),
        revocacao=revocacao,
    )