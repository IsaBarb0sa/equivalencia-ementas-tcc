from sqlalchemy import select
from sqlalchemy.orm import Session

from equivalencia_ementas.academico.domain.entities import (
    MatrizDisciplina,
    NaturezaDisciplina,
)
from equivalencia_ementas.academico.infrastructure.orm.models import (
    MatrizDisciplinaModel,
)


class SqlAlchemyMatrizDisciplinaRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def adicionar(
        self,
        matriz_disciplina: MatrizDisciplina,
    ) -> None:
        model = MatrizDisciplinaModel(
            matriz_curricular_id=(matriz_disciplina.matriz_curricular_id),
            disciplina_id=matriz_disciplina.disciplina_id,
            periodo_sugerido=matriz_disciplina.periodo_sugerido,
            natureza=matriz_disciplina.natureza.value,
            creditos=matriz_disciplina.creditos,
            ativa=matriz_disciplina.ativa,
        )

        self._session.add(model)
        self._session.flush()

        matriz_disciplina.atribuir_id(model.matriz_disciplina_id)

    def buscar_por_id(
        self,
        matriz_disciplina_id: int,
    ) -> MatrizDisciplina | None:
        model = self._session.get(
            MatrizDisciplinaModel,
            matriz_disciplina_id,
        )

        if model is None:
            return None

        return self._converter_para_entidade(model)

    def buscar_associacao(
        self,
        matriz_curricular_id: int,
        disciplina_id: int,
    ) -> MatrizDisciplina | None:
        statement = select(MatrizDisciplinaModel).where(
            MatrizDisciplinaModel.matriz_curricular_id == matriz_curricular_id,
            MatrizDisciplinaModel.disciplina_id == disciplina_id,
        )

        model = self._session.scalar(statement)

        if model is None:
            return None

        return self._converter_para_entidade(model)

    @staticmethod
    def _converter_para_entidade(
        model: MatrizDisciplinaModel,
    ) -> MatrizDisciplina:
        return MatrizDisciplina(
            matriz_disciplina_id=model.matriz_disciplina_id,
            matriz_curricular_id=model.matriz_curricular_id,
            disciplina_id=model.disciplina_id,
            periodo_sugerido=model.periodo_sugerido,
            natureza=NaturezaDisciplina(model.natureza),
            creditos=model.creditos,
            ativa=model.ativa,
        )
