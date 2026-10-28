
from __future__ import annotations

import hashlib
import secrets

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


DURACAO_SESSAO_HORAS = 8
QUANTIDADE_BYTES_TOKEN = 32


@dataclass(frozen=True)
class DadosSessao:
    token: str
    token_hash: str
    expira_em: datetime


class GerenciadorSessao:
    """
    Responsável pela geração e validação estrutural
    dos tokens de autenticação.

    Não acessa o banco de dados.
    """

    def gerar(self) -> DadosSessao:
        token = secrets.token_urlsafe(QUANTIDADE_BYTES_TOKEN)

        token_hash = self.calcular_hash(token)

        expira_em = datetime.now(timezone.utc) + timedelta(
            hours=DURACAO_SESSAO_HORAS
        )

        return DadosSessao(
            token=token,
            token_hash=token_hash,
            expira_em=expira_em,
        )

    @staticmethod
    def calcular_hash(token: str) -> str:
        return hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def token_valido(token: str | None) -> bool:
        if not isinstance(token, str):
            return False

        if len(token) != 43:
            return False

        caracteres_permitidos = (
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789-_"
        )

        return all(
            caractere in caracteres_permitidos
            for caractere in token
        )
