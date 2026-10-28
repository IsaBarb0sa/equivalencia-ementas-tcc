
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session


class SqlAlchemyRecuperacaoSenhaRepository:
    """
    Persistência dos tokens de recuperação de senha.

    Não realiza commit: a transação é controlada
    pelo caso de uso ou pelo endpoint chamador.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def criar(
        self,
        usuario_id: int,
        token_hash: str,
        expira_em: datetime,
    ) -> int:
        """
        Armazena somente o hash do token.
        """

        if usuario_id <= 0:
            raise ValueError("Usuário inválido.")

        if len(token_hash) != 64:
            raise ValueError("Hash do token inválido.")

        if expira_em.tzinfo is None:
            raise ValueError(
                "A expiração deve conter fuso horário."
            )

        # SQL Server DATETIME2 não armazena timezone.
        # Converte explicitamente para UTC sem tzinfo.
        expiracao_utc = expira_em.astimezone(
            timezone.utc
        ).replace(tzinfo=None)

        statement = text("""
            INSERT INTO seguranca.RecuperacaoSenha (
                UsuarioId,
                TokenHash,
                ExpiraEm
            )
            OUTPUT INSERTED.RecuperacaoSenhaId
            VALUES (
                :usuario_id,
                :token_hash,
                :expira_em
            )
        """)

        return self._session.execute(
            statement,
            {
                "usuario_id": usuario_id,
                "token_hash": token_hash,
                "expira_em": expiracao_utc,
            },
        ).scalar_one()

    def consumir(self, token_hash: str) -> int | None:
        """
        Marca atomicamente um token válido como utilizado.

        Retorna o ID do usuário ao qual pertence
        ou None se não existe, expirou ou já foi usado.

        Deve ser executado na mesma transação que
        altera a senha do usuário.
        """

        if len(token_hash) != 64:
            return None

        statement = text("""
            UPDATE seguranca.RecuperacaoSenha
            SET UtilizadoEm = SYSUTCDATETIME()
            OUTPUT INSERTED.UsuarioId
            WHERE TokenHash = :token_hash
              AND UtilizadoEm IS NULL
              AND ExpiraEm > SYSUTCDATETIME()
        """)

        return self._session.execute(
            statement,
            {"token_hash": token_hash},
        ).scalar_one_or_none()

    def invalidar_pendentes(
        self,
        usuario_id: int,
    ) -> None:
        """
        Invalida outros tokens ainda não utilizados.

        Pode ser chamado depois que a senha for
        alterada com sucesso.
        """

        statement = text("""
            UPDATE seguranca.RecuperacaoSenha
            SET UtilizadoEm = SYSUTCDATETIME()
            WHERE UsuarioId = :usuario_id
              AND UtilizadoEm IS NULL
        """)

        self._session.execute(
            statement,
            {"usuario_id": usuario_id},
        )
