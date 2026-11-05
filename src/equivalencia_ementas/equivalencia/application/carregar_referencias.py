from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


CLASSIFICACOES_VALIDAS = frozenset({
    "correspondente",
    "parcialmente_relacionado",
    "nao_correspondente",
    "inconclusivo",
})


@dataclass(frozen=True)
class IdentificacaoTrecho:
    arquivo: str
    disciplina: str
    secao: str
    texto: str


@dataclass(frozen=True)
class ReferenciaValidada:
    identificador: str
    area: str
    origem: IdentificacaoTrecho
    destino: IdentificacaoTrecho
    classificacao: str
    justificativa: str


def _ler_identificacao(dados: dict) -> IdentificacaoTrecho:
    campos = (
        "arquivo",
        "disciplina",
        "secao",
        "texto",
    )

    valores = {}

    for campo in campos:
        valor = dados.get(campo)

        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(
                f"Campo obrigatório inválido: {campo}"
            )

        valores[campo] = valor

    return IdentificacaoTrecho(**valores)


def carregar_referencias_validadas(
    caminho: Path,
) -> tuple[ReferenciaValidada, ...]:
    """
    Carrega exclusivamente referências revisadas.

    Referências com classificacao_validada = null
    não participam da avaliação.
    """

    with Path(caminho).open(
        "r",
        encoding="utf-8",
    ) as arquivo:
        dados = json.load(arquivo)

    if not isinstance(dados, dict):
        raise ValueError(
            "O arquivo deve conter um objeto JSON."
        )

    referencias = dados.get("referencias")

    if not isinstance(referencias, list):
        raise ValueError(
            "O campo 'referencias' deve ser uma lista."
        )

    resultado = []
    identificadores = set()

    for item in referencias:
        if not isinstance(item, dict):
            raise ValueError(
                "Cada referência deve ser um objeto JSON."
            )

        identificador = item.get("id")

        if (
            not isinstance(identificador, str)
            or not identificador.strip()
        ):
            raise ValueError(
                "Referência sem identificador válido."
            )

        if identificador in identificadores:
            raise ValueError(
                f"Identificador duplicado: {identificador}"
            )

        identificadores.add(identificador)

        classificacao = item.get(
            "classificacao_validada"
        )

        if classificacao is None:
            continue

        if classificacao not in CLASSIFICACOES_VALIDAS:
            raise ValueError(
                f"Classificação inválida na referência "
                f"{identificador}: {classificacao}"
            )

        area = item.get("area")
        justificativa = item.get("justificativa")

        if not isinstance(area, str) or not area.strip():
            raise ValueError(
                f"Área inválida na referência {identificador}."
            )

        if (
            not isinstance(justificativa, str)
            or not justificativa.strip()
        ):
            raise ValueError(
                f"Justificativa inválida: {identificador}."
            )

        resultado.append(
            ReferenciaValidada(
                identificador=identificador,
                area=area,
                origem=_ler_identificacao(item["origem"]),
                destino=_ler_identificacao(item["destino"]),
                classificacao=classificacao,
                justificativa=justificativa,
            )
        )

    if not resultado:
        raise ValueError(
            "Nenhuma referência possui classificação "
            "humana validada."
        )

    return tuple(resultado)