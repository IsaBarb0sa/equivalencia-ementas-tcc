"""Rotas de demonstração da análise de equivalência com JSONs já extraídos.

Copiar para src/equivalencia_ementas/api/routers/equivalencia.py.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from equivalencia_ementas.equivalencia.application.comparar_disciplina_com_matriz import (
    CompararDisciplinaComMatriz,
)
from equivalencia_ementas.equivalencia.application.comparar_trechos import CompararTrechos
from equivalencia_ementas.equivalencia.application.preparar_ementas import (
    preparar_disciplinas_json,
)
from equivalencia_ementas.equivalencia.infrastructure.ia.sentence_transformer import (
    GeradorSentenceTransformer,
)
from equivalencia_ementas.seguranca.domain.entities.usuario import PerfilUsuario


class PedidoComparacao(BaseModel):
    documento_origem: str
    indice_disciplina_origem: int = Field(ge=0)
    quantidade_melhores: int = Field(default=3, ge=1, le=5)


def _pasta_dados() -> Path:
    # Executar uvicorn a partir da raiz do projeto ou definir esta variável.
    return Path(os.environ.get("RAIZ_DADOS_EQUIVALENCIA", "data")).resolve()


def _documentos_origem() -> list[Path]:
    pasta = _pasta_dados() / "resultados_gemini"
    return sorted(pasta.glob("*__gemini.json"))


def _documentos_matriz() -> list[Path]:
    pasta = _pasta_dados() / "resultados_unipac"
    return sorted(pasta.glob("*__gemini.json"))


def _ler_disciplinas(arquivo: Path):
    try:
        return preparar_disciplinas_json(arquivo)
    except (OSError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Não foi possível preparar {arquivo.name}: {exc}",
        ) from exc


@lru_cache(maxsize=1)
def _motor() -> CompararDisciplinaComMatriz:
    gerador = GeradorSentenceTransformer()
    return CompararDisciplinaComMatriz(
        comparador=CompararTrechos(gerador),
        contar_tokens=gerador.contar_tokens,
        limite_tokens=gerador.limite_tokens,
    )


def _executar_comparacao(pedido: PedidoComparacao):
    arquivos = {arquivo.name: arquivo for arquivo in _documentos_origem()}
    arquivo = arquivos.get(pedido.documento_origem)
    if arquivo is None:
        raise HTTPException(status_code=404, detail="Documento de origem não encontrado.")

    origens = _ler_disciplinas(arquivo)
    if pedido.indice_disciplina_origem >= len(origens):
        raise HTTPException(status_code=422, detail="Índice da disciplina inválido.")

    matriz = []
    for arquivo_matriz in _documentos_matriz():
        matriz.extend(_ler_disciplinas(arquivo_matriz))
    if not matriz:
        raise HTTPException(status_code=422, detail="A matriz de demonstração está vazia.")

    origem = origens[pedido.indice_disciplina_origem]
    resultados = _motor().executar(
        disciplina_origem=origem,
        disciplinas_matriz=matriz,
        quantidade_melhores=pedido.quantidade_melhores,
    )

    comparacoes = []
    for item in resultados:
        evidencias = []
        if item.resultado is not None:
            for correspondencia in item.resultado.correspondencias:
                evidencias.append({
                    "origem": correspondencia.trecho_origem.texto,
                    "destino": correspondencia.trecho_destino.texto,
                    "secao_origem": correspondencia.trecho_origem.secao,
                    "secao_destino": correspondencia.trecho_destino.secao,
                    "similaridade_semantica": correspondencia.similaridade,
                    "similaridade_lexical": getattr(
                        correspondencia, "similaridade_lexical", None
                    ),
                })
        comparacoes.append({
            "indice_matriz": item.indice_matriz,
            "disciplina_destino": item.disciplina_destino.nome,
            "status": item.status,
            "evidencias": evidencias,
        })

    return {
        "disciplina_origem": origem.nome,
        "total_disciplinas_matriz": len(matriz),
        "comparacoes": comparacoes,
        "aviso": "Correspondências são evidências para revisão, não aprovação automática.",
    }


def criar_router_equivalencia(obter_usuario_autenticado: Callable) -> APIRouter:
    """Recebe a dependência da API para evitar importação circular com main."""
    router = APIRouter(prefix="/api/coordenacao/equivalencia", tags=["Equivalência"])

    def exigir_coordenador(usuario=Depends(obter_usuario_autenticado)):
        if usuario.perfil != PerfilUsuario.COORDENADOR:
            raise HTTPException(status_code=403, detail="Acesso exclusivo do coordenador.")
        return usuario

    @router.get("/documentos", dependencies=[Depends(exigir_coordenador)])
    def listar_documentos():
        documentos = []
        for arquivo in _documentos_origem():
            disciplinas = _ler_disciplinas(arquivo)
            documentos.append({
                "arquivo": arquivo.name,
                "disciplinas": [
                    {"indice": indice, "nome": disciplina.nome}
                    for indice, disciplina in enumerate(disciplinas)
                ],
            })
        return {"documentos": documentos}

    @router.post("/comparar", dependencies=[Depends(exigir_coordenador)])
    async def comparar(pedido: PedidoComparacao):
        return await run_in_threadpool(_executar_comparacao, pedido)

    return router
