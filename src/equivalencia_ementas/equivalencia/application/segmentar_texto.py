from __future__ import annotations

import re
from collections.abc import Callable


class ErroSegmentacao(ValueError):
    pass


def segmentar_texto(
    texto: str,
    contar_tokens: Callable[[str], int],
    limite_tokens: int,
) -> list[str]:
    """
    Divide um texto em trechos que respeitam o limite
    de tokens de um modelo de embeddings.

    Preserva todas as palavras e sua ordem.
    """

    if limite_tokens <= 0:
        raise ErroSegmentacao(
            "O limite de tokens deve ser positivo."
        )

    if not isinstance(texto, str):
        raise ErroSegmentacao(
            "O texto deve ser uma string."
        )

    if not texto.strip():
        return []

    # Padroniza apenas espaços e quebras de linha.
    texto = re.sub(r"\s+", " ", texto).strip()

    palavras = texto.split(" ")

    trechos = []
    atual = []

    for palavra in palavras:
        candidato = " ".join([*atual, palavra])

        if contar_tokens(candidato) <= limite_tokens:
            atual.append(palavra)
            continue

        if atual:
            trechos.append(" ".join(atual))
            atual = []

        if contar_tokens(palavra) > limite_tokens:
            raise ErroSegmentacao(
                "Uma palavra excede o limite de tokens."
            )

        atual.append(palavra)

    if atual:
        trechos.append(" ".join(atual))

    return trechos