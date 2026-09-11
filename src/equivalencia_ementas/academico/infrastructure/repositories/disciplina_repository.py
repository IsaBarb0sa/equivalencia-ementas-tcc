from sqlalchemy import select
from sqlalchemy.orm import Session

from equivalencia_ementas.academico.domain.entities import Disciplina
from equivalencia_ementas.academico.infrastructure.orm.models import (
    DisciplinaModel,
)


class SqlAlchemyDisciplinaRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def adicionar(self, disciplina: Disciplina) -> None:
        model = DisciplinaModel(
            instituicao_id=disciplina.instituicao_id,
            codigo=disciplina.codigo,
            nome=disciplina.nome,
            nome_normalizado=disciplina.nome_normalizado,
            area_conhecimento=disciplina.area_conhecimento,
            ativa=disciplina.ativa,
        )

        self._session.add(model)
        self._session.flush()

        disciplina.atribuir_id(model.disciplina_id)

    def buscar_por_id(
        self,
        disciplina_id: int,
    ) -> Disciplina | None:
        statement = select(DisciplinaModel).where(
            DisciplinaModel.disciplina_id == disciplina_id
        )

        model = self._session.scalar(statement)

        return self._converter_para_dominio(model)

    def buscar_por_codigo(
        self,
        instituicao_id: int,
        codigo: str,
    ) -> Disciplina | None:
        statement = select(DisciplinaModel).where(
            DisciplinaModel.instituicao_id == instituicao_id,
            DisciplinaModel.codigo == codigo,
        )

        model = self._session.scalar(statement)

        return self._converter_para_dominio(model)

    @staticmethod
    def _converter_para_dominio(
        model: DisciplinaModel | None,
    ) -> Disciplina | None:
        if model is None:
            return None

        return Disciplina(
            disciplina_id=model.disciplina_id,
            instituicao_id=model.instituicao_id,
            codigo=model.codigo,
            nome=model.nome,
            nome_normalizado=model.nome_normalizado,
            area_conhecimento=model.area_conhecimento,
            ativa=model.ativa,
        )