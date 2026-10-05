from pathlib import Path
import pytest
from ementas_extracao.comum.documento import ler_linhas
from ementas_extracao.extratores.aprendiz import extrair
from ementas_extracao.roteamento import selecionar

PASTA = Path(__file__).resolve().parents[1] / 'fixtures' / 'ementas' / 'aprendiz'


@pytest.mark.parametrize('nome,quantidade,inconclusivos', [
    ('direito_completo.pdf', 69, 0), ('direito_recente.pdf', 9, 0),
    ('odontologia.pdf', 17, 0), ('historico.pdf', 0, 0),
])
def test_documentos_aprendiz(nome, quantidade, inconclusivos):
    caminho = PASTA / nome
    assert caminho.is_file(), f'PDF não encontrado: {caminho}'
    linhas, paginas = ler_linhas(caminho)
    a = extrair(caminho, linhas, paginas)
    assert len(a['ementas']) == quantidade
    assert len(a['candidatos_inconclusivos']) == inconclusivos
    if nome == 'direito_completo.pdf':
        r = a['ementas'][0]['dados']
        assert r['disciplina'] == 'Introdução à Economia'
        assert r['carga_horaria']['total'] == 36
        assert r['carga_horaria']['unidade'] == 'hora_aula'
        assert r['carga_horaria']['teorica'] is None
        assert r['bibliografia']['basica'] and r['conteudo_programatico']
        portugues = [r for r in a['ementas'] if r['dados']['disciplina'] == 'Português Instrumental II']
        assert len(portugues) == 1
        assert portugues[0]['dados']['carga_horaria']['total'] == 36
        tributario = [r for r in a['ementas'] if r['dados']['disciplina'] == 'Direito Tributário II']
        assert len(tributario) == 1
        assert tributario[0]['dados']['ementa']
    if nome == 'direito_recente.pdf':
        parciais = [r for r in a['ementas'] if r['identificacao'] == 'disciplina_identificada']
        assert {r['inicio']['pagina'] for r in parciais} == {3, 5, 6}
        assert all(r['dados']['ementa'] is None for r in parciais)
        assert sorted(r['dados']['carga_horaria']['total'] for r in parciais) == [40, 40, 60]
        assert all(r['dados']['disciplina'] and 'registro_parcial' in r['avisos'] for r in parciais)
        assert 'LÔBO' in a['ementas'][0]['dados']['bibliografia']['basica']
        assert all(r['dados']['disciplina'] != 'EAD' for r in a['ementas'])
    if nome == 'odontologia.pdf':
        r = a['ementas'][0]['dados']
        assert r['disciplina'] == 'Anatomia Dentária'
        assert r['curso'] == 'Odontologia'
        assert r['carga_horaria'] == {
            'total': 30, 'teorica': 10, 'pratica': 20, 'unidade': 'nao_identificada'
        }
        assert all(r['dados']['bibliografia']['basica'] and
                   r['dados']['bibliografia']['complementar'] for r in a['ementas'])


def test_perfil_aprendiz_ativado():
    executor, meta = selecionar('aprendiz')
    assert executor is extrair
    assert meta['perfil_utilizado'] == 'aprendiz'
    assert meta['fallback_generico'] is False
