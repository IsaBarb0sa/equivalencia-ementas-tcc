
from __future__ import annotations

from datetime import datetime
from typing import Protocol
from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentoConsulta:
    documento_id: int
    nome_arquivo: str
    quantidade_paginas: int
    tamanho_bytes: int
    status_documento: str


@dataclass(frozen=True)
class SolicitacaoResumo:
    solicitacao_id: int
    protocolo: str
    curso_id: int
    curso_destino: str
    status: str
    criado_em: datetime
    quantidade_documentos: int


@dataclass(frozen=True)
class SolicitacaoDetalhada:
    solicitacao_id: int
    protocolo: str
    curso_id: int
    curso_destino: str
    status: str
    criado_em: datetime
    quantidade_documentos: int
    documentos: list[DocumentoConsulta]



class RepositorioConsultaSolicitacoes(Protocol):

    def listar_solicitacoes(
        self,
        instituicao_id: int,
        candidato_usuario_id: int,
        limite: int = 50,
    ) -> list[dict]:
        ...

    def buscar_por_protocolo(
        self,
        protocolo: str,
        instituicao_id: int,
        candidato_usuario_id: int,
    ) -> dict | None:
        ...




class ConsultarSolicitacoes:

    def __init__(
        self,
        repository: RepositorioConsultaSolicitacoes,
    ) -> None:
        self._repository = repository

    def listar(
        self,
        instituicao_id: int,
        candidato_usuario_id: int,
        limite: int = 50,
    ) -> list[SolicitacaoResumo]:

        if instituicao_id <= 0:
            raise ValueError("A instituição deve ser válida.")

        if candidato_usuario_id <= 0:
            raise ValueError("O candidato deve ser válido.")

        if not 1 <= limite <= 100:
            raise ValueError("O limite deve estar entre 1 e 100.")

        registros = self._repository.listar_solicitacoes(
            instituicao_id=instituicao_id,
            candidato_usuario_id=candidato_usuario_id,
            limite=limite,
        )

        return [
            SolicitacaoResumo(
                solicitacao_id=registro["solicitacao_id"],
                protocolo=registro["protocolo"],
                curso_id=registro["curso_id"],
                curso_destino=registro["curso_destino"],
                status=registro["status"],
                criado_em=registro["criado_em"],
                quantidade_documentos=registro["quantidade_documentos"],
            )
            for registro in registros
        ]

    def buscar(
        self,
        protocolo: str,
        instituicao_id: int,
        candidato_usuario_id: int,
    ) -> SolicitacaoDetalhada | None:

        if instituicao_id <= 0:
            raise ValueError("A instituição deve ser válida.")

        if candidato_usuario_id <= 0:
            raise ValueError("O candidato deve ser válido.")

        if not protocolo or not protocolo.strip():
            raise ValueError("O protocolo deve ser informado.")

        registro = self._repository.buscar_por_protocolo(
            protocolo=protocolo.strip(),
            instituicao_id=instituicao_id,
            candidato_usuario_id=candidato_usuario_id,
        )

        if registro is None:
            return None

        documentos = [
            DocumentoConsulta(
                documento_id=documento["documento_id"],
                nome_arquivo=documento["nome_arquivo"],
                quantidade_paginas=documento["quantidade_paginas"],
                tamanho_bytes=documento["tamanho_bytes"],
                status_documento=documento["status_documento"],
            )
            for documento in registro["documentos"]
        ]

        return SolicitacaoDetalhada(
            solicitacao_id=registro["solicitacao_id"],
            protocolo=registro["protocolo"],
            curso_id=registro["curso_id"],
            curso_destino=registro["curso_destino"],
            status=registro["status"],
            criado_em=registro["criado_em"],
            quantidade_documentos=registro["quantidade_documentos"],
            documentos=documentos,
        )
