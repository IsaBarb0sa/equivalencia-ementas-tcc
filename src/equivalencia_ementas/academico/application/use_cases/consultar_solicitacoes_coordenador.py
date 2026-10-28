
from __future__ import annotations

from typing import Protocol

from equivalencia_ementas.academico.application.use_cases.consultar_solicitacoes import (
    DocumentoConsulta,
    SolicitacaoDetalhada,
    SolicitacaoResumo,
)



class RepositorioSolicitacoesCoordenador(Protocol):

    def listar_solicitacoes_coordenador(
        self,
        instituicao_id: int,
        coordenador_usuario_id: int,
        limite: int = 50,
    ) -> list[dict]:
        ...

    def buscar_por_protocolo_coordenador(
        self,
        protocolo: str,
        instituicao_id: int,
        coordenador_usuario_id: int,
    ) -> dict | None:
        ...


class ConsultarSolicitacoesCoordenador:

    def __init__(
        self,
        repository: RepositorioSolicitacoesCoordenador,
    ) -> None:
        self._repository = repository

    def listar(
        self,
        instituicao_id: int,
        coordenador_usuario_id: int,
        limite: int = 50,
    ) -> list[SolicitacaoResumo]:

        if instituicao_id <= 0:
            raise ValueError("A instituição deve ser válida.")

        if coordenador_usuario_id <= 0:
            raise ValueError("O coordenador deve ser válido.")

        if not 1 <= limite <= 100:
            raise ValueError("O limite deve estar entre 1 e 100.")

        registros = (
            self._repository.listar_solicitacoes_coordenador(
                instituicao_id=instituicao_id,
                coordenador_usuario_id=coordenador_usuario_id,
                limite=limite,
            )
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
        coordenador_usuario_id: int,
    ) -> SolicitacaoDetalhada | None:

        if instituicao_id <= 0:
            raise ValueError("A instituição deve ser válida.")

        if coordenador_usuario_id <= 0:
            raise ValueError("O coordenador deve ser válido.")

        if not protocolo or not protocolo.strip():
            raise ValueError("O protocolo deve ser informado.")

        registro = (
            self._repository.buscar_por_protocolo_coordenador(
                protocolo=protocolo.strip(),
                instituicao_id=instituicao_id,
                coordenador_usuario_id=coordenador_usuario_id,
            )
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
