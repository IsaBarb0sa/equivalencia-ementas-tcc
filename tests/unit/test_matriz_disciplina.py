from decimal import Decimal

import pytest

from equivalencia_ementas.academico.domain.entities import (
    MatrizDisciplina,
    NaturezaDisciplina,
)


def test_deve_criar_vinculo_valido() -> None:
    vinculo = MatrizDisciplina(
        matriz_curricular_id=1,
        disciplina_id=1,
        periodo_sugerido=3,
        natureza=NaturezaDisciplina.OBRIGATORIA,
        creditos=Decimal("4.00"),
    )

    assert vinculo.periodo_sugerido == 3
    assert vinculo.creditos == Decimal("4.00")
    assert vinculo.ativa is True


def test_nao_deve_aceitar_periodo_invalido() -> None:
    with pytest.raises(
        ValueError,
        match="O período sugerido deve estar entre 1 e 20",
    ):
        MatrizDisciplina(
            matriz_curricular_id=1,
            disciplina_id=1,
            periodo_sugerido=21,
        )


def test_nao_deve_aceitar_creditos_negativos() -> None:
    with pytest.raises(
        ValueError,
        match="A quantidade de créditos não pode ser negativa",
    ):
        MatrizDisciplina(
            matriz_curricular_id=1,
            disciplina_id=1,
            creditos=Decimal("-1.00"),
        )