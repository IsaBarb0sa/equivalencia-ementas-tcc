from dataclasses import dataclass


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
    NivelCurso,
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