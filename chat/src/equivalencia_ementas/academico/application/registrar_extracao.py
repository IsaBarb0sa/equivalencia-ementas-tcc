"""Valida a extração e encaminha resultados pendentes para armazenamento atômico."""
import json
import re
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class LoteExtracao:
    nome_arquivo: str
    uri_armazenamento: str
    hash_sha256: str
    tamanho_bytes: int
    paginas: int
    versao_extrator: str
    academico: dict
    auditoria: dict


class ArmazenamentoExtracao(Protocol):
    def registrar_atomico(self, lote: LoteExtracao) -> list[int]: ...


def registros_por_numero(documento: dict) -> dict[int, dict]:
    registros = documento.get("ementas")
    if not isinstance(registros, list) or not registros:
        raise ValueError("O lote deve conter ementas para revisão.")
    resultado = {}
    for registro in registros:
        numero = registro.get("numero")
        if type(numero) is not int or numero <= 0 or numero in resultado:
            raise ValueError("Cada ementa deve possuir um número positivo e único.")
        if not isinstance(registro.get("dados"), dict):
            raise ValueError("Dados da ementa ausentes ou inválidos.")
        resultado[numero] = registro
    return resultado


class RegistrarExtracao:
    def __init__(self, armazenamento: ArmazenamentoExtracao):
        self._armazenamento = armazenamento

    def executar(self, lote: LoteExtracao) -> list[int]:
        if not re.fullmatch(r"[0-9a-fA-F]{64}", lote.hash_sha256):
            raise ValueError("Hash SHA-256 inválido.")
        if (type(lote.paginas) is not int or lote.paginas <= 0
                or type(lote.tamanho_bytes) is not int or lote.tamanho_bytes <= 0):
            raise ValueError("Tamanho e quantidade de páginas devem ser positivos.")
        for valor, limite in ((lote.nome_arquivo, 260), (lote.uri_armazenamento, 1000),
                              (lote.versao_extrator, 50)):
            if not valor.strip() or len(valor) > limite:
                raise ValueError("Metadados do lote ausentes ou acima do limite.")
        for documento in (lote.academico, lote.auditoria):
            json.dumps(documento, allow_nan=False)
            origem = documento.get("documento", {})
            if (origem.get("sha256") != lote.hash_sha256
                    or origem.get("total_paginas") != lote.paginas
                    or documento.get("versao_extrator") != lote.versao_extrator):
                raise ValueError("Documento ou versão divergente entre PDF, resultado e auditoria.")
        academico = registros_por_numero(lote.academico)
        auditoria = registros_por_numero(lote.auditoria)
        if academico.keys() != auditoria.keys() or any(
            registro["dados"] != auditoria[numero]["dados"]
            for numero, registro in academico.items()
        ):
            raise ValueError("Dados extraídos divergem da auditoria; revisão necessária.")
        return self._armazenamento.registrar_atomico(lote)
