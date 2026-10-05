from types import TracebackType

from sqlalchemy.orm import Session, sessionmaker

from equivalencia_ementas.academico.infrastructure.repositories.curso_repository import (
    SqlAlchemyCursoRepository,
)
from equivalencia_ementas.academico.infrastructure.repositories.disciplina_repository import (
    SqlAlchemyDisciplinaRepository,
)

from equivalencia_ementas.academico.infrastructure.repositories.instituicao_repository import (
    SqlAlchemyInstituicaoRepository,
)
from equivalencia_ementas.shared.database.session import SessionFactory

from equivalencia_ementas.academico.infrastructure.repositories.matriz_curricular_repository import (
    SqlAlchemyMatrizCurricularRepository,
)

from equivalencia_ementas.academico.infrastructure.repositories.matriz_disciplina_repository import (
    SqlAlchemyMatrizDisciplinaRepository,
)

from equivalencia_ementas.academico.infrastructure.repositories.ementa_repository import (
    SqlAlchemyEmentaRepository,
)


class SqlAlchemyAcademicoUnitOfWork:
    def __init__(
        self,
        session_factory: sessionmaker[Session] = SessionFactory,
    ) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self.instituicoes: SqlAlchemyInstituicaoRepository
        self.cursos: SqlAlchemyCursoRepository
        self.disciplinas: SqlAlchemyDisciplinaRepository
        self.matrizes_curriculares: SqlAlchemyMatrizCurricularRepository
        self.matrizes_disciplinas: SqlAlchemyMatrizDisciplinaRepository
        self.ementas: SqlAlchemyEmentaRepository

    def __enter__(self) -> "SqlAlchemyAcademicoUnitOfWork":
        self._session = self._session_factory()

        self.instituicoes = SqlAlchemyInstituicaoRepository(self._session)

        self.cursos = SqlAlchemyCursoRepository(self._session)

        self.disciplinas = SqlAlchemyDisciplinaRepository(self._session)
        self.matrizes_curriculares = SqlAlchemyMatrizCurricularRepository(self._session)

        self.matrizes_disciplinas = SqlAlchemyMatrizDisciplinaRepository(self._session)

        self.ementas = SqlAlchemyEmentaRepository(self._session)

        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._session is None:
            return

        try:
            if exception_type is not None:
                self._session.rollback()
        finally:
            self._session.close()
            self._session = None

    def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("A Unit of Work não foi iniciada.")

        self._session.commit()

    def rollback(self) -> None:
        if self._session is None:
            raise RuntimeError("A Unit of Work não foi iniciada.")

        self._session.rollback()
