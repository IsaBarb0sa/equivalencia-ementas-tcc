
from decimal import Decimal

import pytest

from equivalencia_ementas.academico.application.use_cases.atualizar_ementa_institucional import (
    AtualizarEmentaInstitucional,
    ConflitoAtualizacaoEmenta,
    DadosAtualizacaoEmenta,
    EmentaNaoEncontrada,
    ErroAtualizacaoEmenta,
)


class RepositorioFalso:

    def __init__(self, resultado="atualizado"):
        self.resultado = resultado
        self.parametros = None

    def atualizar_ementa_coordenador(self, **kwargs):
        self.parametros = kwargs
        return self.resultado


def criar_dados(**alteracoes):
    valores = {
        "matriz_disciplina_id": 3,
        "ementa_id": 3,
        "instituicao_id": 1,
        "coordenador_usuario_id": 3,
        "versao_linha": "0x0000000000017ED6",
        "resumo": "  Conceitos de banco de dados.  ",
        "competencias_habilidades": "  Modelagem de dados.  ",
        "carga_horaria_total": Decimal("80"),
        "carga_horaria_teorica": Decimal("40"),
        "carga_horaria_pratica": Decimal("40"),
    }

    valores.update(alteracoes)

    return DadosAtualizacaoEmenta(**valores)


def test_atualiza_ementa_valida():
    repository = RepositorioFalso()
    caso_de_uso = AtualizarEmentaInstitucional(repository)

    caso_de_uso.executar(criar_dados())

    assert repository.parametros is not None
    assert repository.parametros["resumo"] == (
        "Conceitos de banco de dados."
    )
    assert repository.parametros["carga_horaria_total"] == Decimal("80")


def test_rejeita_versao_invalida():
    repository = RepositorioFalso()

    with pytest.raises(ErroAtualizacaoEmenta):
        AtualizarEmentaInstitucional(repository).executar(
            criar_dados(versao_linha="versao-invalida")
        )

    assert repository.parametros is None


def test_rejeita_carga_negativa():
    repository = RepositorioFalso()

    with pytest.raises(ErroAtualizacaoEmenta):
        AtualizarEmentaInstitucional(repository).executar(
            criar_dados(carga_horaria_total=Decimal("-1"))
        )

    assert repository.parametros is None


def test_rejeita_soma_acima_do_total():
    repository = RepositorioFalso()

    with pytest.raises(
        ErroAtualizacaoEmenta,
        match="não pode ultrapassar",
    ):
        AtualizarEmentaInstitucional(repository).executar(
            criar_dados(
                carga_horaria_total=Decimal("60"),
                carga_horaria_teorica=Decimal("40"),
                carga_horaria_pratica=Decimal("40"),
            )
        )

    assert repository.parametros is None


def test_rejeita_mais_de_duas_casas_decimais():
    repository = RepositorioFalso()

    with pytest.raises(ErroAtualizacaoEmenta):
        AtualizarEmentaInstitucional(repository).executar(
            criar_dados(carga_horaria_total=Decimal("80.123"))
        )


def test_identifica_conflito():
    repository = RepositorioFalso(resultado="conflito")

    with pytest.raises(ConflitoAtualizacaoEmenta):
        AtualizarEmentaInstitucional(repository).executar(
            criar_dados()
        )


def test_identifica_ementa_nao_autorizada():
    repository = RepositorioFalso(resultado="nao_encontrado")

    with pytest.raises(EmentaNaoEncontrada):
        AtualizarEmentaInstitucional(repository).executar(
            criar_dados()
        )


def test_preserva_campos_opcionais_nulos():
    repository = RepositorioFalso()

    AtualizarEmentaInstitucional(repository).executar(
        criar_dados(
            resumo=None,
            competencias_habilidades=None,
            carga_horaria_teorica=None,
            carga_horaria_pratica=None,
        )
    )

    assert repository.parametros["resumo"] is None
    assert repository.parametros["competencias_habilidades"] is None
    assert repository.parametros["carga_horaria_teorica"] is None
    assert repository.parametros["carga_horaria_pratica"] is None
