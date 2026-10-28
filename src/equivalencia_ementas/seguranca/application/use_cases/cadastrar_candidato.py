
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from equivalencia_ementas.seguranca.domain.entities.usuario import (
    PerfilUsuario,
    Usuario,
)
from equivalencia_ementas.seguranca.domain.services.validar_cpf import (
    normalizar_cpf,
    validar_cpf,
)


class ErroCadastro(ValueError):
    pass


@dataclass(frozen=True)
class DadosCadastroCandidato:
    nome_completo: str
    cpf: str
    email: str
    senha: str


@dataclass(frozen=True)
class CandidatoCadastrado:
    usuario_id: int
    nome_completo: str
    email: str


class RepositorioUsuarios(Protocol):

    def buscar_por_email(self, email: str) -> Usuario | None:
        ...

    def buscar_por_cpf(self, cpf: str) -> Usuario | None:
        ...

    def criar(self, usuario: Usuario) -> int:
        ...


class ServicoHashSenha(Protocol):

    def gerar(self, senha: str) -> str:
        ...


class CadastrarCandidato:

    def __init__(
        self,
        repository: RepositorioUsuarios,
        hash_senha: ServicoHashSenha,
    ) -> None:
        self._repository = repository
        self._hash_senha = hash_senha

    def executar(
        self,
        dados: DadosCadastroCandidato,
    ) -> CandidatoCadastrado:

        # Nome completo
        nome = " ".join(dados.nome_completo.split())

        if len(nome) < 3 or len(nome) > 200:
            raise ErroCadastro(
                "Informe um nome válido de até 200 caracteres."
            )

        # CPF
        if not validar_cpf(dados.cpf):
            raise ErroCadastro("O CPF informado é inválido.")

        cpf = normalizar_cpf(dados.cpf)

        # E-mail
        email = dados.email.strip().lower()

        if (
            len(email) > 254
            or not re.fullmatch(
                r"[^@\s]+@[^@\s]+\.[^@\s]+",
                email,
            )
        ):
            raise ErroCadastro("Informe um e-mail válido.")

        # Senha: permite frases-senha e caracteres especiais.
        if not isinstance(dados.senha, str):
            raise ErroCadastro("Informe uma senha válida.")

        if not 12 <= len(dados.senha) <= 128:
            raise ErroCadastro(
                "A senha deve conter entre 12 e 128 caracteres."
            )

        if any(ord(caractere) < 32 for caractere in dados.senha):
            raise ErroCadastro(
                "A senha contém caracteres de controle inválidos."
            )

        # Verificações amigáveis antes da inserção.
        # A unicidade definitiva é garantida pelo SQL Server.
        if self._repository.buscar_por_email(email) is not None:
            raise ErroCadastro(
                "Já existe um cadastro com este e-mail."
            )

        if self._repository.buscar_por_cpf(cpf) is not None:
            raise ErroCadastro(
                "Já existe um cadastro com este CPF."
            )

        senha_hash = self._hash_senha.gerar(dados.senha)

        usuario = Usuario(
            id=None,
            nome_completo=nome,
            cpf=cpf,
            email=email,
            senha_hash=senha_hash,
            perfil=PerfilUsuario.CANDIDATO,
            ativo=True,
            email_verificado=False,
        )

        usuario_id = self._repository.criar(usuario)

        return CandidatoCadastrado(
            usuario_id=usuario_id,
            nome_completo=nome,
            email=email,
        )
