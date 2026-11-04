from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calcular_similaridade_lexical(
    textos_destino: list[str],
    textos_origem: list[str],
) -> list[list[float]]:
    """
    Calcula a similaridade lexical entre os trechos
    de destino e de origem utilizando TF-IDF.

    Retorna uma matriz em que:
    - cada linha representa um trecho de destino;
    - cada coluna representa um trecho de origem.
    """

    if not textos_destino:
        return []

    if not textos_origem:
        return [[] for _ in textos_destino]

    todos_textos = [
        *textos_destino,
        *textos_origem,
    ]

    if not any(texto.strip() for texto in todos_textos):
        return [
            [0.0] * len(textos_origem)
            for _ in textos_destino
        ]

    vetorizador = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        lowercase=True,
        strip_accents="unicode",
    )

    matriz = vetorizador.fit_transform(todos_textos)

    quantidade_destino = len(textos_destino)

    vetores_destino = matriz[:quantidade_destino]
    vetores_origem = matriz[quantidade_destino:]

    similaridades = cosine_similarity(
        vetores_destino,
        vetores_origem,
    )

    return similaridades.tolist()