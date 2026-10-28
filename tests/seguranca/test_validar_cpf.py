
import pytest

from equivalencia_ementas.seguranca.domain.services.validar_cpf import (
    normalizar_cpf,
    validar_cpf,
)


def test_normalizar_cpf():
    assert normalizar_cpf("529.982.247-25") == "52998224725"


@pytest.mark.parametrize(
    "cpf",
    [
        "529.982.247-25",
        "52998224725",
    ],
)
def test_cpf_valido(cpf):
    assert validar_cpf(cpf) is True


@pytest.mark.parametrize(
    "cpf",
    [
        "111.111.111-11",
        "123.456.789-00",
        "123",
        "",
        "abcdefghijk",
        "529.982.247-26",
    ],
)
def test_cpf_invalido(cpf):
    assert validar_cpf(cpf) is False
