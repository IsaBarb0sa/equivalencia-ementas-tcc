import json
import logging
import time
from pathlib import Path

from google import genai
from google.genai import errors

from equivalencia_ementas.infraestrutura.ia.modelos_extracao import (
    DocumentoAcademicoExtraido,
)
from equivalencia_ementas.shared.settings.config import get_settings


logger = logging.getLogger(__name__)


from equivalencia_ementas.infraestrutura.ia.instrucoes_extracao import (
    INSTRUCOES_EXTRACAO,
)


class ExtratorGemini:
    def __init__(self) -> None:
        settings = get_settings()

        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY não configurada no arquivo .env."
            )

        self._modelo = settings.gemini_model
        self._cliente = genai.Client(
            api_key=settings.gemini_api_key
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

        arquivo = self._cliente.files.upload(
            file=caminho_pdf
        )

        prompt = f"""
{INSTRUCOES_EXTRACAO}

Analise integralmente o documento enviado.

Retorne todas as disciplinas e campos encontrados.
"""

        ultima_excecao = None
        esquema_resposta = DocumentoAcademicoExtraido.model_json_schema()
        # Os defaults locais não devem permitir a omissão de campos na API.
        esquema_resposta["required"] = list(esquema_resposta["properties"])

        for tentativa in range(1, 4):
            try:
                interaction = self._cliente.interactions.create(
                    model=self._modelo,
                    input=[
                        {
                            "type": "document",
                            "uri": arquivo.uri,
                            "mime_type": arquivo.mime_type,
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                    response_format={
                        "type": "text",
                        "mime_type": "application/json",
                        "schema": esquema_resposta,
                    },
                )

                logger.debug("Resposta bruta do Gemini: %s", interaction.output_text)
                dados = json.loads(interaction.output_text)
                if isinstance(dados, dict) and "disciplinas" not in dados:
                    raise ValueError(
                        "Resposta incompleta do Gemini: campo disciplinas ausente."
                    )
                resultado = DocumentoAcademicoExtraido.model_validate(dados)
                if not resultado.disciplinas:
                    logger.warning(
                        "Gemini retornou zero disciplinas para %s (modelo %s). "
                        "Confira o documento e as observações: %s",
                        caminho_pdf,
                        self._modelo,
                        resultado.observacoes_documento,
                    )
                return resultado

            except errors.ServerError as exc:
                ultima_excecao = exc

                if exc.code != 503:
                    raise

                print(
                    f"Gemini indisponível (503). "
                    f"Tentativa {tentativa}/3."
                )

                if tentativa < 3:
                    time.sleep(5 * tentativa)

        raise RuntimeError(
            "O Gemini permaneceu indisponível após 3 tentativas."
        ) from ultima_excecao
