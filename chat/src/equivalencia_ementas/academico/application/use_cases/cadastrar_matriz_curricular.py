from equivalencia_ementas.academico.application.commands import (
    CadastrarMatrizCurricularCommand,
)
from equivalencia_ementas.academico.application.exceptions import (
    CursoNaoEncontradoError,
    MatrizCurricularJaExisteError,
)
from equivalencia_ementas.academico.application.ports import (
    AcademicoUnitOfWork,
)
from equivalencia_ementas.academico.domain.entities import (
    MatrizCurricular,
)


class CadastrarMatrizCurricular:
    def __init__(self, unit_of_work: AcademicoUnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    def executar(
        self,
        command: CadastrarMatrizCurricularCommand,
    ) -> int:
        with self._unit_of_work as uow:
            curso = uow.cursos.buscar_por_id(command.curso_id)

            if curso is None:
                raise CursoNaoEncontradoError(f"Curso {command.curso_id} não encontrado.")

            matriz = MatrizCurricular(
                curso_id=command.curso_id,
                codigo=command.codigo,
                nome=command.nome,
                ano_inicio_vigencia=command.ano_inicio_vigencia,
                semestre_inicio=command.semestre_inicio,
                ano_fim_vigencia=command.ano_fim_vigencia,
                semestre_fim=command.semestre_fim,
                status=command.status,
            )

            matriz_existente = uow.matrizes_curriculares.buscar_por_codigo(
                curso_id=matriz.curso_id,
                codigo=matriz.codigo,
            )

            if matriz_existente is not None:
                raise MatrizCurricularJaExisteError(
                    f"Já existe uma matriz com o código "
                    f"'{matriz.codigo}' para o curso {matriz.curso_id}."
                )

            uow.matrizes_curriculares.adicionar(matriz)
            uow.commit()

        if matriz.matriz_curricular_id is None:
            raise RuntimeError("O banco não retornou o identificador da matriz.")

        return matriz.matriz_curricular_id
