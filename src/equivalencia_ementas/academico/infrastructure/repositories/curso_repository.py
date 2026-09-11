from sqlalchemy import select
from sqlalchemy.orm import Session

from equivalencia_ementas.academico.domain.entities import (
    Curso,
    ModalidadeCurso,
    NivelCurso,
)
from equivalencia_ementas.academico.infrastructure.orm.models import (
    CursoModel,
)


class SqlAlchemyCursoRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def adicionar(self, curso: Curso) -> None:
        model = CursoModel(
            instituicao_id=curso.instituicao_id,
            codigo=curso.codigo,
            nome=curso.nome,
            nivel=curso.nivel.value,
            modalidade=curso.modalidade.value,
            ativo=curso.ativo,
        )

        self._session.add(model)
        self._session.flush()

        curso.atribuir_id(model.curso_id)

    def buscar_por_id(self, curso_id: int) -> Curso | None:
        statement = select(CursoModel).where(
            CursoModel.curso_id == curso_id
        )

        model = self._session.scalar(statement)

        return self._converter_para_dominio(model)

    def buscar_por_codigo(
        self,
        instituicao_id: int,
        codigo: str,
    ) -> Curso | None:
        statement = select(CursoModel).where(
            CursoModel.instituicao_id == instituicao_id,
            CursoModel.codigo == codigo,
        )

        model = self._session.scalar(statement)

        return self._converter_para_dominio(model)

    @staticmethod
    def _converter_para_dominio(
        model: CursoModel | None,
    ) -> Curso | None:
        if model is None:
            return None

        return Curso(
            curso_id=model.curso_id,
            instituicao_id=model.instituicao_id,
            codigo=model.codigo,
            nome=model.nome,
            nivel=NivelCurso(model.nivel),
            modalidade=ModalidadeCurso(model.modalidade),
            ativo=model.ativo,
        )