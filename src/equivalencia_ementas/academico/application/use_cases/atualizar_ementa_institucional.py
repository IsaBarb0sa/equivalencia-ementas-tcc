
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Protocol


class ErroAtualizacaoEmenta(ValueError):
    """Dados inválidos para atualização da ementa."""


class ConflitoAtualizacaoEmenta(Exception):
    """A ementa foi alterada ou não está disponível para edição."""


class EmentaNaoEncontrada(Exception):
    """Ementa inexistente ou não autorizada."""


@dataclass(frozen=True)
class DadosAtualizacaoEmenta:
    matriz_disciplina_id: int
    ementa_id: int
    instituicao_id: int
    coordenador_usuario_id: int
    versao_linha: str

    resumo: str | None
    competencias_habilidades: str | None

    carga_horaria_total: Decimal | None
    carga_horaria_teorica: Decimal | None
    carga_horaria_pratica: Decimal | None


class RepositorioAtualizacaoEmenta(Protocol):

    def atualizar_ementa_coordenador(
        self,
        *,
        matriz_disciplina_id: int,
        ementa_id: int,
        instituicao_id: int,
        coordenador_usuario_id: int,
        versao_linha: str,
        resumo: str | None,
        competencias_habilidades: str | None,
        carga_horaria_total: Decimal | None,
        carga_horaria_teorica: Decimal | None,
        carga_horaria_pratica: Decimal | None,
    ) -> str:
        ...


class AtualizarEmentaInstitucional:

    def __init__(
        self,
        repository: RepositorioAtualizacaoEmenta,
    ) -> None:
        self._repository = repository

    @staticmethod
    def _normalizar_texto(
        valor: str | None,
        nome_campo: str,
        limite: int,
    ) -> str | None:

        if valor is None:
            return None

        if not isinstance(valor, str):
            raise ErroAtualizacaoEmenta(
                f"{nome_campo}: informe um texto válido."
            )

        texto = valor.strip()

        if len(texto) > limite:
            raise ErroAtualizacaoEmenta(
                f"{nome_campo}: limite de {limite} caracteres."
            )

        return texto or None

    @staticmethod
    def _validar_carga(
        valor: Decimal | None,
        nome_campo: str,
    ) -> Decimal | None:

        if valor is None:
            return None

        if isinstance(valor, bool):
            raise ErroAtualizacaoEmenta(
                f"{nome_campo}: valor inválido."
            )

        try:
            carga = Decimal(str(valor))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ErroAtualizacaoEmenta(
                f"{nome_campo}: informe um número válido."
            ) from exc

        if not carga.is_finite():
            raise ErroAtualizacaoEmenta(
                f"{nome_campo}: valor não finito."
            )

        if carga < 0:
            raise ErroAtualizacaoEmenta(
                f"{nome_campo}: não pode ser negativa."
            )

        if carga > Decimal("999999.99"):
            raise ErroAtualizacaoEmenta(
                f"{nome_campo}: valor acima do permitido."
            )

        if carga != carga.quantize(Decimal("0.01")):
            raise ErroAtualizacaoEmenta(
                f"{nome_campo}: utilize até duas casas decimais."
            )

        return carga

    def executar(
        self,
        dados: DadosAtualizacaoEmenta,
    ) -> None:

        if min(
            dados.matriz_disciplina_id,
            dados.ementa_id,
            dados.instituicao_id,
            dados.coordenador_usuario_id,
        ) <= 0:
            raise ErroAtualizacaoEmenta(
                "Os identificadores devem ser positivos."
            )

        if not re.fullmatch(
            r"0x[0-9a-fA-F]{16}",
            dados.versao_linha,
        ):
            raise ErroAtualizacaoEmenta(
                "A versão da ementa é inválida."
            )

        resumo = self._normalizar_texto(
            dados.resumo,
            "Resumo",
            30000,
        )

        competencias = self._normalizar_texto(
            dados.competencias_habilidades,
            "Competências e habilidades",
            30000,
        )

        total = self._validar_carga(
            dados.carga_horaria_total,
            "Carga horária total",
        )

        teorica = self._validar_carga(
            dados.carga_horaria_teorica,
            "Carga horária teórica",
        )

        pratica = self._validar_carga(
            dados.carga_horaria_pratica,
            "Carga horária prática",
        )

        if total is not None and total == 0:
            raise ErroAtualizacaoEmenta(
                "A carga horária total deve ser maior que zero."
            )

        if total is not None:
            componentes = [
                valor
                for valor in (teorica, pratica)
                if valor is not None
            ]

            if sum(componentes, Decimal("0")) > total:
                raise ErroAtualizacaoEmenta(
                    "A soma das cargas horárias teórica e prática "
                    "não pode ultrapassar a carga horária total."
                )

        resultado = self._repository.atualizar_ementa_coordenador(
            matriz_disciplina_id=dados.matriz_disciplina_id,
            ementa_id=dados.ementa_id,
            instituicao_id=dados.instituicao_id,
            coordenador_usuario_id=dados.coordenador_usuario_id,
            versao_linha=dados.versao_linha,
            resumo=resumo,
            competencias_habilidades=competencias,
            carga_horaria_total=total,
            carga_horaria_teorica=teorica,
            carga_horaria_pratica=pratica,
        )

        if resultado == "nao_encontrado":
            raise EmentaNaoEncontrada(
                "Ementa não encontrada ou não autorizada."
            )

        if resultado == "conflito":
            raise ConflitoAtualizacaoEmenta(
                "A ementa foi modificada por outro usuário "
                "ou não está disponível para edição. "
                "Atualize a página antes de tentar novamente."
            )

        if resultado != "atualizado":
            raise RuntimeError(
                "Resultado inesperado ao atualizar a ementa."
            )
