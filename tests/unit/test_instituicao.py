import pytest

from equivalencia_ementas.academico.domain.entities import Instituicao


def test_deve_criar_instituicao_valida() -> None:
    instituicao = Instituicao(
        codigo="UNIPAC",
        nome="Centro Universitário Presidente Antônio Carlos",
        sigla="unipac",
        cidade="Barbacena",
        uf="mg",
    )

    assert instituicao.nome == (
        "Centro Universitário Presidente Antônio Carlos"
    )
    assert instituicao.sigla == "UNIPAC"
    assert instituicao.uf == "MG"
    assert instituicao.ativa is True
    assert instituicao.instituicao_id is None


def test_nao_deve_aceitar_nome_vazio() -> None:
    with pytest.raises(
        ValueError,
        match="O nome da instituição é obrigatório",
    ):
        Instituicao(nome="   ")


def test_nao_deve_aceitar_uf_invalida() -> None:
    with pytest.raises(
        ValueError,
        match="A UF deve possuir exatamente dois caracteres",
    ):
        Instituicao(
            nome="Instituição de Teste",
            uf="Minas Gerais",
        )


def test_nao_deve_aceitar_cnpj_com_pontuacao() -> None:
    with pytest.raises(
        ValueError,
        match="O CNPJ deve possuir exatamente 14 números",
    ):
        Instituicao(
            nome="Instituição de Teste",
            cnpj="12.345.678/0001-90",
        )


def test_deve_atribuir_id_uma_unica_vez() -> None:
    instituicao = Instituicao(
        nome="Instituição de Teste",
    )

    instituicao.atribuir_id(10)

    assert instituicao.instituicao_id == 10

    with pytest.raises(
        ValueError,
        match="A instituição já possui um identificador",
    ):
        instituicao.atribuir_id(20)