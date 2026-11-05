from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from equivalencia_ementas.equivalencia.application.comparar_trechos import (
    CompararTrechos,
)
from equivalencia_ementas.equivalencia.application.preparar_trechos import (
    preparar_trechos,
)
from equivalencia_ementas.equivalencia.domain.entities import (
    DisciplinaParaEquivalencia,
    ResultadoComparacaoTrechos,
)
from equivalencia_ementas.equivalencia.application.consolidar_evidencias import (
    ConsolidacaoEvidencias,
    consolidar_evidencias,
)

@dataclass(frozen=True)
class ComparacaoDisciplinaMatriz:
    indice_matriz: int
    disciplina_destino: DisciplinaParaEquivalencia
    status: str
    resultado: ResultadoComparacaoTrechos | None
    consolidacao: ConsolidacaoEvidencias | None = None


class CompararDisciplinaComMatriz:
    """
    Compara uma disciplina de origem com todas as disciplinas
    fornecidas da matriz curricular de destino.

    Não realiza aprovação acadêmica automática.
    """

    def __init__(
        self,
        comparador: CompararTrechos,
        contar_tokens: Callable[[str], int],
        limite_tokens: int,
    ) -> None:
        if limite_tokens < 1:
            raise ValueError(
                "O limite de tokens deve ser positivo."
            )

        self._comparador = comparador
        self._contar_tokens = contar_tokens
        self._limite_tokens = limite_tokens

    def executar(
        self,
        disciplina_origem: DisciplinaParaEquivalencia,
        disciplinas_matriz: Sequence[DisciplinaParaEquivalencia],
        quantidade_melhores: int = 3,
    ) -> tuple[ComparacaoDisciplinaMatriz, ...]:

        if quantidade_melhores < 1:
            raise ValueError(
                "A quantidade de correspondências deve ser positiva."
            )

        if not disciplinas_matriz:
            return ()

        trechos_origem = preparar_trechos(
            disciplina_origem,
            self._contar_tokens,
            self._limite_tokens,
        )

        comparacoes = []

        for indice, disciplina_destino in enumerate(
            disciplinas_matriz
        ):
            trechos_destino = preparar_trechos(
                disciplina_destino,
                self._contar_tokens,
                self._limite_tokens,
            )

            if not trechos_origem:
                comparacoes.append(
                    ComparacaoDisciplinaMatriz(
                        indice_matriz=indice,
                        disciplina_destino=disciplina_destino,
                        status="origem_sem_conteudo",
                        resultado=None,
                    )
                )
                continue

            if not trechos_destino:
                comparacoes.append(
                    ComparacaoDisciplinaMatriz(
                        indice_matriz=indice,
                        disciplina_destino=disciplina_destino,
                        status="destino_sem_conteudo",
                        resultado=None,
                    )
                )
                continue

            resultado = self._comparador.executar(
                trechos_origem=trechos_origem,
                trechos_destino=trechos_destino,
                quantidade_melhores=quantidade_melhores,
                recuperacao_hibrida=True,
            )

            consolidacao = consolidar_evidencias(
                resultado
            )

            comparacoes.append(
                ComparacaoDisciplinaMatriz(
                    indice_matriz=indice,
                    disciplina_destino=disciplina_destino,
                    status="comparado",
                    resultado=resultado,
                    consolidacao=consolidacao,
                )
            )

        return tuple(comparacoes)