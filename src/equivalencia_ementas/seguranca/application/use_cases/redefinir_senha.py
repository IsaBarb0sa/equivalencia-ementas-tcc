
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from equivalencia_ementas.seguranca.infrastructure.security.gerenciador_recuperacao_senha import (
    GerenciadorRecuperacaoSenha,
)


class ErroRedefinicaoSenha(ValueError):
    pass


@dataclass(frozen=True)
class DadosRedefinicaoSenha:
    token: str
    nova_senha: str


class RepositorioRecuperacao(Protocol):

    def consumir(self, token_hash: str) -> int | None:
        ...

    def invalidar_pendentes(self, usuario_id: int) -> None:
        ...


class RepositorioUsuario(Protocol):

    def atualizar_senha(
        self,
        usuario_id: int,
        senha_hash: str,
    ) -> bool:
        ...


class RepositorioSessao(Protocol):

    def revogar_todas_do_usuario(
        self,
        usuario_id: int,
    ) -> None:
        ...


class GeradorHashSenha(Protocol):

    def gerar(self, senha: str) -> str:
        ...


class RedefinirSenha:
    """
    Redefine a senha mediante token temporário válido.

    Importante: executar dentro de uma transação
    que inclua todos os repositórios.
    """

    def __init__(
        self,
        recuperacao_repository: RepositorioRecuperacao,
        usuario_repository: RepositorioUsuario,
        sessao_repository: RepositorioSessao,
        hash_senha: GeradorHashSenha,
    ) -> None:
        self._recuperacao_repository = recuperacao_repository
        self._usuario_repository = usuario_repository
        self._sessao_repository = sessao_repository
        self._hash_senha = hash_senha

    def executar(
        self,
        dados: DadosRedefinicaoSenha,
    ) -> None:

        if not GerenciadorRecuperacaoSenha.token_valido(
            dados.token
        ):
            raise ErroRedefinicaoSenha(
                "Link de recuperação inválido ou expirado."
            )

        if not 12 <= len(dados.nova_senha) <= 128:
            raise ErroRedefinicaoSenha(
                "A nova senha deve conter entre "
                "12 e 128 caracteres."
            )

        # Gera o hash Argon2id antes de consumir o token.
        novo_hash = self._hash_senha.gerar(
            dados.nova_senha
        )

        token_hash = (
            GerenciadorRecuperacaoSenha.calcular_hash(
                dados.token
            )
        )

        usuario_id = self._recuperacao_repository.consumir(
            token_hash
        )

        if usuario_id is None:
            raise ErroRedefinicaoSenha(
                "Link de recuperação inválido ou expirado."
            )

        atualizado = self._usuario_repository.atualizar_senha(
            usuario_id=usuario_id,
            senha_hash=novo_hash,
        )

        if not atualizado:
            raise ErroRedefinicaoSenha(
                "Não foi possível redefinir a senha."
            )

        # Invalida todos os outros links pendentes.
        self._recuperacao_repository.invalidar_pendentes(
            usuario_id
        )

        # Encerra sessões anteriores em outros dispositivos.
        self._sessao_repository.revogar_todas_do_usuario(
            usuario_id
        )
