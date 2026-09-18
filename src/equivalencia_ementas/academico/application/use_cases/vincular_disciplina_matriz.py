from equivalencia_ementas.academico.application.commands import (
    VincularDisciplinaMatrizCommand,
)
from equivalencia_ementas.academico.application.exceptions import (
    CursoNaoEncontradoError,
    DisciplinaJaVinculadaError,
    DisciplinaNaoEncontradaError,
    InstituicoesIncompativeisError,
    MatrizCurricularNaoEditavelError,
    MatrizCurricularNaoEncontradaError,
)
from equivalencia_ementas.academico.application.ports import (
    AcademicoUnitOfWork,
)
from equivalencia_ementas.academico.domain.entities import (
    MatrizDisciplina,
)


class VincularDisciplinaMatriz:
    def __init__(self, unit_of_work: AcademicoUnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    def executar(
        self,
        command: VincularDisciplinaMatrizCommand,
    ) -> int:
        with self._unit_of_work as uow:
            matriz = uow.matrizes_curriculares.buscar_por_id(
                command.matriz_curricular_id
            )

            if matriz is None:
                raise MatrizCurricularNaoEncontradaError(
                    f"Matriz {command.matriz_curricular_id} "
                    f"não encontrada."
                )

            if not matriz.pode_ser_alterada:
                raise MatrizCurricularNaoEditavelError(
                    "Somente matrizes em rascunho podem receber "
                    "novas disciplinas."
                )

            disciplina = uow.disciplinas.buscar_por_id(
                command.disciplina_id
            )

            if disciplina is None:
                raise DisciplinaNaoEncontradaError(
                    f"Disciplina {command.disciplina_id} "
                    f"não encontrada."
                )

            curso = uow.cursos.buscar_por_id(matriz.curso_id)

            if curso is None:
                raise CursoNaoEncontradoError(
                    f"Curso {matriz.curso_id} não encontrado."
                )

            if curso.instituicao_id != disciplina.instituicao_id:
                raise InstituicoesIncompativeisError(
                    "A disciplina e o curso da matriz pertencem "
                    "a instituições diferentes."
                )

            associacao_existente = (
                uow.matrizes_disciplinas.buscar_associacao(
                    matriz_curricular_id=matriz.matriz_curricular_id,
                    disciplina_id=disciplina.disciplina_id,
                )
            )

            if associacao_existente is not None:
                raise DisciplinaJaVinculadaError(
                    f"A disciplina {disciplina.disciplina_id} já "
                    f"está vinculada à matriz "
                    f"{matriz.matriz_curricular_id}."
                )

            matriz_disciplina = MatrizDisciplina(
                matriz_curricular_id=matriz.matriz_curricular_id,
                disciplina_id=disciplina.disciplina_id,
                periodo_sugerido=command.periodo_sugerido,
                natureza=command.natureza,
                creditos=command.creditos,
            )

            uow.matrizes_disciplinas.adicionar(
                matriz_disciplina
            )
            uow.commit()

        if matriz_disciplina.matriz_disciplina_id is None:
            raise RuntimeError(
                "O banco não retornou o identificador da associação."
            )

        return matriz_disciplina.matriz_disciplina_id