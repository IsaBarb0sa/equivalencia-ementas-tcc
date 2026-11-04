from pathlib import Path

from equivalencia_ementas.equivalencia.application.preparar_ementas import (
    preparar_disciplinas_json,
)


def main():
    pasta = Path("data")

    arquivos = sorted(
        pasta.rglob("*__gemini.json")
    )

    total_disciplinas = 0

    for arquivo in arquivos:
        print("\n" + "=" * 70)
        print(f"ARQUIVO: {arquivo}")
        print("=" * 70)

        try:
            disciplinas = preparar_disciplinas_json(arquivo)

        except (ValueError, KeyError, TypeError, OSError) as erro:
            print(f"Erro ao carregar: {erro}")
            continue

        print(f"Disciplinas encontradas: {len(disciplinas)}")

        total_disciplinas += len(disciplinas)

        for indice, disciplina in enumerate(
            disciplinas,
            start=1,
        ):
            print(f"{indice:3}. {disciplina.nome}")

    print("\n" + "=" * 70)
    print(f"Total de arquivos: {len(arquivos)}")
    print(f"Total de disciplinas extraídas: {total_disciplinas}")
    print("=" * 70)


if __name__ == "__main__":
    main()