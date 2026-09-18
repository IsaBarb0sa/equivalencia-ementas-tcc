import pytest

from equivalencia_ementas.academico.domain.entities import (
    Curso,
    ModalidadeCurso,
    NivelCurso,
)


def test_deve_criar_curso_valido() -> None:
    curso = Curso(
        instituicao_id=1,
        codigo="cc",
        nome="Ciência da Computação",
        nivel=NivelCurso.GRADUACAO,
        modalidade=ModalidadeCurso.PRESENCIAL,
    )

    assert curso.instituicao_id == 1
    assert curso.codigo == "CC"
    assert curso.nome == "Ciência da Computação"
    assert curso.ativo is True


def test_nao_deve_criar_curso_sem_instituicao() -> None:
    with pytest.raises(
        ValueError,
        match="O identificador da instituição deve ser positivo",
    ):
        Curso(
            instituicao_id=0,
            codigo="CC",
            nome="Ciência da Computação",
        )


def test_nao_deve_criar_curso_sem_codigo() -> None:
    with pytest.raises(
        ValueError,
        match="O código do curso é obrigatório",
    ):
        Curso(
            instituicao_id=1,
            codigo=" ",
            nome="Ciência da Computação",
        )
