import argparse
import json
from pathlib import Path

from equivalencia_ementas.academico.application.normalizar_extracao import (
    normalizar_extracao,
)
from equivalencia_ementas.infraestrutura.ia.cliente_gemini import (
    ExtratorGemini,
)
from equivalencia_ementas.infraestrutura.ia.processador_documento import (
    ProcessadorDocumentoIA,
)


PASTA_RESULTADOS = Path("data/resultados_gemini")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Teste de extração de documentos acadêmicos "
            "com Gemini utilizando processamento em blocos."
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
    print("TESTE DE EXTRAÇÃO - GEMINI EM BLOCOS")
    print("=" * 70)
    print()

    print(f"Arquivo: {args.pdf}")
    print()

    extrator = ExtratorGemini()

    processador = ProcessadorDocumentoIA(
        extrator=extrator,
        tamanho_bloco=15,
        sobreposicao=2,
    )

    resultado = processador.processar(
        args.pdf
    )

    resultado_normalizado = normalizar_extracao(
        resultado
    )

    PASTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    caminho_resultado = (
        PASTA_RESULTADOS
        / f"{args.pdf.stem}__gemini.json"
    )

    dados_saida = {
        "arquivo": args.pdf.name,
        "modelo": extrator.modelo,
        "tamanho_bloco": 15,
        "sobreposicao": 2,
        "resultado": resultado_normalizado.model_dump(),
    }

    caminho_resultado.write_text(
        json.dumps(
            dados_saida,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 70)
    print("RESULTADO CONSOLIDADO")
    print("=" * 70)
    print()

    print(
        json.dumps(
            resultado_normalizado.model_dump(),
            ensure_ascii=False,
            indent=2,
        )
    )

    print()
    print(
        f"Resultado salvo em: "
        f"{caminho_resultado}"
    )


if __name__ == "__main__":
    main()