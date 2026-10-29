from __future__ import annotations

import math
from collections.abc import Sequence


class ErroSimilaridade(ValueError):
    pass


def similaridade_cosseno(
    vetor_a: Sequence[float],
    vetor_b: Sequence[float],
) -> float:
    """
    Calcula a similaridade de cosseno entre dois vetores.

    Retorna um valor entre -1 e 1.
    """

    if not vetor_a or not vetor_b:
        raise ErroSimilaridade(
            "Os vetores não podem estar vazios."
        )

    if len(vetor_a) != len(vetor_b):
        raise ErroSimilaridade(
            "Os vetores devem possuir a mesma dimensão."
        )

    if not all(
        math.isfinite(valor)
        for valor in (*vetor_a, *vetor_b)
    ):
        raise ErroSimilaridade(
            "Os vetores devem conter somente valores finitos."
        )

    produto_escalar = math.fsum(
        a * b
        for a, b in zip(vetor_a, vetor_b)
    )

    norma_a = math.hypot(*vetor_a)
    norma_b = math.hypot(*vetor_b)

    if norma_a == 0 or norma_b == 0:
        raise ErroSimilaridade(
            "Não é possível comparar um vetor nulo."
        )

    resultado = produto_escalar / (norma_a * norma_b)

    return max(-1.0, min(1.0, resultado))