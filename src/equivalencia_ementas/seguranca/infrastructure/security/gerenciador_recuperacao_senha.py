
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class DadosTokenRecuperacao:
    token: str
    token_hash: str
    expira_em: datetime


class GerenciadorRecuperacaoSenha:
    VALIDADE_MINUTOS = 15

    @staticmethod
    def calcular_hash(token: str) -> str:
        return hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

    @classmethod
    def gerar(cls) -> DadosTokenRecuperacao:
        token = secrets.token_urlsafe(32)

        expira_em = datetime.now(
            timezone.utc
        ) + timedelta(minutes=cls.VALIDADE_MINUTOS)

        return DadosTokenRecuperacao(
            token=token,
            token_hash=cls.calcular_hash(token),
            expira_em=expira_em,
        )

    @staticmethod
    def token_valido(token: str | None) -> bool:
        if not isinstance(token, str):
            return False

        if len(token) != 43:
            return False

        return all(
            caractere.isascii()
            and (
                caractere.isalnum()
                or caractere in "-_"
            )
            for caractere in token
        )
