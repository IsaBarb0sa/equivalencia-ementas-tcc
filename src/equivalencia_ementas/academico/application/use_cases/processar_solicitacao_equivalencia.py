
"""Orquestra extração, armazenamento e pré-análise de uma solicitação.

Não chama FastAPI nem abre sessões SQL; as dependências são injetadas.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from equivalencia_ementas.academico.application.adaptar_extracao_gemini import (
    criar_lote_extracao_gemini,
)
from equivalencia_ementas.academico.application.registrar_extracao import RegistrarExtracao
from equivalencia_ementas.equivalencia.application.analisar_documento import (
    AnalisarDocumento,
    AnaliseDisciplinaOrigem,
)
from equivalencia_ementas.equivalencia.application.preparar_ementas import preparar_disciplinas
from equivalencia_ementas.equivalencia.domain.entities import DisciplinaParaEquivalencia
from equivalencia_ementas.infraestrutura.ia.modelos_extracao import DocumentoAcademicoExtraido


@dataclass(frozen=True)
class DocumentoDaSolicitacao:
    documento_fonte_id: int
    caminho_pdf: Path
    nome_arquivo: str
    hash_sha256: str
    tamanho_bytes: int
    paginas: int


@dataclass(frozen=True)
class ResultadoProcessamentoSolicitacao:
    quantidade_documentos: int
    quantidade_disciplinas: int
    quantidade_sem_disciplinas: int
    analises: tuple[AnaliseDisciplinaOrigem, ...]


class ExtratorDocumento(Protocol):
    def processar(self, caminho_pdf: Path) -> DocumentoAcademicoExtraido: ...


class ProcessarSolicitacaoEquivalencia:
    def __init__(
        self,
        extrator: ExtratorDocumento,
        registrador: RegistrarExtracao,
        analisador: AnalisarDocumento,
        versao_extrator: str,
    ) -> None:
        self._extrator = extrator
        self._registrador = registrador
        self._analisador = analisador
        self._versao_extrator = versao_extrator

    def executar(
        self,
        *,
        documentos: Sequence[DocumentoDaSolicitacao],
        disciplinas_matriz: Sequence[DisciplinaParaEquivalencia],
    ) -> ResultadoProcessamentoSolicitacao:
        origens: list[DisciplinaParaEquivalencia] = []
        sem_disciplinas = 0

        for item in documentos:
            documento = self._extrator.processar(item.caminho_pdf)
            lote = criar_lote_extracao_gemini(
                documento=documento,
                nome_arquivo=item.nome_arquivo,
                uri_armazenamento=str(item.caminho_pdf),
                hash_sha256=item.hash_sha256,
                tamanho_bytes=item.tamanho_bytes,
                paginas=item.paginas,
                versao_extrator=self._versao_extrator,
            )
            if lote is None:
                sem_disciplinas += 1
                continue

            self._registrador.executar(lote)
            origens.extend(preparar_disciplinas(documento.model_dump(mode="json")))

        analises = self._analisador.executar(origens, disciplinas_matriz) if origens else ()
        return ResultadoProcessamentoSolicitacao(
            quantidade_documentos=len(documentos),
            quantidade_disciplinas=len(origens),
            quantidade_sem_disciplinas=sem_disciplinas,
            analises=tuple(analises),
        )

