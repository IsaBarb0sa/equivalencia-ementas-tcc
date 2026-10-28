
import re

from datetime import datetime, timedelta, timezone

from equivalencia_ementas.seguranca.infrastructure.security.gerenciador_sessao import (
    GerenciadorSessao,
)


def test_gerar_sessao():
    gerenciador = GerenciadorSessao()

    sessao = gerenciador.gerar()

    assert sessao.token
    assert len(sessao.token) == 43
    assert len(sessao.token_hash) == 64


def test_hash_corresponde_ao_token():
    gerenciador = GerenciadorSessao()

    sessao = gerenciador.gerar()

    assert sessao.token_hash == gerenciador.calcular_hash(
        sessao.token
    )


def test_tokens_sao_diferentes():
    gerenciador = GerenciadorSessao()

    primeira = gerenciador.gerar()
    segunda = gerenciador.gerar()

    assert primeira.token != segunda.token
    assert primeira.token_hash != segunda.token_hash


def test_hash_tem_formato_sha256():
    gerenciador = GerenciadorSessao()

    sessao = gerenciador.gerar()

    assert re.fullmatch(
        r"[0-9a-f]{64}",
        sessao.token_hash,
    )


def test_sessao_expira_em_oito_horas():
    gerenciador = GerenciadorSessao()

    antes = datetime.now(timezone.utc)
    sessao = gerenciador.gerar()
    depois = datetime.now(timezone.utc)

    assert (
        antes + timedelta(hours=8)
        <= sessao.expira_em
        <= depois + timedelta(hours=8)
    )


def test_token_gerado_e_valido():
    gerenciador = GerenciadorSessao()

    sessao = gerenciador.gerar()

    assert gerenciador.token_valido(sessao.token)


def test_rejeitar_token_invalido():
    gerenciador = GerenciadorSessao()

    assert not gerenciador.token_valido(None)
    assert not gerenciador.token_valido("")
    assert not gerenciador.token_valido("abc")
    assert not gerenciador.token_valido("a" * 44)
    assert not gerenciador.token_valido("!" * 43)


def test_expiracao_possui_timezone_utc():
    gerenciador = GerenciadorSessao()

    sessao = gerenciador.gerar()

    assert sessao.expira_em.tzinfo is not None
    assert sessao.expira_em.utcoffset() == timedelta(0)
