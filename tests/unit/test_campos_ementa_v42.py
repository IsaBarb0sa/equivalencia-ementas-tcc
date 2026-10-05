from decimal import Decimal
import pytest
from equivalencia_ementas.academico.domain.entities import Ementa, UnidadeCargaHoraria


def criar(**kwargs):
    return Ementa(disciplina_id=1, versao='teste', carga_horaria_declarada=Decimal('80'), **kwargs)


def test_componentes_e_competencias():
    e = criar(carga_horaria_teorica=40,carga_horaria_pratica=40, competencias_habilidades='  Anatomia  ')
    assert e.carga_horaria_teorica == Decimal('40')
    assert e.competencias_habilidades == 'Anatomia'


def test_desconhecido_diferente_de_zero():
    assert criar().carga_horaria_pratica is None
    assert criar(carga_horaria_pratica=0).carga_horaria_pratica == 0


@pytest.mark.parametrize('kwargs',[
    {'carga_horaria_teorica':-1}, {'carga_horaria_pratica':81},
    {'carga_horaria_teorica':50,'carga_horaria_pratica':40},
    {'carga_horaria_teorica':Decimal('NaN')},
    {'carga_horaria_pratica':Decimal('1.001')},
    {'unidade_carga_horaria':UnidadeCargaHoraria.NAO_INFO,'carga_horaria_normalizada_min':4800},
])
def test_recusa_valores_inconsistentes(kwargs):
    with pytest.raises(ValueError):criar(**kwargs)


def test_unidade_desconhecida_aceita_rascunho_impede_publicacao():
    e=criar(unidade_carga_horaria=UnidadeCargaHoraria.NAO_INFO,resumo='Texto')
    with pytest.raises(ValueError):e.publicar()


def test_legado_continua_com_hora():
    assert criar().unidade_carga_horaria == UnidadeCargaHoraria.HORA
