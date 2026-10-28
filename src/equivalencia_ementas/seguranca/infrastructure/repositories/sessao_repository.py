
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from equivalencia_ementas.seguranca.domain.entities.usuario import (
    PerfilUsuario,
    Usuario,
)


class SqlAlchemySessaoRepository:

    def __init__(self, session: Session) -> None:
        self._session = session

    def criar(
        self,
        usuario_id: int,
        token_hash: str,
        expira_em: datetime,
    ) -> int:
        # A coluna DATETIME2 armazena UTC sem tzinfo.
        expiracao_utc = expira_em.astimezone(
            timezone.utc
        ).replace(tzinfo=None)

        statement = text("""
            INSERT INTO seguranca.SessaoUsuario (
                UsuarioId,
                TokenHash,
                ExpiraEm
            )
            OUTPUT INSERTED.SessaoUsuarioId
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

    def buscar_usuario_por_token(
        self,
        token_hash: str,
    ) -> Usuario | None:
        statement = text("""
            SELECT
                U.UsuarioId,
                U.NomeCompleto,
                U.Cpf,
                U.Email,
                U.SenhaHash,
                U.Perfil,
                U.Ativo,
                U.EmailVerificado,
                U.CriadoEm
            FROM seguranca.SessaoUsuario S
            INNER JOIN seguranca.Usuario U
                ON U.UsuarioId = S.UsuarioId
            WHERE S.TokenHash = :token_hash
              AND S.RevogadoEm IS NULL
              AND S.ExpiraEm > SYSUTCDATETIME()
              AND U.Ativo = 1
        """)

        registro = self._session.execute(
            statement,
            {"token_hash": token_hash},
        ).mappings().one_or_none()

        if registro is None:
            return None

        return Usuario(
            id=registro["UsuarioId"],
            nome_completo=registro["NomeCompleto"],
            cpf=registro["Cpf"],
            email=registro["Email"],
            senha_hash=registro["SenhaHash"],
            perfil=PerfilUsuario(registro["Perfil"]),
            ativo=bool(registro["Ativo"]),
            email_verificado=bool(registro["EmailVerificado"]),
            criado_em=registro["CriadoEm"],
        )

    def revogar(self, token_hash: str) -> bool:
        statement = text("""
            UPDATE seguranca.SessaoUsuario
            SET RevogadoEm = SYSUTCDATETIME()
            WHERE TokenHash = :token_hash
              AND RevogadoEm IS NULL
              AND ExpiraEm > SYSUTCDATETIME()
        """)

        resultado = self._session.execute(
            statement,
            {"token_hash": token_hash},
        )

        return resultado.rowcount > 0

    def revogar_todas_do_usuario(
        self,
        usuario_id: int,
    ) -> None:
        """
        Encerra todas as sessões ativas do usuário.

        Usado após redefinição de senha.
        A transação é controlada pelo chamador.
        """

        self._session.execute(
            text("""
                UPDATE seguranca.SessaoUsuario
                SET RevogadoEm = SYSUTCDATETIME()
                WHERE UsuarioId = :usuario_id
                  AND RevogadoEm IS NULL
            """),
            {"usuario_id": usuario_id},
        )
