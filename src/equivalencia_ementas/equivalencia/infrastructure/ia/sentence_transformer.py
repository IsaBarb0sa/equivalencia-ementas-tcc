from __future__ import annotations

from functools import cached_property


class GeradorSentenceTransformer:
    """
    Implementação local de embeddings utilizando
    a biblioteca Sentence Transformers.
    """

    MODELO_PADRAO = (
        "sentence-transformers/"
        "paraphrase-multilingual-MiniLM-L12-v2"
    )

    def __init__(
        self,
        modelo: str = MODELO_PADRAO,
    ) -> None:
        self._nome_modelo = modelo

    @property
    def nome_modelo(self) -> str:
        return self._nome_modelo

    @cached_property
    def _modelo(self):
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(
            self._nome_modelo,
            device="cpu",
        )

    def gerar(
        self,
        textos: list[str],
    ) -> list[list[float]]:

        if not textos:
            return []

        if any(
            not isinstance(texto, str) or not texto.strip()
            for texto in textos
        ):
            raise ValueError(
                "Todos os textos devem ser strings não vazias."
            )

        vetores = self._modelo.encode(
            textos,
            batch_size=8,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return vetores.tolist()

    @property
    def limite_tokens(self) -> int:
        return int(self._modelo.max_seq_length)

    def contar_tokens(self, texto: str) -> int:
        if not isinstance(texto, str):
            raise TypeError(
                "O texto deve ser uma string."
            )

        tokenizer = self._modelo.tokenizer

        # A segmentação precisa da contagem completa, mesmo acima do limite.
        # Esta etapa apenas conta tokens; não envia a sequência ao modelo.
        tokens = tokenizer.encode(
            texto,
            add_special_tokens=True,
            truncation=False,
            verbose=False,
        )

        return len(tokens)
