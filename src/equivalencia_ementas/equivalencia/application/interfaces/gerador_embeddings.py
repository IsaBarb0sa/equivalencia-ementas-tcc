from typing import Protocol


class GeradorEmbeddings(Protocol):
    """
    Contrato para modelos que transformam textos
    em representações vetoriais.
    """

    @property
    def nome_modelo(self) -> str:
        ...

    def gerar(
        self,
        textos: list[str],
    ) -> list[list[float]]:
        ...