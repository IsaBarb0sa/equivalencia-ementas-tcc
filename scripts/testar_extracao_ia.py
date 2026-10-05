import argparse
import json
from pathlib import Path

from equivalencia_ementas.infraestrutura.ia.cliente_openai import (
    ExtratorOpenAI,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Teste de extração estruturada de documentos "
            "acadêmicos utilizando Gemini."
        )
    )

    parser.add_argument(
        "pdf",
        type=Path,
        help="Caminho para o PDF.",
    )

    args = parser.parse_args()

    print()
    print("=" * 70)
    print("TESTE DE EXTRAÇÃO POR IA - GEMINI")
    print("=" * 70)
    print()

    print(f"Arquivo: {args.pdf}")
    print()

    extrator = ExtratorOpenAI()

    resultado = extrator.extrair(args.pdf)

    print()
    print("=" * 70)
    print("RESULTADO CONSOLIDADO")
    print("=" * 70)
    print()

    print(
        json.dumps(
            resultado.model_dump(),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()