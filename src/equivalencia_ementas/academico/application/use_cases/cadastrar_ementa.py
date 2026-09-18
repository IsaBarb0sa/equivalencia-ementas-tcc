from equivalencia_ementas.academico.application.commands import (
    CadastrarEmentaCommand,
)
from equivalencia_ementas.academico.application.exceptions import (
    DisciplinaNaoEncontradaError,
    EmentaJaExisteError,
    EmentaMatrizDisciplinaIncompativelError,
    MatrizDisciplinaNaoEncontradaError,
)
from equivalencia_ementas.academico.application.ports import (
    AcademicoUnitOfWork,
)
from equivalencia_ementas.academico.domain.entities import Ementa


class CadastrarEmenta:
    def __init__(self, unit_of_work: AcademicoUnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    def executar(
        self,
        command: CadastrarEmentaCommand,
    ) -> int:
        with self._unit_of_work as uow:
            disciplina = uow.disciplinas.buscar_por_id(command.disciplina_id)

            if disciplina is None:
                raise DisciplinaNaoEncontradaError(
                    f"Disciplina {command.disciplina_id} não encontrada."
                )

            if command.matriz_disciplina_id is not None:
                vinculo = uow.matrizes_disciplinas.buscar_por_id(command.matriz_disciplina_id)

                if vinculo is None:
                    raise MatrizDisciplinaNaoEncontradaError(
                        "Vínculo entre matriz e disciplina "
                        f"{command.matriz_disciplina_id} não encontrado."
                    )

                if vinculo.disciplina_id != command.disciplina_id:
                    raise EmentaMatrizDisciplinaIncompativelError(
                        "O vínculo informado pertence a outra disciplina."
                    )

            ementa = Ementa(
                disciplina_id=command.disciplina_id,
                matriz_disciplina_id=command.matriz_disciplina_id,
                versao=command.versao,
                idioma=command.idioma,
                ano_vigencia=command.ano_vigencia,
                semestre_vigencia=command.semestre_vigencia,
                resumo=command.resumo,
                carga_horaria_declarada=(command.carga_horaria_declarada),
                unidade_carga_horaria=(command.unidade_carga_horaria),
                duracao_hora_aula_minutos=(command.duracao_hora_aula_minutos),
                carga_horaria_normalizada_min=(command.carga_horaria_normalizada_min),
            )

            existente = uow.ementas.buscar_por_identidade(
                disciplina_id=ementa.disciplina_id,
                matriz_disciplina_id=ementa.matriz_disciplina_id,
                versao=ementa.versao,
            )

            if existente is not None:
                raise EmentaJaExisteError(
                    "Já existe uma ementa com essa disciplina, matriz e versão."
                )

            uow.ementas.adicionar(ementa)
            uow.commit()

        if ementa.ementa_id is None:
            raise RuntimeError("O banco não retornou o identificador da ementa.")

        return ementa.ementa_id
