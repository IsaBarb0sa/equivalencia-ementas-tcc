from equivalencia_ementas.equivalencia.domain.services.similaridade import (
    similaridade_cosseno,
)
from equivalencia_ementas.equivalencia.infrastructure.ia.sentence_transformer import (
    GeradorSentenceTransformer,
)
from equivalencia_ementas.equivalencia.application.segmentar_texto import (
    segmentar_texto,
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

    texto_longo = (
        "Modelagem de dados, normalização, consultas SQL, "
        "transações e administração de bancos de dados. "
    ) * 30

    trechos = segmentar_texto(
        texto=texto_longo,
        contar_tokens=gerador.contar_tokens,
        limite_tokens=gerador.limite_tokens,
    )

    print("Trechos gerados:", len(trechos))

    for indice, trecho in enumerate(trechos):
        quantidade = gerador.contar_tokens(trecho)

        print(
            f"Trecho {indice + 1}: {quantidade} tokens"
        )

        assert quantidade <= gerador.limite_tokens

    assert " ".join(trechos) == " ".join(
        texto_longo.split()
    )

if __name__ == "__main__":
    main()