from sqlalchemy import text

from equivalencia_ementas.shared.database.engine import engine


def main() -> None:
    with engine.connect() as connection:
        banco = connection.execute(
            text("SELECT DB_NAME()")
        ).scalar_one()

    print("Sistema de Equivalência de Ementas iniciado.")
    print(f"Banco conectado: {banco}")


if __name__ == "__main__":
    main()


from equivalencia_ementas.academico.application.commands import (
    CadastrarCursoCommand,
    CadastrarDisciplinaCommand,
)
from equivalencia_ementas.academico.application.exceptions import (
    CursoJaExisteError,
    DisciplinaJaExisteError,
    InstituicaoNaoEncontradaError,
)
from equivalencia_ementas.academico.application.use_cases.cadastrar_curso import (
    CadastrarCurso,
)
from equivalencia_ementas.academico.application.use_cases.cadastrar_disciplina import (
    CadastrarDisciplina,
)
from equivalencia_ementas.academico.domain.entities import (
    ModalidadeCurso,
    NivelCurso,
)
from equivalencia_ementas.academico.infrastructure.unit_of_work import (
    SqlAlchemyAcademicoUnitOfWork,
)


INSTITUICAO_ID = 1


def cadastrar_curso() -> None:
    caso_de_uso = CadastrarCurso(
        SqlAlchemyAcademicoUnitOfWork()
    )

    command = CadastrarCursoCommand(
        instituicao_id=INSTITUICAO_ID,
        codigo="CC",
        nome="Ciência da Computação",
        nivel=NivelCurso.GRADUACAO,
        modalidade=ModalidadeCurso.PRESENCIAL,
    )

    try:
        curso_id = caso_de_uso.executar(command)
        print(f"Curso cadastrado com sucesso. ID: {curso_id}")

    except CursoJaExisteError as error:
        print(f"Curso não cadastrado: {error}")


def cadastrar_disciplina() -> None:
    caso_de_uso = CadastrarDisciplina(
        SqlAlchemyAcademicoUnitOfWork()
    )

    command = CadastrarDisciplinaCommand(
        instituicao_id=INSTITUICAO_ID,
        codigo="BD001",
        nome="Banco de Dados",
        area_conhecimento="Computação",
    )

    try:
        disciplina_id = caso_de_uso.executar(command)
        print(
            f"Disciplina cadastrada com sucesso. "
            f"ID: {disciplina_id}"
        )

    except DisciplinaJaExisteError as error:
        print(f"Disciplina não cadastrada: {error}")


def main() -> None:
    try:
        cadastrar_curso()
        cadastrar_disciplina()

    except InstituicaoNaoEncontradaError as error:
        print(f"Erro: {error}")


if __name__ == "__main__":
    main()