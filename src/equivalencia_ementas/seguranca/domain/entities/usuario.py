
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PerfilUsuario(str, Enum):
    CANDIDATO = "CANDIDATO"
    COORDENADOR = "COORDENADOR"
    ADMIN = "ADMIN"


@dataclass(frozen=True)
class Usuario:
    id: int | None
    nome_completo: str
    cpf: str | None
    email: str
    senha_hash: str
    perfil: PerfilUsuario
    ativo: bool = True
    email_verificado: bool = False
    criado_em: datetime | None = None
