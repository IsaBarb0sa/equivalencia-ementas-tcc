from __future__ import annotations

import argparse
from pathlib import Path

from equivalencia_ementas.equivalencia.application.comparar_disciplina_com_matriz import (
    CompararDisciplinaComMatriz,
)
from equivalencia_ementas.equivalencia.application.comparar_trechos import (
    CompararTrechos,
)
from equivalencia_ementas.equivalencia.application.preparar_ementas import (
    preparar_disciplinas_json,
)
from equivalencia_ementas.equivalencia.infrastructure.ia.sentence_transformer import (
    GeradorSentenceTransformer,
)


def selecionar_disciplina(disciplinas, nome):
    encontradas = [
        disciplina
        for disciplina in disciplinas
        if disciplina.nome.casefold().strip()
        == nome.casefold().strip()
    ]

    if len(encontradas) != 1:
        raise ValueError(
            f"Esperada uma disciplina chamada '{nome}', "
            f"mas foram encontradas {len(encontradas)}."
        )

    return encontradas[0]


def carregar_matriz(pasta: Path):
    if not pasta.is_dir():
        raise ValueError(
            f"Pasta da matriz não encontrada: {pasta}"
        )

    disciplinas = []
    arquivos_processados = 0

    for arquivo in sorted(
        pasta.rglob("*__gemini.json")
    ):
        extraidas = preparar_disciplinas_json(arquivo)

        disciplinas.extend(extraidas)
        arquivos_processados += 1

    return disciplinas, arquivos_processados


def executar(
    arquivo_origem: Path,
    nome_origem: str,
    pasta_matriz: Path,
):
    disciplinas_origem = preparar_disciplinas_json(
        arquivo_origem
    )

    origem = selecionar_disciplina(
        disciplinas_origem,
        nome_origem,
    )

    matriz, quantidade_arquivos = carregar_matriz(
        pasta_matriz
    )

    if not matriz:
        raise ValueError(
            "Nenhuma disciplina foi encontrada na matriz."
        )

    print("\nCOMPARAÇÃO AUTOMÁTICA COM A MATRIZ")
    print("=" * 65)

    print(f"Disciplina de origem: {origem.nome}")
    print(f"Arquivos da matriz: {quantidade_arquivos}")
    print(f"Disciplinas da matriz: {len(matriz)}")

    gerador = GeradorSentenceTransformer()

    comparador = CompararTrechos(gerador)

    caso_de_uso = CompararDisciplinaComMatriz(
        comparador=comparador,
        contar_tokens=gerador.contar_tokens,
        limite_tokens=gerador.limite_tokens,
    )

    resultados = caso_de_uso.executar(
        disciplina_origem=origem,
        disciplinas_matriz=matriz,
        quantidade_melhores=3,
    )

    comparadas = 0
    inconclusivas = 0

    print("\nRESULTADOS POR DISCIPLINA")
    print("=" * 65)

    for item in resultados:
        print(f"\nDisciplina: {item.disciplina_destino.nome}")
        print(f"Status: {item.status}")

        if item.resultado is None:
            inconclusivas += 1
            continue

        comparadas += 1

        correspondencias = item.resultado.correspondencias
        consolidacao = item.consolidacao

        print(
            f"Correspondências recuperadas: "
            f"{len(correspondencias)}"
        )

        if consolidacao is not None:
            print(
                f"Tópicos com candidatos recuperados: "
                f"{len(consolidacao.topicos)}"
            )

            print(
                f"Correspondências únicas: "
                f"{consolidacao.total_correspondencias_unicas}"
            )

            print(
                f"Repetições identificadas: "
                f"{consolidacao.total_repeticoes}"
            )

        # Exibição resumida das evidências com maior
        # similaridade semântica.
        melhores = sorted(
            correspondencias,
            key=lambda correspondencia:
                correspondencia.similaridade,
            reverse=True,
        )[:3]

        for indice, correspondencia in enumerate(
            melhores,
            start=1,
        ):
            print(f"\n  Evidência {indice}")

            print(
                f"  Similaridade semântica: "
                f"{correspondencia.similaridade:.4f}"
            )

            if correspondencia.similaridade_lexical is not None:
                print(
                    f"  Similaridade lexical: "
                    f"{correspondencia.similaridade_lexical:.4f}"
                )

            print(
                f"  Origem: "
                f"{correspondencia.trecho_origem.texto}"
            )

            print(
                f"  Destino: "
                f"{correspondencia.trecho_destino.texto}"
            )

    print("\n" + "=" * 65)
    print("RESUMO")
    print("=" * 65)

    print(f"Disciplinas analisadas: {len(resultados)}")
    print(f"Comparações executadas: {comparadas}")
    print(f"Sem conteúdo suficiente: {inconclusivas}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--origem",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--disciplina-origem",
        required=True,
    )

    parser.add_argument(
        "--pasta-matriz",
        type=Path,
        required=True,
    )

    argumentos = parser.parse_args()

    executar(
        arquivo_origem=argumentos.origem,
        nome_origem=argumentos.disciplina_origem,
        pasta_matriz=argumentos.pasta_matriz,
    )


if __name__ == "__main__":
    main()