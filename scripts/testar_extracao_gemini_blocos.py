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
TAMANHO_BLOCO = 15
SOBREPOSICAO = 2


def localizar_pdfs(caminho: Path) -> list[Path]:
    if not caminho.exists():
        raise ValueError(f"Caminho não encontrado: {caminho}")

    if caminho.is_file():
        if caminho.suffix.lower() != ".pdf":
            raise ValueError("O arquivo informado precisa ser um PDF.")

        return [caminho]

    if caminho.is_dir():
        # Somente arquivos diretamente na pasta, sem subpastas.
        arquivos = sorted(
            (
                arquivo
                for arquivo in caminho.iterdir()
                if arquivo.is_file()
                and arquivo.suffix.lower() == ".pdf"
            ),
            key=lambda arquivo: arquivo.name.casefold(),
        )

        if not arquivos:
            raise ValueError(f"Nenhum PDF encontrado em: {caminho}")

        # Evita sobrescrever resultados de nomes equivalentes.
        nomes_saida = [
            f"{arquivo.stem}__gemini.json".casefold()
            for arquivo in arquivos
        ]

        if len(nomes_saida) != len(set(nomes_saida)):
            raise ValueError(
                "Há PDFs que gerariam o mesmo nome de JSON. "
                "Renomeie os arquivos antes de continuar."
            )

        return arquivos

    raise ValueError(f"Caminho inválido: {caminho}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extrai um PDF ou todos os PDFs de uma pasta "
            "com Gemini, utilizando processamento em blocos."
        )
    )

    parser.add_argument(
        "entrada",
        type=Path,
        help="Caminho para um PDF ou uma pasta contendo PDFs.",
    )

    args = parser.parse_args()

    try:
        arquivos = localizar_pdfs(args.entrada)
    except ValueError as erro:
        parser.error(str(erro))

    print()
    print("=" * 70)
    print("EXTRAÇÃO - GEMINI EM BLOCOS")
    print("=" * 70)
    print(f"Documentos encontrados: {len(arquivos)}")

    extrator = ExtratorGemini()

    processador = ProcessadorDocumentoIA(
        extrator=extrator,
        tamanho_bloco=TAMANHO_BLOCO,
        sobreposicao=SOBREPOSICAO,
    )

    PASTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    sucessos: list[Path] = []
    falhas: list[tuple[Path, str]] = []

    for indice, arquivo in enumerate(arquivos, start=1):
        print()
        print("-" * 70)
        print(f"[{indice}/{len(arquivos)}] {arquivo.name}")
        print("-" * 70)

        caminho_resultado = (
            PASTA_RESULTADOS / f"{arquivo.stem}__gemini.json"
        )
        caminho_temporario = caminho_resultado.with_suffix(".json.tmp")

        try:
            resultado = processador.processar(arquivo)

            resultado_normalizado = normalizar_extracao(resultado)

            dados_saida = {
                "arquivo": arquivo.name,
                "modelo": extrator.modelo,
                "tamanho_bloco": TAMANHO_BLOCO,
                "sobreposicao": SOBREPOSICAO,
                "resultado": resultado_normalizado.model_dump(
                    mode="json"
                ),
            }

            # Só substitui o JSON anterior após escrever o novo completo.
            caminho_temporario.write_text(
                json.dumps(
                    dados_saida,
                    ensure_ascii=False,
                    indent=2,
                    allow_nan=False,
                ),
                encoding="utf-8",
            )
            caminho_temporario.replace(caminho_resultado)

            sucessos.append(arquivo)

            print(
                "Disciplinas extraídas: "
                f"{len(resultado_normalizado.disciplinas)}"
            )
            print(f"Resultado salvo em: {caminho_resultado}")

        except Exception as erro:
            mensagem = f"{type(erro).__name__}: {erro}"
            falhas.append((arquivo, mensagem))

            try:
                caminho_temporario.unlink(missing_ok=True)
            except OSError:
                pass

            print(f"ERRO: {mensagem}")

            if caminho_resultado.exists():
                print(
                    "Atenção: existe um JSON de uma execução anterior. "
                    "Ele não foi atualizado nesta tentativa."
                )

            print("Continuando para o próximo documento.")

    print()
    print("=" * 70)
    print("RESUMO DA EXECUÇÃO")
    print("=" * 70)
    print(f"PDFs encontrados: {len(arquivos)}")
    print(f"Processados com sucesso: {len(sucessos)}")
    print(f"Falhas: {len(falhas)}")
    print(f"Pasta dos resultados: {PASTA_RESULTADOS.resolve()}")

    if falhas:
        print()
        print("Documentos com falha:")

        for arquivo, mensagem in falhas:
            print(f"- {arquivo.name}: {mensagem}")

    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())