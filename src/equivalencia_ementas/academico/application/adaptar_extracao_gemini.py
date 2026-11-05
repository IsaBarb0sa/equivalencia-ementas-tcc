
"""Converte a saída Gemini no lote exigido por RegistrarExtracao.

Não grava no banco, não publica ementas e não decide equivalência.
"""

from __future__ import annotations

from equivalencia_ementas.academico.application.registrar_extracao import LoteExtracao
from equivalencia_ementas.academico.application.normalizar_extracao import normalizar_extracao
from equivalencia_ementas.infraestrutura.ia.modelos_extracao import DocumentoAcademicoExtraido


def criar_lote_extracao_gemini(
    *,
    documento: DocumentoAcademicoExtraido,
    nome_arquivo: str,
    uri_armazenamento: str,
    hash_sha256: str,
    tamanho_bytes: int,
    paginas: int,
    versao_extrator: str,
) -> LoteExtracao | None:
    """Retorna None para documentos sem disciplinas; requer tratamento explícito.

    A auditoria replica fielmente os dados extraídos, conforme o contrato
    atual de RegistrarExtracao. Observações ficam nos metadados do lote.
    """
    normalizado = normalizar_extracao(documento)
    if not normalizado.disciplinas:
        return None

    metadados = {
        "documento": {
            "sha256": hash_sha256,
            "total_paginas": paginas,
        },
        "versao_extrator": versao_extrator,
        "instituicao": normalizado.instituicao,
        "curso": normalizado.curso,
        "observacoes_documento": normalizado.observacoes_documento,
    }
    registros = [
        {"numero": numero, "dados": disciplina.model_dump(mode="json")}
        for numero, disciplina in enumerate(normalizado.disciplinas, start=1)
    ]
    academico = {**metadados, "ementas": registros}
    auditoria = {**metadados, "ementas": registros}

    return LoteExtracao(
        nome_arquivo=nome_arquivo,
        uri_armazenamento=uri_armazenamento,
        hash_sha256=hash_sha256,
        tamanho_bytes=tamanho_bytes,
        paginas=paginas,
        versao_extrator=versao_extrator,
        academico=academico,
        auditoria=auditoria,
    )

