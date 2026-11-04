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
from equivalencia_ementas.equivalencia.domain.services.similaridade_lexical import (
    calcular_similaridade_lexical,
)


class CompararTrechos:
    """
    Identifica as melhores correspondências para cada
    trecho da disciplina de destino.

    Calcula:
    - Similaridade semântica por embeddings;
    - Similaridade lexical por TF-IDF.

    A ordenação permanece baseada na similaridade
    semântica até a validação do método híbrido.
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
        quantidade_melhores: int = 3,
    ) -> ResultadoComparacaoTrechos:

        if quantidade_melhores < 1:
            raise ValueError(
                "A quantidade de correspondências deve ser positiva."
            )

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

        # A matriz lexical é calculada uma única vez,
        # considerando todos os trechos das duas disciplinas.
        matriz_lexical = calcular_similaridade_lexical(
            textos_destino=[
                trecho.texto
                for trecho in trechos_destino
            ],
            textos_origem=[
                trecho.texto
                for trecho in trechos_origem
            ],
        )

        correspondencias = []

        for indice_destino, (
            trecho_destino,
            vetor_destino,
        ) in enumerate(
            zip(trechos_destino, vetores_destino)
        ):
            candidatas = []

            for indice_origem, (
                trecho_origem,
                vetor_origem,
            ) in enumerate(
                zip(trechos_origem, vetores_origem)
            ):
                pontuacao_semantica = similaridade_cosseno(
                    vetor_destino,
                    vetor_origem,
                )

                pontuacao_lexical = matriz_lexical[
                    indice_destino
                ][indice_origem]

                candidatas.append(
                    CorrespondenciaTrecho(
                        trecho_destino=trecho_destino,
                        trecho_origem=trecho_origem,
                        similaridade=pontuacao_semantica,
                        similaridade_lexical=pontuacao_lexical,
                    )
                )

            candidatas.sort(
                key=lambda item: item.similaridade,
                reverse=True,
            )

            correspondencias.extend(
                candidatas[:quantidade_melhores]
            )

        return ResultadoComparacaoTrechos(
            modelo=self._gerador.nome_modelo,
            correspondencias=tuple(correspondencias),
            quantidade_trechos_destino=len(trechos_destino),
            quantidade_trechos_origem=len(trechos_origem),
        )