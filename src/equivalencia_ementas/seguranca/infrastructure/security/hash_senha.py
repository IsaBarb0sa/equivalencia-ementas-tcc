
from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)
from argon2.low_level import Type


class HashSenha:
    def __init__(self) -> None:
        self._hasher = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            salt_len=16,
            type=Type.ID,
        )

    def gerar(self, senha: str) -> str:
        if not isinstance(senha, str) or not senha:
            raise ValueError("A senha não pode ser vazia.")

        return self._hasher.hash(senha)

    def verificar(self, senha: str, senha_hash: str) -> bool:
        if not isinstance(senha, str) or not isinstance(senha_hash, str):
            return False

        if not senha or not senha_hash:
            return False

        try:
            return self._hasher.verify(senha_hash, senha)
        except (
            VerifyMismatchError,
            VerificationError,
            InvalidHashError,
        ):
            return False

    def precisa_atualizar(self, senha_hash: str) -> bool:
        return self._hasher.check_needs_rehash(senha_hash)
