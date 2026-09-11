from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    FetchedValue,
    ForeignKey,
    String,
    Unicode,
)
from sqlalchemy.dialects.mssql import ROWVERSION
from sqlalchemy.orm import Mapped, mapped_column

from equivalencia_ementas.academico.infrastructure.orm.base import Base


class InstituicaoModel(Base):
    __tablename__ = "Instituicao"
    __table_args__ = {"schema": "academico"}

    instituicao_id: Mapped[int] = mapped_column(
        "InstituicaoId",
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    codigo: Mapped[str | None] = mapped_column(
        "Codigo",
        Unicode(30),
        nullable=True,
    )

    nome: Mapped[str] = mapped_column(
        "Nome",
        Unicode(200),
        nullable=False,
    )

    sigla: Mapped[str | None] = mapped_column(
        "Sigla",
        Unicode(30),
        nullable=True,
    )

    cnpj: Mapped[str | None] = mapped_column(
        "Cnpj",
        String(14),
        nullable=True,
    )

    cidade: Mapped[str | None] = mapped_column(
        "Cidade",
        Unicode(100),
        nullable=True,
    )

    uf: Mapped[str | None] = mapped_column(
        "Uf",
        String(2),
        nullable=True,
    )

    ativa: Mapped[bool] = mapped_column(
        "Ativa",
        Boolean,
        nullable=False,
        server_default=FetchedValue(),
    )

    criado_em: Mapped[datetime] = mapped_column(
        "CriadoEm",
        DateTime,
        nullable=False,
        server_default=FetchedValue(),
    )

    atualizado_em: Mapped[datetime] = mapped_column(
        "AtualizadoEm",
        DateTime,
        nullable=False,
        server_default=FetchedValue(),
    )

    versao_linha: Mapped[bytes] = mapped_column(
        "VersaoLinha",
        ROWVERSION,
        nullable=False,
        server_default=FetchedValue(),
    )

class CursoModel(Base):
    __tablename__ = "Curso"
    __table_args__ = {"schema": "academico"}

    curso_id: Mapped[int] = mapped_column(
        "CursoId",
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    instituicao_id: Mapped[int] = mapped_column(
        "InstituicaoId",
        BigInteger,
        ForeignKey("academico.Instituicao.InstituicaoId"),
        nullable=False,
    )

    codigo: Mapped[str] = mapped_column(
        "Codigo",
        Unicode(30),
        nullable=False,
    )

    nome: Mapped[str] = mapped_column(
        "Nome",
        Unicode(200),
        nullable=False,
    )

    nivel: Mapped[str] = mapped_column(
        "Nivel",
        String(20),
        nullable=False,
    )

    modalidade: Mapped[str] = mapped_column(
        "Modalidade",
        String(20),
        nullable=False,
    )

    ativo: Mapped[bool] = mapped_column(
        "Ativo",
        Boolean,
        nullable=False,
    )

    criado_em: Mapped[datetime] = mapped_column(
        "CriadoEm",
        DateTime,
        nullable=False,
        server_default=FetchedValue(),
    )

    atualizado_em: Mapped[datetime] = mapped_column(
        "AtualizadoEm",
        DateTime,
        nullable=False,
        server_default=FetchedValue(),
    )

    versao_linha: Mapped[bytes] = mapped_column(
        "VersaoLinha",
        ROWVERSION,
        nullable=False,
        server_default=FetchedValue(),
    )


class DisciplinaModel(Base):
    __tablename__ = "Disciplina"
    __table_args__ = {"schema": "academico"}

    disciplina_id: Mapped[int] = mapped_column(
        "DisciplinaId",
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    instituicao_id: Mapped[int] = mapped_column(
        "InstituicaoId",
        BigInteger,
        ForeignKey("academico.Instituicao.InstituicaoId"),
        nullable=False,
    )

    codigo: Mapped[str] = mapped_column(
        "Codigo",
        Unicode(50),
        nullable=False,
    )

    nome: Mapped[str] = mapped_column(
        "Nome",
        Unicode(200),
        nullable=False,
    )

    nome_normalizado: Mapped[str | None] = mapped_column(
        "NomeNormalizado",
        Unicode(200),
        nullable=True,
    )

    area_conhecimento: Mapped[str | None] = mapped_column(
        "AreaConhecimento",
        Unicode(150),
        nullable=True,
    )

    ativa: Mapped[bool] = mapped_column(
        "Ativa",
        Boolean,
        nullable=False,
    )

    criado_em: Mapped[datetime] = mapped_column(
        "CriadoEm",
        DateTime,
        nullable=False,
        server_default=FetchedValue(),
    )

    atualizado_em: Mapped[datetime] = mapped_column(
        "AtualizadoEm",
        DateTime,
        nullable=False,
        server_default=FetchedValue(),
    )

    versao_linha: Mapped[bytes] = mapped_column(
        "VersaoLinha",
        ROWVERSION,
        nullable=False,
        server_default=FetchedValue(),
    )