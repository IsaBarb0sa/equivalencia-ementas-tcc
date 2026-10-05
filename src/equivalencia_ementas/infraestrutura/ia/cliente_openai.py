import base64
from pathlib import Path

from openai import OpenAI

from equivalencia_ementas.infraestrutura.ia.modelos_extracao import (
    DocumentoAcademicoExtraido,
)
from equivalencia_ementas.shared.settings.config import get_settings


INSTRUCOES_EXTRACAO = """
Você é um componente de extração estruturada de documentos acadêmicos.

Analise integralmente o PDF fornecido e identifique todas as disciplinas
ou componentes curriculares presentes.

Regras obrigatórias:

1. Extraia somente informações explicitamente presentes no documento.
2. Não invente, estime ou complete informações ausentes.
3. Quando uma informação estiver ausente, utilize null.
4. O documento pode possuir uma ou várias disciplinas.
5. Preserve uma disciplina mesmo que possua somente nome e carga horária.
6. Não descarte disciplinas por ausência de ementa, objetivos ou bibliografia.
7. Não misture informações pertencentes a disciplinas diferentes.
8. Extraia, quando disponíveis:
   - nome da disciplina;
   - carga horária;
   - objetivos;
   - competências e habilidades;
   - ementa;
   - conteúdo programático;
   - bibliografia.
9. Diferencie carga horária total, teórica e prática apenas quando isso
   estiver explicitamente informado.
10. Não converta automaticamente hora-aula em hora-relógio.
11. Não suponha a duração da hora-aula.
12. Preserve os textos acadêmicos com fidelidade.
13. Informe as páginas de origem das informações.
14. Instituição e curso somente devem ser preenchidos quando houver
    evidência no documento.
15. É preferível retornar uma disciplina parcialmente preenchida do que
    deixar de retornar uma disciplina existente.
"""


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

        return resultado