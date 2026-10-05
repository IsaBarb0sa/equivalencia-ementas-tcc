from copy import deepcopy
import pytest
from ementas_extracao.comum.registros import aproveitar_disciplinas


def analise(total=52.5):
    return {'ementas': [], 'candidatos_inconclusivos': [{
        'numero': 1, 'dados': {'disciplina': 'Tópicos Interdisciplinares',
        'carga_horaria': {'total': total, 'unidade': 'nao_identificada'}, 'ementa': None},
        'identificacao': 'candidato_inconclusivo', 'criterios': {'identidade': True},
        'evidencias': {'disciplina': [{'pagina': 2}], 'carga_horaria': [{'pagina': 2}]},
        'avisos': [], 'inicio': {'pagina': 2}}], 'classificacao': {}}


def test_preserva_dados_e_fontes_sem_inventar_conteudo():
    a = analise()
    original = deepcopy(a['candidatos_inconclusivos'][0])
    aproveitar_disciplinas(a)
    assert a['candidatos_inconclusivos'] == []
    r = a['ementas'][0]
    assert r['dados'] == original['dados']
    assert r['evidencias'] == original['evidencias']
    assert r['identificacao'] == 'disciplina_identificada'
    assert r['status'] == 'pendente_revisao'
    assert a['classificacao']['resultado'] == 'contem_disciplinas'
    anterior = deepcopy(a)
    assert aproveitar_disciplinas(a) == anterior


@pytest.mark.parametrize('total', [None, True, -3, 0, '60', float('nan'), float('inf')])
def test_nao_promove_carga_invalida(total):
    a = aproveitar_disciplinas(analise(total))
    assert not a['ementas']
    assert len(a['candidatos_inconclusivos']) == 1


@pytest.mark.parametrize('campo', ['disciplina', 'carga_horaria'])
def test_exige_evidencia_do_campo(campo):
    a = analise()
    a['candidatos_inconclusivos'][0]['evidencias'].pop(campo)
    assert not aproveitar_disciplinas(a)['ementas']


@pytest.mark.parametrize('titulo', ['ementa', 'programa', 'bibliografia'])
def test_reconhece_titulo_com_caracteres_sobrepostos(titulo):
    from ementas_extracao.comum.segmentacao import cabecalho
    duplicado = ''.join(c * 2 for c in titulo.upper()) + '::'
    assert cabecalho(duplicado) == cabecalho(titulo)


def test_nao_reduz_texto_desconhecido():
    from ementas_extracao.comum.segmentacao import cabecalho
    assert cabecalho('TTOOPPIICCOOSS::') is None


def test_aceita_evidencia_de_carga_do_extrator_generico():
    a = analise()
    e = a['candidatos_inconclusivos'][0]['evidencias']
    e['carga_horaria.total'] = e.pop('carga_horaria')
    assert len(aproveitar_disciplinas(a)['ementas']) == 1
