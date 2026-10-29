from equivalencia_ementas.equivalencia.domain.entities import (
    CargaHorariaEquivalencia,
    DisciplinaParaEquivalencia,
)


def test_disciplina_com_conteudo_semantico():
    disciplina = DisciplinaParaEquivalencia(
        nome="Banco de Dados",
        ementa="Introdução aos bancos de dados relacionais.",
    )

    assert disciplina.possui_conteudo_semantico()


def test_disciplina_sem_conteudo_semantico():
    disciplina = DisciplinaParaEquivalencia(
        nome="Banco de Dados",
        carga_horaria=CargaHorariaEquivalencia(
            total=80,
        ),
    )

    assert not disciplina.possui_conteudo_semantico()


def test_disciplina_com_conteudo_programatico():
    disciplina = DisciplinaParaEquivalencia(
        nome="Algoritmos",
        conteudo_programatico=(
            "Estruturas de repetição, funções e recursividade."
        ),
    )

    assert disciplina.possui_conteudo_semantico()


def test_campos_opcionais():
    disciplina = DisciplinaParaEquivalencia(
        nome="Matemática Discreta",
    )

    assert disciplina.ementa is None
    assert disciplina.conteudo_programatico is None
    assert disciplina.carga_horaria.total is None


def test_carga_horaria_preservada():
    carga = CargaHorariaEquivalencia(
        total=80,
        teorica=40,
        pratica=40,
        unidade="HORA_AULA",
    )

    disciplina = DisciplinaParaEquivalencia(
        nome="Banco de Dados",
        carga_horaria=carga,
    )

    assert disciplina.carga_horaria.total == 80
    assert disciplina.carga_horaria.teorica == 40
    assert disciplina.carga_horaria.pratica == 40
    assert disciplina.carga_horaria.unidade == "HORA_AULA"


def test_texto_em_branco_nao_e_conteudo():
    disciplina = DisciplinaParaEquivalencia(
        nome="Disciplina de Teste",
        ementa="   ",
        conteudo_programatico="",
    )

    assert not disciplina.possui_conteudo_semantico()