
from sqlalchemy import text
from sqlalchemy.orm import Session

from equivalencia_ementas.seguranca.domain.entities.usuario import (
    PerfilUsuario,
    Usuario,
)


class SqlAlchemyUsuarioRepository:

    def __init__(self, session: Session) -> None:
        self._session = session

    def buscar_por_email(self, email: str) -> Usuario | None:
        statement = text("""
            SELECT
                UsuarioId,
                NomeCompleto,
                Cpf,
                Email,
                SenhaHash,
                Perfil,
                Ativo,
                EmailVerificado,
                CriadoEm
            FROM seguranca.Usuario
            WHERE EmailNormalizado = :email
        """)

        registro = self._session.execute(
            statement,
            {"email": email.strip().lower()},
        ).mappings().one_or_none()

        return self._converter_usuario(registro)

    def buscar_por_cpf(self, cpf: str) -> Usuario | None:
        statement = text("""
            SELECT
                UsuarioId,
                NomeCompleto,
                Cpf,
                Email,
                SenhaHash,
                Perfil,
                Ativo,
                EmailVerificado,
                CriadoEm
            FROM seguranca.Usuario
            WHERE Cpf = :cpf
        """)

        registro = self._session.execute(
            statement,
            {"cpf": cpf},
        ).mappings().one_or_none()

        return self._converter_usuario(registro)

    def buscar_por_id(self, usuario_id: int) -> Usuario | None:
        statement = text("""
            SELECT
                UsuarioId,
                NomeCompleto,
                Cpf,
                Email,
                SenhaHash,
                Perfil,
                Ativo,
                EmailVerificado,
                CriadoEm
            FROM seguranca.Usuario
            WHERE UsuarioId = :usuario_id
        """)

        registro = self._session.execute(
            statement,
            {"usuario_id": usuario_id},
        ).mappings().one_or_none()

        return self._converter_usuario(registro)

    def criar(self, usuario: Usuario) -> int:
        statement = text("""
            INSERT INTO seguranca.Usuario (
                NomeCompleto,
                Cpf,
                Email,
                SenhaHash,
                Perfil,
                Ativo,
                EmailVerificado
            )
            OUTPUT INSERTED.UsuarioId
            VALUES (
                :nome,
                :cpf,
                :email,
                :senha_hash,
                :perfil,
                :ativo,
                :email_verificado
            )
        """)

        return self._session.execute(
            statement,
            {
                "nome": usuario.nome_completo,
                "cpf": usuario.cpf,
                "email": usuario.email,
                "senha_hash": usuario.senha_hash,
                "perfil": usuario.perfil.value,
                "ativo": usuario.ativo,
                "email_verificado": usuario.email_verificado,
            },
        ).scalar_one()

    def atualizar_senha(
        self,
        usuario_id: int,
        senha_hash: str,
    ) -> bool:
        """
        Atualiza o hash da senha de um usuário ativo.

        A transação é controlada pelo chamador.
        """

        resultado = self._session.execute(
            text("""
                UPDATE seguranca.Usuario
                SET SenhaHash = :senha_hash
                WHERE UsuarioId = :usuario_id
                  AND Ativo = 1
            """),
            {
                "usuario_id": usuario_id,
                "senha_hash": senha_hash,
            },
        )

        return resultado.rowcount == 1

    @staticmethod
    def _converter_usuario(registro) -> Usuario | None:
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
