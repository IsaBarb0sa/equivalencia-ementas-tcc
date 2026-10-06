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

VERSAO_EXTRACAO = "2"

@dataclass
class ResultadoOpenAI:
    documento: DocumentoAcademicoExtraido
    uso: UsoOpenAI
    modelo: str
    versao_extracao: str

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
9. Extraia os dados de carga horária exatamente conforme apresentados
   no documento.

10. Quando o documento apresentar apenas uma carga horária total,
    preencha carga_horaria.total e informe sua unidade em
    carga_horaria.unidade.

11. Quando o documento apresentar explicitamente dois totais diferentes,
    um em horas-aula e outro em horas-relógio, não escolha apenas um deles.
    Preencha:
    - total_hora_aula com o valor em horas-aula;
    - total_hora_relogio com o valor em horas-relógio;
    - total como null.

12. Os campos teorica e pratica representam cargas horárias TOTAIS.
    Só os preencha quando o documento informar explicitamente a carga
    horária teórica total ou prática total.

13. Se valores teóricos e práticos representarem distribuição semanal,
    utilize teorica_semanal e pratica_semanal.

14. Não interprete automaticamente valores semanais como cargas totais.

15. Não calcule carga horária total multiplicando valores semanais.

16. Não converta hora-aula em hora-relógio.

17. Não suponha a duração da hora-aula.
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