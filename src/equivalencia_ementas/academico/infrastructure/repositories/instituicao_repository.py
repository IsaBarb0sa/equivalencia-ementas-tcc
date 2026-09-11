from sqlalchemy import select
from sqlalchemy.orm import Session

from equivalencia_ementas.academico.domain.entities import Instituicao
from equivalencia_ementas.academico.infrastructure.orm.models import (
    InstituicaoModel,
)


class SqlAlchemyInstituicaoRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def adicionar(self, instituicao: Instituicao) -> None:
        model = InstituicaoModel(
            codigo=instituicao.codigo,
            nome=instituicao.nome,
            sigla=instituicao.sigla,
            cnpj=instituicao.cnpj,
            cidade=instituicao.cidade,
            uf=instituicao.uf,
            ativa=instituicao.ativa,
        )

        self._session.add(model)
        self._session.flush()

        instituicao.atribuir_id(model.instituicao_id)

    def buscar_por_id(
        self,
        instituicao_id: int,
    ) -> Instituicao | None:
        statement = select(InstituicaoModel).where(
            InstituicaoModel.instituicao_id == instituicao_id
        )

        model = self._session.scalar(statement)

        return self._converter_para_dominio(model)

    def buscar_por_codigo(
        self,
        codigo: str,
    ) -> Instituicao | None:
        statement = select(InstituicaoModel).where(
            InstituicaoModel.codigo == codigo
        )

        model = self._session.scalar(statement)

        return self._converter_para_dominio(model)

    @staticmethod
    def _converter_para_dominio(
        model: InstituicaoModel | None,
    ) -> Instituicao | None:
        if model is None:
            return None

        return Instituicao(
            instituicao_id=model.instituicao_id,
            codigo=model.codigo,
            nome=model.nome,
            sigla=model.sigla,
            cnpj=model.cnpj,
            cidade=model.cidade,
            uf=model.uf,
            ativa=model.ativa,
        )