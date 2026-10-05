from pathlib import Path

from openai import OpenAI

from equivalencia_ementas.infraestrutura.ia.modelos_extracao import (
    DocumentoAcademicoExtraido,
)
from equivalencia_ementas.shared.settings.config import get_settings


INSTRUCOES_EXTRACAO = """
Você é um componente de extração estruturada de documentos acadêmicos.

Sua tarefa é analisar o documento fornecido e identificar disciplinas e
informações acadêmicas presentes nele.

REGRAS OBRIGATÓRIAS:

1. Extraia SOMENTE informações presentes no documento.
2. Não invente, complete, estime ou deduza informações ausentes.
3. Se uma informação não estiver disponível, retorne null ou lista vazia.
4. Preserve uma disciplina mesmo que somente o nome e/ou carga horária
   estejam disponíveis.
5. Um documento pode conter uma única disciplina ou várias disciplinas.
6. Identifique todas as disciplinas encontradas.
7. Não misture informações de disciplinas diferentes.
8. Não confunda histórico escolar, cabeçalhos ou dados administrativos com
   conteúdo da disciplina.
9. Quando existirem carga horária total, teórica e prática, mantenha os
   valores separadamente.
10. Se somente a carga horária total estiver presente, não tente dividir
    entre teórica e prática.
11. Informe as páginas em que os dados de cada disciplina foram encontrados.
12. Preserve o conteúdo acadêmico com o máximo de fidelidade possível.
13. Não resuma ementa ou conteúdo programático desnecessariamente.
14. Se houver bibliografia básica e complementar, mantenha-as separadas.
15. Se não for possível classificar uma bibliografia, use
    bibliografia.nao_classificada.
16. A instituição e o curso devem ser preenchidos somente quando houver
    evidência no documento.
"""


class ExtratorOpenAI:
    def __init__(self) -> None:
        settings = get_settings()

        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY não configurada no arquivo .env."
            )

        self._modelo = settings.openai_model
        self._cliente = OpenAI(api_key=settings.openai_api_key)

    def extrair(self, caminho_pdf: Path) -> DocumentoAcademicoExtraido:
        caminho_pdf = Path(caminho_pdf)

        if not caminho_pdf.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {caminho_pdf}"
            )

        if caminho_pdf.suffix.lower() != ".pdf":
            raise ValueError(
                "A primeira versão do extrator por IA aceita somente PDF."
            )

        with caminho_pdf.open("rb") as arquivo:
            arquivo_enviado = self._cliente.files.create(
                file=arquivo,
                purpose="user_data",
            )

        try:
            resposta = self._cliente.responses.parse(
                model=self._modelo,
                input=[
                    {
                        "role": "system",
                        "content": INSTRUCOES_EXTRACAO,
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_file",
                                "file_id": arquivo_enviado.id,
                                "detail": "high",
                            },
                            {
                                "type": "input_text",
                                "text": (
                                    "Analise este documento acadêmico e "
                                    "extraia todas as disciplinas e campos "
                                    "solicitados."
                                ),
                            },
                        ],
                    },
                ],
                text_format=DocumentoAcademicoExtraido,
            )

            resultado = resposta.output_parsed

            if resultado is None:
                raise RuntimeError(
                    "A API não retornou um resultado estruturado."
                )

            return resultado

        finally:
            self._cliente.files.delete(arquivo_enviado.id)