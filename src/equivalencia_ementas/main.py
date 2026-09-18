from decimal import Decimal

from equivalencia_ementas.academico.application.commands import (
    CadastrarMatrizCurricularCommand,
    VincularDisciplinaMatrizCommand,
)
from equivalencia_ementas.academico.application.exceptions import (
    CursoNaoEncontradoError,
    DisciplinaJaVinculadaError,
    DisciplinaNaoEncontradaError,
    InstituicoesIncompativeisError,
    MatrizCurricularJaExisteError,
    MatrizCurricularNaoEditavelError,
    MatrizCurricularNaoEncontradaError,
)
from equivalencia_ementas.academico.application.use_cases.cadastrar_matriz_curricular import (
    CadastrarMatrizCurricular,
)
from equivalencia_ementas.academico.application.use_cases.vincular_disciplina_matriz import (
    VincularDisciplinaMatriz,
)
from equivalencia_ementas.academico.domain.entities import (
    NaturezaDisciplina,
)
from equivalencia_ementas.academico.infrastructure.unit_of_work import (
    SqlAlchemyAcademicoUnitOfWork,
)


CURSO_ID = 1
DISCIPLINA_ID = 1


def main() -> None:
    cadastrar_matriz = CadastrarMatrizCurricular(
        SqlAlchemyAcademicoUnitOfWork()
    )

    try:
        matriz_id = cadastrar_matriz.executar(
            CadastrarMatrizCurricularCommand(
                curso_id=CURSO_ID,
                codigo="CC-2026",
                nome="Matriz Ciência da Computação 2026",
                ano_inicio_vigencia=2026,
                semestre_inicio=1,
            )
        )

        print(f"Matriz cadastrada com sucesso. ID: {matriz_id}")

    except MatrizCurricularJaExisteError as error:
        print(f"Matriz não cadastrada: {error}")
        return

    vincular_disciplina = VincularDisciplinaMatriz(
        SqlAlchemyAcademicoUnitOfWork()
    )

    try:
        vinculo_id = vincular_disciplina.executar(
            VincularDisciplinaMatrizCommand(
                matriz_curricular_id=matriz_id,
                disciplina_id=DISCIPLINA_ID,
                periodo_sugerido=3,
                natureza=NaturezaDisciplina.OBRIGATORIA,
                creditos=Decimal("4.00"),
            )
        )

        print(
            f"Disciplina vinculada à matriz. "
            f"ID da associação: {vinculo_id}"
        )

    except (
        CursoNaoEncontradoError,
        DisciplinaNaoEncontradaError,
        DisciplinaJaVinculadaError,
        InstituicoesIncompativeisError,
        MatrizCurricularNaoEncontradaError,
        MatrizCurricularNaoEditavelError,
    ) as error:
        print(f"Não foi possível vincular a disciplina: {error}")


if __name__ == "__main__":
    main()