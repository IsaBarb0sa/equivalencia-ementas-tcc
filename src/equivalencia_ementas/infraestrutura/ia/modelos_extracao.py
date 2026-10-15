from pydantic import BaseModel, Field
from enum import StrEnum

class CargaHorariaExtraida(BaseModel):
    # Valores totais da disciplina; nunca aulas ou horas por semana.
    total: float | None = Field(default=None, ge=0, allow_inf_nan=False,
        description="Carga total explícita da disciplina. Nunca carga semanal.")
    teorica: float | None = Field(default=None, ge=0, allow_inf_nan=False,
        description="Carga teórica total explícita; não calcular por diferença.")
    pratica: float | None = Field(default=None, ge=0, allow_inf_nan=False,
        description="Carga prática total explícita; não calcular por diferença.")
    unidade: str | None = Field(default=None,
        description="Unidade comum aos valores: HORA, HORA_AULA ou CREDITO, se explícita; caso contrário null. Não converter valores.")


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