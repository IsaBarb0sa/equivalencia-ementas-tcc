
from __future__ import annotations

import hashlib
import hmac

from equivalencia_ementas.seguranca.domain.services.validar_cpf import (
    normalizar_cpf,
)
from equivalencia_ementas.shared.settings.config import get_settings


def gerar_chave_login(identificador: str) -> str:
    """
    Gera uma chave HMAC-SHA256 para controlar
    as tentativas de login sem armazenar CPF/e-mail
    diretamente na tabela de controle.
    """
    segredo = get_settings().login_hmac_secret

    if len(segredo) < 32:
        raise RuntimeError(
            "Configure LOGIN_HMAC_SECRET com um segredo "
            "aleatório de pelo menos 32 caracteres."
        )

    identificador = identificador.strip().lower()

    if "@" in identificador:
        normalizado = identificador
    else:
        normalizado = normalizar_cpf(identificador)

    if not normalizado:
        raise ValueError("Identificador inválido.")

    mensagem = f"login:identificador:{normalizado}"

    return hmac.new(
        segredo.encode("utf-8"),
        mensagem.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
