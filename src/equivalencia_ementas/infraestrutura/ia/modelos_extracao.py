from pydantic import BaseModel, Field
from enum import StrEnum

class CargaHorariaExtraida(BaseModel):
    total: float | None = Field(
        default=None,
        description=(
            "Carga horária total quando o documento apresenta "
            "apenas um único total."
        ),
    )


    total_hora_aula: float | None = Field(
        default=None,
        description=(
            "Carga horária total expressa explicitamente em horas-aula."
        ),
    )

    total_hora_relogio: float | None = Field(
        default=None,
        description=(
            "Carga horária total expressa explicitamente em horas-relógio."
        ),
    )

    teorica: float | None = Field(
        default=None,
        description=(
            "Carga horária teórica TOTAL da disciplina, "
            "somente quando explicitamente informada."
        ),
    )

    pratica: float | None = Field(
        default=None,
        description=(
            "Carga horária prática TOTAL da disciplina, "
            "somente quando explicitamente informada."
        ),
    )

    teorica_semanal: float | None = Field(
        default=None,
        description=(
            "Quantidade semanal de horas ou aulas teóricas, "
            "somente quando explicitamente apresentada como semanal."
        ),
    )

    pratica_semanal: float | None = Field(
        default=None,
        description=(
            "Quantidade semanal de horas ou aulas práticas, "
            "somente quando explicitamente apresentada como semanal."
        ),
    )

    total_semanal: float | None = Field(
        default=None,
        description=(
            "Carga horária semanal total, somente quando "
            "explicitamente apresentada como semanal."
        ),
    )

    unidade: str | None = Field(
        default=None,
        description=(
            "Unidade usada no campo total, por exemplo "
            "HORA ou HORA_AULA."
        ),
    )

    duracao_hora_aula_minutos: int | None = Field(
        default=None,
        description=(
            "Duração da hora-aula em minutos, somente quando "
            "explicitamente informada."
        ),
    )


class ObjetivosExtraidos(BaseModel):
    geral: str | None = None
    especificos: str | None = None
    nao_classificados: str | None = None


class BibliografiaExtraida(BaseModel):
    basica: str | None = None
    complementar: str | None = None
    nao_classificada: str | None = None


class TipoOcorrenciaDisciplina(StrEnum):
    CURRICULAR = "CURRICULAR"
    HISTORICA = "HISTORICA"
    COMPARATIVA = "COMPARATIVA"
    MENCAO = "MENCAO"
    INDETERMINADA = "INDETERMINADA"

class DisciplinaExtraida(BaseModel):
    nome: str

    tipo_ocorrencia: TipoOcorrenciaDisciplina = (
        TipoOcorrenciaDisciplina.INDETERMINADA
    )

    carga_horaria: CargaHorariaExtraida = Field(
        default_factory=CargaHorariaExtraida
    )

    objetivos: ObjetivosExtraidos = Field(
        default_factory=ObjetivosExtraidos
    )

    competencias_habilidades: str | None = None

    ementa: str | None = None

    conteudo_programatico: str | None = None

    bibliografia: BibliografiaExtraida = Field(
        default_factory=BibliografiaExtraida
    )

    paginas_origem: list[int] = Field(
        default_factory=list,
        description=(
            "Número das páginas do PDF nas quais foram encontradas "
            "informações da disciplina."
        ),
    )

    observacoes: list[str] = Field(
        default_factory=list
    )


class DocumentoAcademicoExtraido(BaseModel):
    instituicao: str | None = Field(
        default=None,
        description="Nome da instituição, somente se identificável no documento."
    )

    curso: str | None = Field(
        default=None,
        description="Nome do curso, somente se identificável no documento."
    )

    disciplinas: list[DisciplinaExtraida] = Field(
        default_factory=list
    )

    observacoes_documento: list[str] = Field(
        default_factory=list
    )