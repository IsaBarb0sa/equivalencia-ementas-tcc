from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from equivalencia_ementas.equivalencia.domain.entities import (
    CargaHorariaEquivalencia,
    DisciplinaParaEquivalencia,
)


class ErroPreparacaoEmentas(ValueError):
    """Indica que os dados recebidos não possuem o formato esperado."""


def _texto(valor: Any) -> str | None:
    """Preserva o texto, removendo apenas espaços nas extremidades."""
    if valor is None:
        return None

    if not isinstance(valor, str):
        raise ErroPreparacaoEmentas(
            "Um campo textual possui um valor inválido."
        )

    texto = valor.strip()
    return texto or None


def _objeto(valor: Any, campo: str) -> Mapping:
    if valor is None:
        return {}

    if not isinstance(valor, Mapping):
        raise ErroPreparacaoEmentas(
            f"O campo '{campo}' deve ser um objeto."
        )

    return valor


def _numero(valor: Any, campo: str) -> float | None:
    if valor is None:
        return None

    if isinstance(valor, bool) or not isinstance(
        valor, (int, float)
    ):
        raise ErroPreparacaoEmentas(
            f"O campo '{campo}' deve ser numérico."
        )

    from math import isfinite

    numero = float(valor)

    if not isfinite(numero) or numero < 0:
        raise ErroPreparacaoEmentas(
            f"O campo '{campo}' possui um valor inválido."
        )

    return numero


def preparar_disciplinas(
    dados: Mapping[str, Any],
) -> list[DisciplinaParaEquivalencia]:
    """
    Converte um documento acadêmico extraído em disciplinas
    independentes do formato de entrada.

    Aceita tanto o JSON completo quanto o objeto 'resultado'.
    """

    if not isinstance(dados, Mapping):
        raise ErroPreparacaoEmentas(
            "O documento deve ser um objeto."
        )

    resultado = dados.get("resultado", dados)

    if not isinstance(resultado, Mapping):
        raise ErroPreparacaoEmentas(
            "O resultado da extração deve ser um objeto."
        )

    registros = resultado.get("disciplinas")

    if not isinstance(registros, list):
        raise ErroPreparacaoEmentas(
            "O documento deve conter uma lista de disciplinas."
        )

    instituicao = _texto(resultado.get("instituicao"))
    curso = _texto(resultado.get("curso"))

    disciplinas = []

    for indice, registro in enumerate(registros):
        if not isinstance(registro, Mapping):
            raise ErroPreparacaoEmentas(
                f"Disciplina na posição {indice} inválida."
            )

        nome = _texto(registro.get("nome"))

        if not nome:
            raise ErroPreparacaoEmentas(
                f"Disciplina na posição {indice} sem nome."
            )

        carga = _objeto(
            registro.get("carga_horaria"),
            "carga_horaria",
        )

        objetivos = _objeto(
            registro.get("objetivos"),
            "objetivos",
        )

        disciplina = DisciplinaParaEquivalencia(
            nome=nome,
            instituicao=instituicao,
            curso=curso,
            ementa=_texto(registro.get("ementa")),
            conteudo_programatico=_texto(
                registro.get("conteudo_programatico")
            ),
            objetivo_geral=_texto(
                objetivos.get("geral")
            ),
            objetivos_especificos=_texto(
                objetivos.get("especificos")
            ),
            objetivos_nao_classificados=_texto(
                objetivos.get("nao_classificados")
            ),
            competencias_habilidades=_texto(
                registro.get("competencias_habilidades")
            ),
            carga_horaria=CargaHorariaEquivalencia(
                total=_numero(carga.get("total"), "total"),
                teorica=_numero(carga.get("teorica"), "teorica"),
                pratica=_numero(carga.get("pratica"), "pratica"),
                unidade=_texto(carga.get("unidade")),
            ),
        )

        disciplinas.append(disciplina)

    return disciplinas


def preparar_disciplinas_json(
    caminho: str | Path,
) -> list[DisciplinaParaEquivalencia]:
    """Carrega um arquivo JSON e prepara suas disciplinas."""

    caminho = Path(caminho)

    with caminho.open("r", encoding="utf-8-sig") as arquivo:
        dados = json.load(arquivo)

    return preparar_disciplinas(dados)