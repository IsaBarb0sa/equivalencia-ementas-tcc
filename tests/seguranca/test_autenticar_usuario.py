
from dataclasses import replace

import pytest

from equivalencia_ementas.seguranca.application.use_cases.autenticar_usuario import (
    AutenticarUsuario,
    CredenciaisInvalidas,
    DadosLogin,
)
from equivalencia_ementas.seguranca.domain.entities.usuario import (
    PerfilUsuario,
    Usuario,
)


class RepositorioFake:
    def __init__(self):
        self.usuario = Usuario(
            id=1,
            nome_completo="Candidata Teste",
            cpf="52998224725",
            email="candidata.teste@example.com",
            senha_hash="hash_de_teste",
            perfil=PerfilUsuario.CANDIDATO,
            ativo=True,
            email_verificado=False,
        )

    def buscar_por_email(self, email):
        if self.usuario.email == email:
            return self.usuario
        return None

    def buscar_por_cpf(self, cpf):
        if self.usuario.cpf == cpf:
            return self.usuario
        return None


class HashFake:
    def verificar(self, senha, senha_hash):
        return (
            senha == "SenhaTeste@2026"
            and senha_hash == "hash_de_teste"
        )


@pytest.fixture
def ambiente():
    repository = RepositorioFake()
    caso_de_uso = AutenticarUsuario(repository, HashFake())
    return repository, caso_de_uso


def test_login_com_email(ambiente):
    _, caso_de_uso = ambiente

    resultado = caso_de_uso.executar(
        DadosLogin(
            identificador="CANDIDATA.TESTE@EXAMPLE.COM",
            senha="SenhaTeste@2026",
        )
    )

    assert resultado.usuario_id == 1
    assert resultado.perfil == "CANDIDATO"
    assert resultado.email_verificado is False


def test_login_com_cpf_formatado(ambiente):
    _, caso_de_uso = ambiente

    resultado = caso_de_uso.executar(
        DadosLogin(
            identificador="529.982.247-25",
            senha="SenhaTeste@2026",
        )
    )

    assert resultado.usuario_id == 1


def test_login_com_cpf_sem_formatacao(ambiente):
    _, caso_de_uso = ambiente

    resultado = caso_de_uso.executar(
        DadosLogin(
            identificador="52998224725",
            senha="SenhaTeste@2026",
        )
    )

    assert resultado.usuario_id == 1


def test_rejeitar_senha_incorreta(ambiente):
    _, caso_de_uso = ambiente

    with pytest.raises(CredenciaisInvalidas):
        caso_de_uso.executar(
            DadosLogin(
                identificador="candidata.teste@example.com",
                senha="senha_errada",
            )
        )


def test_rejeitar_usuario_inexistente(ambiente):
    _, caso_de_uso = ambiente

    with pytest.raises(CredenciaisInvalidas):
        caso_de_uso.executar(
            DadosLogin(
                identificador="naoexiste@example.com",
                senha="SenhaTeste@2026",
            )
        )


def test_rejeitar_conta_inativa(ambiente):
    repository, caso_de_uso = ambiente

    repository.usuario = replace(
        repository.usuario,
        ativo=False,
    )

    with pytest.raises(CredenciaisInvalidas):
        caso_de_uso.executar(
            DadosLogin(
                identificador="52998224725",
                senha="SenhaTeste@2026",
            )
        )


def test_rejeitar_identificador_vazio(ambiente):
    _, caso_de_uso = ambiente

    with pytest.raises(CredenciaisInvalidas):
        caso_de_uso.executar(
            DadosLogin(
                identificador="",
                senha="SenhaTeste@2026",
            )
        )


def test_rejeitar_cpf_incompleto(ambiente):
    _, caso_de_uso = ambiente

    with pytest.raises(CredenciaisInvalidas):
        caso_de_uso.executar(
            DadosLogin(
                identificador="123",
                senha="SenhaTeste@2026",
            )
        )


def test_rejeitar_senha_vazia(ambiente):
    _, caso_de_uso = ambiente

    with pytest.raises(CredenciaisInvalidas):
        caso_de_uso.executar(
            DadosLogin(
                identificador="52998224725",
                senha="",
            )
        )
