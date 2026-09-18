from equivalencia_ementas.academico.application.commands import (
    CadastrarDisciplinaCommand,
)
from equivalencia_ementas.academico.application.exceptions import (
    DisciplinaJaExisteError,
    InstituicaoNaoEncontradaError,
)
from equivalencia_ementas.academico.application.ports import (
    AcademicoUnitOfWork,
)
from equivalencia_ementas.academico.domain.entities import Disciplina


class CadastrarDisciplina:
    def __init__(self, unit_of_work: AcademicoUnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    def executar(
        self,
        command: CadastrarDisciplinaCommand,
    ) -> int:
        with self._unit_of_work as uow:
            instituicao = uow.instituicoes.buscar_por_id(command.instituicao_id)

            if instituicao is None:
                raise InstituicaoNaoEncontradaError(
                    f"Instituição {command.instituicao_id} não encontrada."
                )

            disciplina = Disciplina(
                instituicao_id=command.instituicao_id,
                codigo=command.codigo,
                nome=command.nome,
                area_conhecimento=command.area_conhecimento,
            )

            disciplina_existente = uow.disciplinas.buscar_por_codigo(
                instituicao_id=disciplina.instituicao_id,
                codigo=disciplina.codigo,
            )

            if disciplina_existente is not None:
                raise DisciplinaJaExisteError(
                    f"Já existe uma disciplina com o código "
                    f"'{disciplina.codigo}' na instituição "
                    f"{disciplina.instituicao_id}."
                )

            uow.disciplinas.adicionar(disciplina)
            uow.commit()

        if disciplina.disciplina_id is None:
            raise RuntimeError("O banco não retornou o identificador da disciplina.")

        return disciplina.disciplina_id
