import base64
from pathlib import Path

from openai import OpenAI

from equivalencia_ementas.shared.settings.config import get_settings

from dataclasses import dataclass

from equivalencia_ementas.infraestrutura.ia.modelos_extracao import (
    DocumentoAcademicoExtraido,
)


@dataclass
class UsoOpenAI:
    input_tokens: int
    output_tokens: int
    total_tokens: int

VERSAO_EXTRACAO = "3"

@dataclass
class ResultadoOpenAI:
    documento: DocumentoAcademicoExtraido
    uso: UsoOpenAI
    modelo: str
    versao_extracao: str

from equivalencia_ementas.infraestrutura.ia.instrucoes_extracao import (
    INSTRUCOES_EXTRACAO,
)


class ExtratorOpenAI:
    def __init__(self) -> None:
        settings = get_settings()

        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY não configurada no arquivo .env."
            )

        self._modelo = settings.openai_model

        self._cliente = OpenAI(
            api_key=settings.openai_api_key
        )

    @property
    def modelo(self) -> str:
        return self._modelo

    def extrair(
        self,
        caminho_pdf: Path,
    ) -> DocumentoAcademicoExtraido:

        caminho_pdf = Path(caminho_pdf)

        if not caminho_pdf.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {caminho_pdf}"
            )

        if caminho_pdf.suffix.lower() != ".pdf":
            raise ValueError(
                "O extrator aceita apenas arquivos PDF."
            )

        with caminho_pdf.open("rb") as arquivo:
            pdf_base64 = base64.b64encode(
                arquivo.read()
            ).decode("utf-8")

        resposta = self._cliente.responses.parse(
            model=self._modelo,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "filename": caminho_pdf.name,
                            "file_data": (
                                "data:application/pdf;base64,"
                                f"{pdf_base64}"
                            ),
                            "detail": "low",
                        },
                        {
                            "type": "input_text",
                            "text": INSTRUCOES_EXTRACAO,
                        },
                    ],
                }
            ],
            text_format=DocumentoAcademicoExtraido,
        )

        resultado = resposta.output_parsed

        if resultado is None:
            raise RuntimeError(
                "A OpenAI não retornou um resultado estruturado."
            )

        uso = resposta.usage

        return ResultadoOpenAI(
            documento=resultado,
            uso=UsoOpenAI(
                input_tokens=uso.input_tokens if uso else 0,
                output_tokens=uso.output_tokens if uso else 0,
                total_tokens=uso.total_tokens if uso else 0,
            ),
            modelo=self._modelo,
            versao_extracao=VERSAO_EXTRACAO,
        )