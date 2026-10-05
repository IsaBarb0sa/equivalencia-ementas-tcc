"""Seleção não presume cobertura de instituições ainda não implementadas."""
import pytest
from ementas_extracao.roteamento import selecionar
from ementas_extracao.extratores.generico import extrair


@pytest.mark.parametrize('instituicao', ['estacio', 'anhanguera_unopar'])
def test_perfil_pendente_usa_generico_explicitamente(instituicao):
    executor, meta = selecionar(instituicao)
    assert executor is extrair
    assert meta['perfil_utilizado'] == 'generico'
    assert meta['instituicao_solicitada'] == instituicao
    assert meta['fallback_generico'] is True
    assert meta['motivo'] == 'perfil_especifico_pendente'


def test_instituicao_desconhecida_nao_e_ignorada():
    with pytest.raises(ValueError, match='desconhecido'):
        selecionar('nome_digitado_incorretamente')
