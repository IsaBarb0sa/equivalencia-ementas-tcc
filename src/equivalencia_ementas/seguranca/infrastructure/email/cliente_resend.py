
from __future__ import annotations

import os

import httpx


class ErroEnvioEmail(RuntimeError):
    pass


class ClienteResend:
    URL_API = "https://api.resend.com/emails"

    def __init__(self) -> None:
        self._api_key = os.environ.get(
            "RESEND_API_KEY", ""
        ).strip()

        self._remetente = os.environ.get(
            "EMAIL_REMETENTE", ""
        ).strip()

        if not self._api_key:
            raise RuntimeError(
                "Configure a variável RESEND_API_KEY."
            )

        if not self._remetente:
            raise RuntimeError(
                "Configure a variável EMAIL_REMETENTE."
            )

    def enviar_recuperacao_senha(
        self,
        destinatario: str,
        link: str,
    ) -> None:
        assunto = "Redefinição de senha - Equivalência de Ementas"

        corpo = (
            "Olá!\n\n"
            "Recebemos uma solicitação de redefinição "
            "de senha para sua conta.\n\n"
            "Acesse o link abaixo para criar uma nova senha:\n"
            f"{link}\n\n"
            "Este link expira em 15 minutos e pode "
            "ser utilizado apenas uma vez.\n\n"
            "Se você não solicitou a redefinição, "
            "ignore esta mensagem.\n\n"
            "Equipe Equivalência de Ementas"
        )

        try:
            resposta = httpx.post(
                self.URL_API,
                headers={
                    "Authorization": (
                        f"Bearer {self._api_key}"
                    ),
                    "Content-Type": "application/json",
                    "User-Agent": "equivalencia-ementas-tcc/1.0",
                },
                json={
                    "from": self._remetente,
                    "to": [destinatario],
                    "subject": assunto,
                    "text": corpo,
                },
                timeout=10.0,
            )

            resposta.raise_for_status()

        except httpx.HTTPError as exc:
            # Não expõe chave, link ou token nos logs.
            raise ErroEnvioEmail(
                "Não foi possível enviar o e-mail "
                "de recuperação."
            ) from exc
