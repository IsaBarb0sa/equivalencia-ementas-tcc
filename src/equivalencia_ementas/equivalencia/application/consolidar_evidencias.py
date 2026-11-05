from __future__ import annotations

import re
from dataclasses import dataclass

from equivalencia_ementas.equivalencia.domain.entities import (
    CorrespondenciaTrecho,
    ResultadoComparacaoTrechos,
    TrechoAcademico,
)


@dataclass(frozen=True)
class EvidenciasTopico:
    trecho_destino: TrechoAcademico
    correspondencias: tuple[CorrespondenciaTrecho, ...]
    quantidade_originais: int
    quantidade_repetidas: int


@dataclass(frozen=True)
class ConsolidacaoEvidencias:
    topicos: tuple[EvidenciasTopico, ...]
    total_correspondencias_originais: int
    total_correspondencias_unicas: int
    total_repeticoes: int


def normalizar_texto_evidencia(texto: str) -> str:
    """
    Normalização textual mínima para identificar
    repetições de conteúdo.

    Não altera o texto original armazenado.
    """

    texto = texto.casefold().strip()

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    texto = texto.rstrip(".,;:")

    return texto


def consolidar_evidencias(
    resultado: ResultadoComparacaoTrechos,
) -> ConsolidacaoEvidencias:
    """
    Organiza correspondências por tópico de destino
    e identifica repetições textuais na origem.

    Não calcula equivalência acadêmica.
    """

    grupos: dict[
        TrechoAcademico,
        list[CorrespondenciaTrecho],
    ] = {}

    for correspondencia in resultado.correspondencias:
        destino = correspondencia.trecho_destino

        grupos.setdefault(
            destino,
            [],
        ).append(correspondencia)

    topicos = []

    total_originais = 0
    total_unicas = 0
    total_repeticoes = 0

    for trecho_destino, correspondencias in grupos.items():
        quantidade_originais = len(correspondencias)

        # Identificamos conteúdos repetidos pela
        # representação textual normalizada.
        unicas: dict[str, CorrespondenciaTrecho] = {}

        for correspondencia in correspondencias:
            chave = normalizar_texto_evidencia(
                correspondencia.trecho_origem.texto
            )

            existente = unicas.get(chave)

            if (
                existente is None
                or correspondencia.similaridade
                > existente.similaridade
            ):
                unicas[chave] = correspondencia

        selecionadas = sorted(
            unicas.values(),
            key=lambda item: item.similaridade,
            reverse=True,
        )

        quantidade_repetidas = (
            quantidade_originais - len(selecionadas)
        )

        topicos.append(
            EvidenciasTopico(
                trecho_destino=trecho_destino,
                correspondencias=tuple(selecionadas),
                quantidade_originais=quantidade_originais,
                quantidade_repetidas=quantidade_repetidas,
            )
        )

        total_originais += quantidade_originais
        total_unicas += len(selecionadas)
        total_repeticoes += quantidade_repetidas

    return ConsolidacaoEvidencias(
        topicos=tuple(topicos),
        total_correspondencias_originais=total_originais,
        total_correspondencias_unicas=total_unicas,
        total_repeticoes=total_repeticoes,
    )