from __future__ import annotations

import hashlib
import json
from pathlib import Path

from equivalencia_ementas.infraestrutura.ia.cliente_openai import (
    ExtratorOpenAI,
    ResultadoOpenAI,
    UsoOpenAI,
    VERSAO_EXTRACAO,
)
from equivalencia_ementas.infraestrutura.ia.modelos_extracao import (
    DocumentoAcademicoExtraido,
)


class ExtracaoComCache:
    def __init__(
        self,
        extrator: ExtratorOpenAI,
        pasta_cache: Path = Path("data/extracoes_ia"),
    ) -> None:
        self._extrator = extrator
        self._pasta_cache = pasta_cache

        self._pasta_cache.mkdir(
            parents=True,
            exist_ok=True,
        )

    def extrair(
        self,
        caminho_pdf: Path,
        forcar: bool = False,
    ) -> ResultadoOpenAI:

        caminho_pdf = Path(caminho_pdf)

        if not caminho_pdf.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {caminho_pdf}"
            )

        hash_arquivo = self._calcular_hash(caminho_pdf)

        identificador_cache = (
            f"{hash_arquivo}"
            f"__{self._extrator.modelo}"
            f"__v{VERSAO_EXTRACAO}"
        )

        caminho_cache = (
                self._pasta_cache
                / f"{identificador_cache}.json"
        )

        if caminho_cache.exists() and not forcar:
            print("Resultado encontrado no cache.")
            print("A API NÃO será chamada novamente.")

            return self._carregar_cache(
                caminho_cache
            )

        print("Documento ainda não processado.")
        print("Chamando OpenAI...")

        resultado = self._extrator.extrair(
            caminho_pdf
        )

        self._salvar_cache(
            caminho_cache=caminho_cache,
            caminho_pdf=caminho_pdf,
            hash_arquivo=hash_arquivo,
            resultado=resultado,
        )

        return resultado

    @staticmethod
    def _calcular_hash(
        caminho_pdf: Path,
    ) -> str:

        sha256 = hashlib.sha256()

        with caminho_pdf.open("rb") as arquivo:
            while bloco := arquivo.read(1024 * 1024):
                sha256.update(bloco)

        return sha256.hexdigest()

    @staticmethod
    def _salvar_cache(
        caminho_cache: Path,
        caminho_pdf: Path,
        hash_arquivo: str,
        resultado: ResultadoOpenAI,
    ) -> None:

        dados = {
            "arquivo": caminho_pdf.name,
            "sha256": hash_arquivo,
            "modelo": resultado.modelo,
            "versao_extracao": resultado.versao_extracao,
            "uso": {
                "input_tokens": resultado.uso.input_tokens,
                "output_tokens": resultado.uso.output_tokens,
                "total_tokens": resultado.uso.total_tokens,
            },
            "resultado": resultado.documento.model_dump(),
        }

        caminho_cache.write_text(
            json.dumps(
                dados,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _carregar_cache(
        caminho_cache: Path,
    ) -> ResultadoOpenAI:

        dados = json.loads(
            caminho_cache.read_text(
                encoding="utf-8"
            )
        )

        documento = (
            DocumentoAcademicoExtraido.model_validate(
                dados["resultado"]
            )
        )

        uso_cache = dados.get("uso", {})

        return ResultadoOpenAI(
            documento=documento,
            uso=UsoOpenAI(
                input_tokens=uso_cache.get(
                    "input_tokens",
                    0,
                ),
                output_tokens=uso_cache.get(
                    "output_tokens",
                    0,
                ),
                total_tokens=uso_cache.get(
                    "total_tokens",
                    0,
                ),
            ),
            modelo=dados.get(
                "modelo",
                "desconhecido",
            ),
            versao_extracao=dados.get(
                "versao_extracao",
                "1",
            ),
        )