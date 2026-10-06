import argparse
import json
from pathlib import Path

from equivalencia_ementas.infraestrutura.ia.cliente_openai import (
    ExtratorOpenAI,
)
from equivalencia_ementas.infraestrutura.ia.extracao_com_cache import (
    ExtracaoComCache,
)

from equivalencia_ementas.academico.application.normalizar_extracao import (
    normalizar_extracao,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Teste de extração estruturada de documentos "
            "acadêmicos utilizando OpenAI."
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
    print("TESTE DE EXTRAÇÃO POR IA - OPENAI")
    print("=" * 70)
    print()

    print(f"Arquivo: {args.pdf}")
    print()

    extrator = ExtratorOpenAI()

    servico = ExtracaoComCache(
        extrator=extrator
    )

    resultado = servico.extrair(
        args.pdf
    )

    documento_normalizado = normalizar_extracao(
        resultado.documento
    )

    print()
    print("=" * 70)
    print("RESULTADO CONSOLIDADO")
    print("=" * 70)
    print()

    print(
        json.dumps(
            documento_normalizado.model_dump(),
            ensure_ascii=False,
            indent=2,
        )
    )

    print()
    print("=" * 70)
    print("USO DA API")
    print("=" * 70)

    print(f"Modelo: {resultado.modelo}")
    print(
        f"Tokens de entrada: "
        f"{resultado.uso.input_tokens:,}"
    )
    print(
        f"Tokens de saída: "
        f"{resultado.uso.output_tokens:,}"
    )
    print(
        f"Tokens totais: "
        f"{resultado.uso.total_tokens:,}"
    )


if __name__ == "__main__":
    main()