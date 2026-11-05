"""Triagem acadêmica provisória: sugestões, nunca pareceres oficiais."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from equivalencia_ementas.equivalencia.application.comparar_disciplina_com_matriz import (
    ComparacaoDisciplinaMatriz,
)
from equivalencia_ementas.equivalencia.domain.entities import DisciplinaParaEquivalencia


class IndicacaoEquivalencia(StrEnum):
    APTO_A_DISPENSA = "APTO_A_DISPENSA"
    TALVEZ_APTO = "TALVEZ_APTO"
    NAO_APTO = "NAO_APTO"


@dataclass(frozen=True)
class PoliticaTriagem:
    """Parâmetros experimentais; ajustar após validação acadêmica."""

    versao: str = "triagem-experimental-v1"
    similaridade_topico: float = 0.75
    cobertura_apto: float = 0.85
    cobertura_nao_apto: float = 0.30

    def __post_init__(self) -> None:
        if not (0 <= self.similaridade_topico <= 1):
            raise ValueError("similaridade_topico fora de 0..1")
        if not (0 <= self.cobertura_nao_apto < self.cobertura_apto <= 1):
            raise ValueError("Limites de cobertura inválidos")


@dataclass(frozen=True)
class SugestaoEquivalencia:
    disciplina_origem: str
    disciplina_destino: str
    indicacao: IndicacaoEquivalencia
    cobertura_destino: float | None
    carga_horaria_compativel: bool | None
    topicos_cobertos: int
    total_topicos: int
    justificativas: tuple[str, ...]
    versao_politica: str
    decisao_coordenador: str | None = None


def _carga_compativel(
    origem: DisciplinaParaEquivalencia,
    destino: DisciplinaParaEquivalencia,
) -> bool | None:
    a, b = origem.carga_horaria, destino.carga_horaria
    if a.total is None or b.total is None:
        return None
    # Horas e horas-aula não podem ser comparadas diretamente sem conversão validada.
    if not a.unidade or not b.unidade or a.unidade != b.unidade:
        return None
    return a.total >= b.total


def sugerir_equivalencia(
    origem: DisciplinaParaEquivalencia,
    comparacao: ComparacaoDisciplinaMatriz,
    politica: PoliticaTriagem = PoliticaTriagem(),
) -> SugestaoEquivalencia:
    carga = _carga_compativel(origem, comparacao.disciplina_destino)
    justificativas: list[str] = []

    # Nunca interpretar ausência de evidências como ausência de conteúdo.
    if comparacao.status != "comparado" or comparacao.consolidacao is None:
        indicacao = IndicacaoEquivalencia.TALVEZ_APTO
        cobertura = None
        total = cobertos = 0
        justificativas.append("Dados insuficientes para classificação automática.")
    else:
        topicos = comparacao.consolidacao.topicos
        total = len(topicos)
        cobertos = sum(
            1 for topico in topicos
            if any(
                correspondencia.similaridade >= politica.similaridade_topico
                for correspondencia in topico.correspondencias
            )
        )
        cobertura = cobertos / total if total else None

        if cobertura is None:
            indicacao = IndicacaoEquivalencia.TALVEZ_APTO
            justificativas.append("Nenhum tópico de destino disponível para avaliação.")
        elif carga is False:
            indicacao = IndicacaoEquivalencia.NAO_APTO
            justificativas.append("Carga horária de origem inferior à de destino, na mesma unidade.")
        elif cobertura >= politica.cobertura_apto and carga is True:
            indicacao = IndicacaoEquivalencia.APTO_A_DISPENSA
        elif cobertura < politica.cobertura_nao_apto:
            indicacao = IndicacaoEquivalencia.NAO_APTO
        else:
            indicacao = IndicacaoEquivalencia.TALVEZ_APTO
        justificativas.append(
            f"{cobertos} de {total} tópicos do destino possuem evidência acima do limiar experimental."
        )

    if carga is None:
        justificativas.append("Compatibilidade da carga horária não comprovada.")

    return SugestaoEquivalencia(
        disciplina_origem=origem.nome,
        disciplina_destino=comparacao.disciplina_destino.nome,
        indicacao=indicacao,
        cobertura_destino=cobertura,
        carga_horaria_compativel=carga,
        topicos_cobertos=cobertos,
        total_topicos=total,
        justificativas=tuple(justificativas),
        versao_politica=politica.versao,
    )
