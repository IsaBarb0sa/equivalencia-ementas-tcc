import hashlib
import hmac

import pytest

from equivalencia_ementas.seguranca.infrastructure.security.chaves_controle_login import (
    gerar_chave_login,
)
from equivalencia_ementas.shared.settings.config import get_settings


@pytest.fixture(autouse=True)
def configurar_ambiente(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DB_SERVER", "localhost")
    monkeypatch.setenv("DB_NAME", "teste")
    monkeypatch.delenv("LOGIN_HMAC_SECRET", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_carrega_segredo_do_dotenv(tmp_path):
    segredo = "a" * 48
    (tmp_path / ".env").write_text(
        f"LOGIN_HMAC_SECRET={segredo}\n", encoding="utf-8"
    )
    esperado = hmac.new(
        segredo.encode(), b"login:identificador:teste@example.com", hashlib.sha256
    ).hexdigest()

    assert gerar_chave_login(" Teste@Example.com ") == esperado


def test_variavel_do_processo_tem_prioridade(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("LOGIN_HMAC_SECRET=curto\n", encoding="utf-8")
    segredo = "b" * 48
    monkeypatch.setenv("LOGIN_HMAC_SECRET", segredo)

    assert gerar_chave_login("teste@example.com") == hmac.new(
        segredo.encode(), b"login:identificador:teste@example.com", hashlib.sha256
    ).hexdigest()


@pytest.mark.parametrize("segredo", ["", "a" * 31])
def test_rejeita_segredo_ausente_ou_curto(monkeypatch, segredo):
    monkeypatch.setenv("LOGIN_HMAC_SECRET", segredo)

    with pytest.raises(RuntimeError, match="LOGIN_HMAC_SECRET"):
        gerar_chave_login("teste@example.com")
