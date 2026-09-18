from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CadastrarInstituicaoCommand:
    nome: str
    codigo: str | None = None
    sigla: str | None = None
    cnpj: str | None = None
    cidade: str | None = None
    uf: str | None = None

from equivalencia_ementas.academico.domain.entities import (
    ModalidadeCurso,
    NaturezaDisciplina,
    NivelCurso,
    NivelCurso,
    StatusMatrizCurricular,
)


@dataclass(frozen=True, slots=True)
class CadastrarCursoCommand:
    instituicao_id: int
    codigo: str
    nome: str
    nivel: NivelCurso = NivelCurso.GRADUACAO
    modalidade: ModalidadeCurso = ModalidadeCurso.PRESENCIAL


@dataclass(frozen=True, slots=True)
class CadastrarDisciplinaCommand:
    instituicao_id: int
    codigo: str
    nome: str
    area_conhecimento: str | None = None

@dataclass(frozen=True, slots=True)
class CadastrarMatrizCurricularCommand:
    curso_id: int
    codigo: str
    nome: str | None = None
    ano_inicio_vigencia: int | None = None
    semestre_inicio: int | None = None
    ano_fim_vigencia: int | None = None
    semestre_fim: int | None = None
    status: StatusMatrizCurricular = (
        StatusMatrizCurricular.RASCUNHO
    )


@dataclass(frozen=True, slots=True)
class VincularDisciplinaMatrizCommand:
    matriz_curricular_id: int
    disciplina_id: int
    periodo_sugerido: int | None = None
    natureza: NaturezaDisciplina = (
        NaturezaDisciplina.OBRIGATORIA
    )
    creditos: Decimal | None = None