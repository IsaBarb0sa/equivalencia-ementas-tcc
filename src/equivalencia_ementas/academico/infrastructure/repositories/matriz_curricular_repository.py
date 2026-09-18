from sqlalchemy import select
from sqlalchemy.orm import Session

from equivalencia_ementas.academico.domain.entities import (
    MatrizCurricular,
    StatusMatrizCurricular,
)
from equivalencia_ementas.academico.infrastructure.orm.models import (
    MatrizCurricularModel,
)


class SqlAlchemyMatrizCurricularRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def adicionar(self, matriz: MatrizCurricular) -> None:
        model = MatrizCurricularModel(
            curso_id=matriz.curso_id,
            codigo=matriz.codigo,
            nome=matriz.nome,
            ano_inicio_vigencia=matriz.ano_inicio_vigencia,
            semestre_inicio=matriz.semestre_inicio,
            ano_fim_vigencia=matriz.ano_fim_vigencia,
            semestre_fim=matriz.semestre_fim,
            status=matriz.status.value,
        )

        self._session.add(model)
        self._session.flush()

        matriz.atribuir_id(model.matriz_curricular_id)

    def buscar_por_id(
        self,
        matriz_curricular_id: int,
    ) -> MatrizCurricular | None:
        statement = select(MatrizCurricularModel).where(
            MatrizCurricularModel.matriz_curricular_id == matriz_curricular_id
        )

        model = self._session.scalar(statement)

        return self._converter_para_dominio(model)

    def buscar_por_codigo(
        self,
        curso_id: int,
        codigo: str,
    ) -> MatrizCurricular | None:
        statement = select(MatrizCurricularModel).where(
            MatrizCurricularModel.curso_id == curso_id,
            MatrizCurricularModel.codigo == codigo,
        )

        model = self._session.scalar(statement)

        return self._converter_para_dominio(model)

    @staticmethod
    def _converter_para_dominio(
        model: MatrizCurricularModel | None,
    ) -> MatrizCurricular | None:
        if model is None:
            return None

        return MatrizCurricular(
            matriz_curricular_id=model.matriz_curricular_id,
            curso_id=model.curso_id,
            codigo=model.codigo,
            nome=model.nome,
            ano_inicio_vigencia=model.ano_inicio_vigencia,
            semestre_inicio=model.semestre_inicio,
            ano_fim_vigencia=model.ano_fim_vigencia,
            semestre_fim=model.semestre_fim,
            status=StatusMatrizCurricular(model.status),
        )
