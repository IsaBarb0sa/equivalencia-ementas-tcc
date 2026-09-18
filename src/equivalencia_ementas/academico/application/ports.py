from types import TracebackType
from typing import Protocol, Self

from equivalencia_ementas.academico.domain.repositories import (
    CursoRepository,
    DisciplinaRepository,
    InstituicaoRepository,
    MatrizCurricularRepository,
    MatrizDisciplinaRepository,
    EmentaRepository,
)


class AcademicoUnitOfWork(Protocol):
    instituicoes: InstituicaoRepository
    cursos: CursoRepository
    disciplinas: DisciplinaRepository
    matrizes_curriculares: MatrizCurricularRepository
    matrizes_disciplinas: MatrizDisciplinaRepository
    ementas: EmentaRepository

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
