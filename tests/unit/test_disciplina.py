import pytest

from equivalencia_ementas.academico.domain.entities import (
    Disciplina,
)


def test_deve_criar_disciplina_valida() -> None:
    disciplina = Disciplina(
        instituicao_id=1,
        codigo="bd001",
        nome="Introdução à Programação",
        area_conhecimento="Computação",
    )

    assert disciplina.codigo == "BD001"
    assert disciplina.nome == "Introdução à Programação"
    assert disciplina.nome_normalizado == "introducao a programacao"
    assert disciplina.ativa is True


def test_nao_deve_criar_disciplina_sem_nome() -> None:
    with pytest.raises(
        ValueError,
        match="O nome da disciplina é obrigatório",
    ):
        Disciplina(
            instituicao_id=1,
            codigo="BD001",
            nome=" ",
        )


def test_nao_deve_criar_disciplina_sem_instituicao() -> None:
    with pytest.raises(
        ValueError,
        match="O identificador da instituição deve ser positivo",
    ):
        Disciplina(
            instituicao_id=0,
            codigo="BD001",
            nome="Banco de Dados",
        )