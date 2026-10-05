from equivalencia_ementas.academico.application.commands import (
    CadastrarCursoCommand,
)
from equivalencia_ementas.academico.application.exceptions import (
    CursoJaExisteError,
    InstituicaoNaoEncontradaError,
)
from equivalencia_ementas.academico.application.ports import (
    AcademicoUnitOfWork,
)
from equivalencia_ementas.academico.domain.entities import Curso


class CadastrarCurso:
    def __init__(self, unit_of_work: AcademicoUnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    def executar(self, command: CadastrarCursoCommand) -> int:
        with self._unit_of_work as uow:
            instituicao = uow.instituicoes.buscar_por_id(command.instituicao_id)

            if instituicao is None:
                raise InstituicaoNaoEncontradaError(
                    f"Instituição {command.instituicao_id} não encontrada."
                )

            curso = Curso(
                instituicao_id=command.instituicao_id,
                codigo=command.codigo,
                nome=command.nome,
                nivel=command.nivel,
                modalidade=command.modalidade,
            )

            curso_existente = uow.cursos.buscar_por_codigo(
                instituicao_id=curso.instituicao_id,
                codigo=curso.codigo,
            )

            if curso_existente is not None:
                raise CursoJaExisteError(
                    f"Já existe um curso com o código '{curso.codigo}' "
                    f"na instituição {curso.instituicao_id}."
                )

            uow.cursos.adicionar(curso)
            uow.commit()

        if curso.curso_id is None:
            raise RuntimeError("O banco não retornou o identificador do curso.")

        return curso.curso_id
