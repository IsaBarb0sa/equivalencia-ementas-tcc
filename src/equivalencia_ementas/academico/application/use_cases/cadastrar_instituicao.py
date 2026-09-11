from equivalencia_ementas.academico.application.commands import (
    CadastrarInstituicaoCommand,
)
from equivalencia_ementas.academico.application.exceptions import (
    InstituicaoJaExisteError,
)
from equivalencia_ementas.academico.application.ports import (
    AcademicoUnitOfWork,
)
from equivalencia_ementas.academico.domain.entities import Instituicao


class CadastrarInstituicao:
    def __init__(self, unit_of_work: AcademicoUnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    def executar(
        self,
        command: CadastrarInstituicaoCommand,
    ) -> int:
        with self._unit_of_work as uow:
            if command.codigo is not None:
                instituicao_existente = (
                    uow.instituicoes.buscar_por_codigo(command.codigo)
                )

                if instituicao_existente is not None:
                    raise InstituicaoJaExisteError(
                        f"Já existe uma instituição com o código "
                        f"'{command.codigo}'."
                    )

            instituicao = Instituicao(
                nome=command.nome,
                codigo=command.codigo,
                sigla=command.sigla,
                cnpj=command.cnpj,
                cidade=command.cidade,
                uf=command.uf,
            )

            uow.instituicoes.adicionar(instituicao)
            uow.commit()

        if instituicao.instituicao_id is None:
            raise RuntimeError(
                "O banco não retornou o identificador da instituição."
            )

        return instituicao.instituicao_id