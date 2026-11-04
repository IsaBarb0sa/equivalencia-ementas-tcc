import json
from pathlib import Path

import pytest


ARQUIVO_REFERENCIAS = (
    Path(__file__).parent
    / "dados_avaliacao"
    / "referencias_v1.json"
)

CLASSIFICACOES_VALIDAS = {
    "correspondente",
    "parcialmente_relacionado",
    "nao_correspondente",
    "inconclusivo",
}


@pytest.fixture
def referencias():
    with ARQUIVO_REFERENCIAS.open(
        "r",
        encoding="utf-8",
    ) as arquivo:
        dados = json.load(arquivo)

    return dados["referencias"]


def test_referencias_possuem_identificadores_unicos(
    referencias,
):
    identificadores = [
        referencia["id"]
        for referencia in referencias
    ]

    assert len(identificadores) == len(
        set(identificadores)
    )


def test_referencias_possuem_campos_obrigatorios(
    referencias,
):
    for referencia in referencias:
        assert referencia["id"]
        assert referencia["area"]
        assert referencia["origem"]
        assert referencia["destino"]
        assert referencia["justificativa"]


def test_origem_e_destino_possuem_dados_necessarios(
    referencias,
):
    for referencia in referencias:
        for lado in ("origem", "destino"):
            dados = referencia[lado]

            assert dados["arquivo"]
            assert dados["disciplina"]
            assert dados["secao"]
            assert dados["texto"]


def test_classificacoes_propostas_sao_validas(
    referencias,
):
    for referencia in referencias:
        assert (
            referencia["classificacao_proposta"]
            in CLASSIFICACOES_VALIDAS
        )


def test_classificacoes_validadas_sao_validas_ou_pendentes(
    referencias,
):
    for referencia in referencias:
        classificacao = referencia[
            "classificacao_validada"
        ]

        assert (
            classificacao is None
            or classificacao in CLASSIFICACOES_VALIDAS
        )


def test_conjunto_de_referencias_nao_esta_vazio(
    referencias,
):
    assert len(referencias) > 0