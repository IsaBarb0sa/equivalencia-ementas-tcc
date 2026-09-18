import pytest

from equivalencia_ementas.academico.domain.entities import (
    MatrizCurricular,
    StatusMatrizCurricular,
)


def test_deve_criar_matriz_curricular_valida() -> None:
    matriz = MatrizCurricular(
        curso_id=1,
        codigo="cc-2026",
        nome="Matriz Ciência da Computação 2026",
        ano_inicio_vigencia=2026,
        semestre_inicio=1,
    )

    assert matriz.codigo == "CC-2026"
    assert matriz.status == StatusMatrizCurricular.RASCUNHO
    assert matriz.pode_ser_alterada is True


def test_nao_deve_aceitar_fim_anterior_ao_inicio() -> None:
    with pytest.raises(
        ValueError,
        match="O fim da vigência não pode ser anterior",
    ):
        MatrizCurricular(
            curso_id=1,
            codigo="CC-2026",
            ano_inicio_vigencia=2026,
            semestre_inicio=2,
            ano_fim_vigencia=2026,
            semestre_fim=1,
        )


def test_matriz_ativa_nao_deve_ser_editavel() -> None:
    matriz = MatrizCurricular(
        curso_id=1,
        codigo="CC-2026",
        status=StatusMatrizCurricular.ATIVA,
    )

    assert matriz.pode_ser_alterada is False
