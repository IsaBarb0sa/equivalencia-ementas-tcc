from pydantic import BaseModel, Field


class CargaHorariaExtraida(BaseModel):
    total: float | None = Field(
        default=None,
        description="Carga horária total da disciplina."
    )

    teorica: float | None = Field(
        default=None,
        description="Carga horária teórica, somente se explicitamente informada."
    )

    pratica: float | None = Field(
        default=None,
        description="Carga horária prática, somente se explicitamente informada."
    )

    unidade: str | None = Field(
        default=None,
        description="Unidade da carga horária, por exemplo HORA ou HORA_AULA."
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


class DisciplinaExtraida(BaseModel):
    nome: str = Field(
        description=(
            "Nome da disciplina exatamente como identificado "
            "no documento."
        )
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