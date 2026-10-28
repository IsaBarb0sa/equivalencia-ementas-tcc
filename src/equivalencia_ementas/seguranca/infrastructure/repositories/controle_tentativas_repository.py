
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


class SqlAlchemyControleTentativasRepository:
    """
    Persistência do controle de tentativas de login.

    Uma chave hash representa um identificador ou
    uma origem de autenticação.

    A transação é controlada pela camada chamadora.
    """

    LIMITE_FALHAS = 5
    JANELA_MINUTOS = 15
    BLOQUEIO_MINUTOS = 15

    def __init__(self, session: Session) -> None:
        self._session = session

    def esta_bloqueado(self, chave_hash: str) -> bool:
        statement = text("""
            SELECT CASE
                WHEN BloqueadoAte > SYSUTCDATETIME()
                THEN 1
                ELSE 0
            END
            FROM seguranca.ControleTentativaLogin
            WHERE ChaveHash = :chave_hash
        """)

        resultado = self._session.execute(
            statement,
            {"chave_hash": chave_hash},
        ).scalar_one_or_none()

        return bool(resultado) if resultado is not None else False

    def registrar_falha(self, chave_hash: str) -> None:
        """
        Registra uma tentativa incorreta.

        Reinicia a contagem quando a janela expira.
        Na quinta falha, aplica bloqueio de 15 minutos.

        Deve ser chamado dentro de uma transação.
        """
        self._obter_bloqueio_transacional(chave_hash)

        statement = text("""
            UPDATE seguranca.ControleTentativaLogin
            SET
                QuantidadeFalhas = CASE
                    WHEN JanelaInicio <= DATEADD(
                        MINUTE, -15, SYSUTCDATETIME()
                    )
                    THEN 1
                    ELSE QuantidadeFalhas + 1
                END,

                BloqueadoAte = CASE
                    WHEN JanelaInicio <= DATEADD(
                        MINUTE, -15, SYSUTCDATETIME()
                    )
                    THEN NULL

                    WHEN QuantidadeFalhas + 1 >= 5
                    THEN DATEADD(
                        MINUTE, 15, SYSUTCDATETIME()
                    )

                    ELSE NULL
                END,

                JanelaInicio = CASE
                    WHEN JanelaInicio <= DATEADD(
                        MINUTE, -15, SYSUTCDATETIME()
                    )
                    THEN SYSUTCDATETIME()
                    ELSE JanelaInicio
                END,

                AtualizadoEm = SYSUTCDATETIME()
            WHERE ChaveHash = :chave_hash;

            IF @@ROWCOUNT = 0
            BEGIN
                INSERT INTO seguranca.ControleTentativaLogin (
                    ChaveHash,
                    QuantidadeFalhas,
                    JanelaInicio,
                    BloqueadoAte,
                    AtualizadoEm
                )
                VALUES (
                    :chave_hash,
                    1,
                    SYSUTCDATETIME(),
                    NULL,
                    SYSUTCDATETIME()
                );
            END;
        """)

        self._session.execute(
            statement,
            {"chave_hash": chave_hash},
        )

    def limpar(self, chave_hash: str) -> None:
        """
        Remove falhas após autenticação bem-sucedida.

        Deve ser chamado dentro de uma transação.
        """
        self._obter_bloqueio_transacional(chave_hash)

        self._session.execute(
            text("""
                DELETE FROM seguranca.ControleTentativaLogin
                WHERE ChaveHash = :chave_hash
            """),
            {"chave_hash": chave_hash},
        )

    def _obter_bloqueio_transacional(
        self,
        chave_hash: str,
    ) -> None:
        """
        Serializa alterações na mesma chave.

        Requer uma transação SQL Server ativa,
        que deve ser confirmada pelo chamador.
        """
        resultado = self._session.execute(
            text("""
                DECLARE @resultado INT;

                EXEC @resultado = sys.sp_getapplock
                    @Resource = :recurso,
                    @LockMode = 'Exclusive',
                    @LockOwner = 'Transaction',
                    @LockTimeout = 5000;

                SELECT @resultado;
            """),
            {"recurso": f"login:{chave_hash}"},
        ).scalar_one()

        if resultado < 0:
            raise RuntimeError(
                "Não foi possível adquirir o bloqueio "
                "de controle de tentativas."
            )
