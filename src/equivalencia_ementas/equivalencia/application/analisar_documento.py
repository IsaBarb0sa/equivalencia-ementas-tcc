"""Compara todas as disciplinas extraídas com uma matriz curricular."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from equivalencia_ementas.equivalencia.application.comparar_disciplina_com_matriz import (
    CompararDisciplinaComMatriz,
)
from equivalencia_ementas.equivalencia.application.triagem_equivalencia import (
    PoliticaTriagem,
    SugestaoEquivalencia,
    sugerir_equivalencia,
)
from equivalencia_ementas.equivalencia.domain.entities import DisciplinaParaEquivalencia


@dataclass(frozen=True)
class AnaliseDisciplinaOrigem:
    disciplina_origem: str
    sugestoes: tuple[SugestaoEquivalencia, ...]


class AnalisarDocumento:
    def __init__(
        self,
        comparador_matriz: CompararDisciplinaComMatriz,
        politica: PoliticaTriagem = PoliticaTriagem(),
    ) -> None:
        self._comparador_matriz = comparador_matriz
        self._politica = politica

    def executar(
        self,
        disciplinas_origem: Sequence[DisciplinaParaEquivalencia],
        disciplinas_matriz: Sequence[DisciplinaParaEquivalencia],
        quantidade_melhores: int = 3,
    ) -> tuple[AnaliseDisciplinaOrigem, ...]:
        resultados = []
        for origem in disciplinas_origem:
            comparacoes = self._comparador_matriz.executar(
                disciplina_origem=origem,
                disciplinas_matriz=disciplinas_matriz,
                quantidade_melhores=quantidade_melhores,
            )
            sugestoes = tuple(
                sugerir_equivalencia(origem, comparacao, self._politica)
                for comparacao in comparacoes
            )
            resultados.append(AnaliseDisciplinaOrigem(origem.nome, sugestoes))
        return tuple(resultados)
