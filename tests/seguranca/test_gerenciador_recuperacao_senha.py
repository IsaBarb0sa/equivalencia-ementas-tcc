
from datetime import datetime, timedelta, timezone

from equivalencia_ementas.seguranca.infrastructure.security.gerenciador_recuperacao_senha import (
    GerenciadorRecuperacaoSenha,
)


def test_gera_token_valido():
    dados = GerenciadorRecuperacaoSenha.gerar()

    assert GerenciadorRecuperacaoSenha.token_valido(
        dados.token
    )
    assert len(dados.token_hash) == 64


def test_gera_tokens_diferentes():
    primeiro = GerenciadorRecuperacaoSenha.gerar()
    segundo = GerenciadorRecuperacaoSenha.gerar()

    assert primeiro.token != segundo.token
    assert primeiro.token_hash != segundo.token_hash


def test_hash_corresponde_ao_token():
    dados = GerenciadorRecuperacaoSenha.gerar()

    assert dados.token_hash == (
        GerenciadorRecuperacaoSenha.calcular_hash(
            dados.token
        )
    )
    assert dados.token_hash != dados.token


def test_token_expira_em_aproximadamente_15_minutos():
    antes = datetime.now(timezone.utc)
    dados = GerenciadorRecuperacaoSenha.gerar()
    depois = datetime.now(timezone.utc)

    assert (
        antes + timedelta(minutes=15)
        <= dados.expira_em
        <= depois + timedelta(minutes=15)
    )


def test_rejeita_tokens_invalidos():
    invalidos = [
        None,
        "",
        "token-curto",
        "a" * 44,
        "a" * 42 + "!",
        "á" * 43,
    ]

    for token in invalidos:
        assert not GerenciadorRecuperacaoSenha.token_valido(
            token
        )
