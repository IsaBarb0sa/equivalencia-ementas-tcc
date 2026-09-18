from sqlalchemy import select
from sqlalchemy.orm import Session

from equivalencia_ementas.academico.domain.entities import (
    Ementa,
    StatusEmenta,
    UnidadeCargaHoraria,
)
from equivalencia_ementas.academico.infrastructure.orm.models import (
    EmentaModel,
)


class SqlAlchemyEmentaRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def adicionar(self, ementa: Ementa) -> None:
        model = EmentaModel(
            disciplina_id=ementa.disciplina_id,
            matriz_disciplina_id=ementa.matriz_disciplina_id,
            documento_fonte_id=ementa.documento_fonte_id,
            versao=ementa.versao,
            idioma=ementa.idioma,
            ano_vigencia=ementa.ano_vigencia,
            semestre_vigencia=ementa.semestre_vigencia,
            resumo=ementa.resumo,
            carga_horaria_declarada=(ementa.carga_horaria_declarada),
            unidade_carga_horaria=(ementa.unidade_carga_horaria.value),
            duracao_hora_aula_minutos=(ementa.duracao_hora_aula_minutos),
            carga_horaria_normalizada_min=(ementa.carga_horaria_normalizada_min),
            status=ementa.status.value,
            confianca_parsing=ementa.confianca_parsing,
            publicada_em=ementa.publicada_em,
        )

        self._session.add(model)
        self._session.flush()

        ementa.atribuir_id(model.ementa_id)

    def buscar_por_id(
        self,
        ementa_id: int,
    ) -> Ementa | None:
        model = self._session.get(
            EmentaModel,
            ementa_id,
        )

        if model is None:
            return None

        return self._converter_para_entidade(model)

    def buscar_por_identidade(
        self,
        disciplina_id: int,
        matriz_disciplina_id: int | None,
        versao: str,
    ) -> Ementa | None:
        condicao_matriz = (
            EmentaModel.matriz_disciplina_id.is_(None)
            if matriz_disciplina_id is None
            else EmentaModel.matriz_disciplina_id == matriz_disciplina_id
        )

        statement = select(EmentaModel).where(
            EmentaModel.disciplina_id == disciplina_id,
            condicao_matriz,
            EmentaModel.versao == versao,
        )

        model = self._session.scalar(statement)

        if model is None:
            return None

        return self._converter_para_entidade(model)

    @staticmethod
    def _converter_para_entidade(
        model: EmentaModel,
    ) -> Ementa:
        return Ementa(
            ementa_id=model.ementa_id,
            disciplina_id=model.disciplina_id,
            matriz_disciplina_id=model.matriz_disciplina_id,
            documento_fonte_id=model.documento_fonte_id,
            versao=model.versao,
            idioma=model.idioma,
            ano_vigencia=model.ano_vigencia,
            semestre_vigencia=model.semestre_vigencia,
            resumo=model.resumo,
            carga_horaria_declarada=(model.carga_horaria_declarada),
            unidade_carga_horaria=UnidadeCargaHoraria(model.unidade_carga_horaria),
            duracao_hora_aula_minutos=(model.duracao_hora_aula_minutos),
            carga_horaria_normalizada_min=(model.carga_horaria_normalizada_min),
            status=StatusEmenta(model.status),
            confianca_parsing=model.confianca_parsing,
            publicada_em=model.publicada_em,
        )
