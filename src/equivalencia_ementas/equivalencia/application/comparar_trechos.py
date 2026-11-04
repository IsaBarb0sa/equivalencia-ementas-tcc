from __future__ import annotations

from equivalencia_ementas.equivalencia.application.interfaces.gerador_embeddings import (
    GeradorEmbeddings,
)
from equivalencia_ementas.equivalencia.domain.entities import (
    CorrespondenciaTrecho,
    ResultadoComparacaoTrechos,
    TrechoAcademico,
)
from equivalencia_ementas.equivalencia.domain.services.similaridade import (
    similaridade_cosseno,
)


class CompararTrechos:
    """
    Identifica as melhores correspondências semânticas
    para os trechos exigidos pela disciplina de destino.
    """

    def __init__(
        self,
        gerador_embeddings: GeradorEmbeddings,
    ) -> None:
        self._gerador = gerador_embeddings

    def executar(
        self,
        trechos_origem: list[TrechoAcademico],
        trechos_destino: list[TrechoAcademico],
    ) -> ResultadoComparacaoTrechos:

        if not trechos_origem or not trechos_destino:
            return ResultadoComparacaoTrechos(
                modelo=self._gerador.nome_modelo,
                correspondencias=(),
                quantidade_trechos_destino=len(trechos_destino),
                quantidade_trechos_origem=len(trechos_origem),
            )

        todos_trechos = [
            *trechos_destino,
            *trechos_origem,
        ]

        vetores = self._gerador.gerar(
            [trecho.texto for trecho in todos_trechos]
        )

        if len(vetores) != len(todos_trechos):
            raise ValueError(
                "O gerador retornou uma quantidade inválida de embeddings."
            )

        quantidade_destino = len(trechos_destino)

        vetores_destino = vetores[:quantidade_destino]
        vetores_origem = vetores[quantidade_destino:]

        correspondencias = []

        for trecho_destino, vetor_destino in zip(
            trechos_destino,
            vetores_destino,
        ):
            melhor = None

            for trecho_origem, vetor_origem in zip(
                trechos_origem,
                vetores_origem,
            ):
                pontuacao = similaridade_cosseno(
                    vetor_destino,
                    vetor_origem,
                )

                if (
                    melhor is None
                    or pontuacao > melhor.similaridade
                ):
                    melhor = CorrespondenciaTrecho(
                        trecho_destino=trecho_destino,
                        trecho_origem=trecho_origem,
                        similaridade=pontuacao,
                    )

            if melhor is not None:
                correspondencias.append(melhor)

        return ResultadoComparacaoTrechos(
            modelo=self._gerador.nome_modelo,
            correspondencias=tuple(correspondencias),
            quantidade_trechos_destino=len(trechos_destino),
            quantidade_trechos_origem=len(trechos_origem),
        )