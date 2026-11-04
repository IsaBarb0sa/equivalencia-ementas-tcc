from __future__ import annotations

import argparse
from pathlib import Path

from equivalencia_ementas.equivalencia.application.comparar_trechos import (
    CompararTrechos,
)
from equivalencia_ementas.equivalencia.application.preparar_ementas import (
    preparar_disciplinas_json,
)
from equivalencia_ementas.equivalencia.application.preparar_trechos import (
    preparar_trechos,
)
from equivalencia_ementas.equivalencia.infrastructure.ia.sentence_transformer import (
    GeradorSentenceTransformer,
)


def selecionar_disciplina(disciplinas, nome):
    correspondencias = [
        disciplina
        for disciplina in disciplinas
        if disciplina.nome.casefold().strip() == nome.casefold().strip()
    ]

    if len(correspondencias) != 1:
        raise ValueError(
            f"Esperada uma disciplina chamada '{nome}', "
            f"mas foram encontradas {len(correspondencias)}."
        )

    return correspondencias[0]


def executar(
    arquivo_origem: Path,
    arquivo_destino: Path,
    nome_origem: str,
    nome_destino: str,
):
    disciplinas_origem = preparar_disciplinas_json(
        arquivo_origem
    )

    disciplinas_destino = preparar_disciplinas_json(
        arquivo_destino
    )

    origem = selecionar_disciplina(
        disciplinas_origem,
        nome_origem,
    )

    destino = selecionar_disciplina(
        disciplinas_destino,
        nome_destino,
    )

    gerador = GeradorSentenceTransformer()

    trechos_origem = preparar_trechos(
        origem,
        gerador.contar_tokens,
        gerador.limite_tokens,
    )

    trechos_destino = preparar_trechos(
        destino,
        gerador.contar_tokens,
        gerador.limite_tokens,
    )

    comparador = CompararTrechos(gerador)

    resultado = comparador.executar(
        trechos_origem=trechos_origem,
        trechos_destino=trechos_destino,
        quantidade_melhores=3,
        recuperacao_hibrida=True,
    )

    print("\nCOMPARAÇÃO HÍBRIDA DE EMENTAS")
    print("=" * 60)

    print(f"Origem: {origem.nome}")
    print(f"Destino: {destino.nome}")
    print(f"Modelo: {resultado.modelo}")

    print(
        f"Trechos da origem: "
        f"{resultado.quantidade_trechos_origem}"
    )

    print(
        f"Trechos do destino: "
        f"{resultado.quantidade_trechos_destino}"
    )

    print("\nMELHORES CORRESPONDÊNCIAS")
    print("=" * 60)

    for indice, correspondencia in enumerate(
        resultado.correspondencias,
        start=1,
    ):
        print(f"\nCorrespondência {indice}")

        print(
            f"Similaridade semântica: "
            f"{correspondencia.similaridade:.4f}"
        )

        if correspondencia.similaridade_lexical is not None:
            print(
                f"Similaridade lexical: "
                f"{correspondencia.similaridade_lexical:.4f}"
            )

        print(
            f"Seção destino: "
            f"{correspondencia.trecho_destino.secao}"
        )

        print(
            f"Texto destino: "
            f"{correspondencia.trecho_destino.texto}"
        )

        print(
            f"Seção origem: "
            f"{correspondencia.trecho_origem.secao}"
        )

        print(
            f"Texto origem: "
            f"{correspondencia.trecho_origem.texto}"
        )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--origem", type=Path, required=True)
    parser.add_argument("--destino", type=Path, required=True)
    parser.add_argument("--disciplina-origem", required=True)
    parser.add_argument("--disciplina-destino", required=True)

    argumentos = parser.parse_args()

    executar(
        arquivo_origem=argumentos.origem,
        arquivo_destino=argumentos.destino,
        nome_origem=argumentos.disciplina_origem,
        nome_destino=argumentos.disciplina_destino,
    )


if __name__ == "__main__":
    main()