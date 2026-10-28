
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from equivalencia_ementas.seguranca.domain.entities.usuario import Usuario
from equivalencia_ementas.seguranca.domain.services.validar_cpf import (
    normalizar_cpf,
)


class CredenciaisInvalidas(ValueError):
    pass


@dataclass(frozen=True)
class DadosLogin:
    identificador: str
    senha: str


@dataclass(frozen=True)
class UsuarioAutenticado:
    usuario_id: int
    nome_completo: str
    email: str
    perfil: str
    email_verificado: bool


class RepositorioAutenticacao(Protocol):
    def buscar_por_email(self, email: str) -> Usuario | None:
        ...

    def buscar_por_cpf(self, cpf: str) -> Usuario | None:
        ...


class VerificadorSenha(Protocol):
    def verificar(self, senha: str, senha_hash: str) -> bool:
        ...


class AutenticarUsuario:
    def __init__(
        self,
        repository: RepositorioAutenticacao,
        hash_senha: VerificadorSenha,
    ) -> None:
        self._repository = repository
        self._hash_senha = hash_senha

    def executar(self, dados: DadosLogin) -> UsuarioAutenticado:
        identificador = dados.identificador.strip().lower()

        if not identificador or not dados.senha:
            raise CredenciaisInvalidas("CPF/e-mail ou senha inválidos.")

        if "@" in identificador:
            usuario = self._repository.buscar_por_email(identificador)
        else:
            cpf = normalizar_cpf(identificador)

            if len(cpf) != 11:
                raise CredenciaisInvalidas(
                    "CPF/e-mail ou senha inválidos."
                )

            usuario = self._repository.buscar_por_cpf(cpf)

        if (
            usuario is None
            or not usuario.ativo
            or not self._hash_senha.verificar(
                dados.senha,
                usuario.senha_hash,
            )
        ):
            raise CredenciaisInvalidas("CPF/e-mail ou senha inválidos.")

        if usuario.id is None:
            raise CredenciaisInvalidas("CPF/e-mail ou senha inválidos.")

        return UsuarioAutenticado(
            usuario_id=usuario.id,
            nome_completo=usuario.nome_completo,
            email=usuario.email,
            perfil=usuario.perfil.value,
            email_verificado=usuario.email_verificado,
        )
