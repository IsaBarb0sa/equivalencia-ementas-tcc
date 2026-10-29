from equivalencia_ementas.equivalencia.domain.services.similaridade import (
    similaridade_cosseno,
)
from equivalencia_ementas.equivalencia.infrastructure.ia.sentence_transformer import (
    GeradorSentenceTransformer,
)


def main():
    textos = [
        "Modelagem de bancos de dados relacionais e linguagem SQL.",
        "Modelo relacional, consultas SQL e normalização de dados.",
        "Anatomia humana e funcionamento do sistema cardiovascular.",
    ]

    gerador = GeradorSentenceTransformer()

    print("Carregando modelo:", gerador.nome_modelo)

    vetores = gerador.gerar(textos)

    print("Embeddings gerados:", len(vetores))
    print("Dimensão dos vetores:", len(vetores[0]))

    similaridade_relacionada = similaridade_cosseno(
        vetores[0],
        vetores[1],
    )

    similaridade_diferente = similaridade_cosseno(
        vetores[0],
        vetores[2],
    )

    print()
    print("Textos relacionados:", round(similaridade_relacionada, 4))
    print("Textos diferentes:", round(similaridade_diferente, 4))


if __name__ == "__main__":
    main()