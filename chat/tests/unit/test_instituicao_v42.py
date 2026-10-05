import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from ementas_extracao.instituicao import reconhecer_alias, aplicar_evidencias, NOME_UNIPAC


def registro(nome=None):
    return {'dados':{'instituicao':nome},'metodo_segmentacao':'perfil_plano_aprendizagem_unico','avisos':[]}


def test_alias_exato():
    assert reconhecer_alias('UNIPAC')
    assert not reconhecer_alias('UNIPACIFIC')


def test_associacao_preserva_fonte():
    a={'ementas':[registro()],'candidatos_inconclusivos':[]}
    fontes=[{'pagina':22,'texto':'UNIPAC','metodo':'ocr'}]
    aplicar_evidencias(a,fontes)
    assert a['ementas'][0]['dados']['instituicao']==NOME_UNIPAC
    assert a['ementas'][0]['evidencias']['instituicao']==fontes


def test_nao_propaga_em_multiplas_ementas():
    a={'ementas':[registro(),registro()],'candidatos_inconclusivos':[]}
    aplicar_evidencias(a,[{'pagina':1,'texto':'UNIPAC'}])
    assert a['ementas'][0]['dados']['instituicao'] is None


def test_nao_sobrescreve_instituicao_divergente():
    a={'ementas':[registro('Outra Faculdade')],'candidatos_inconclusivos':[]}
    aplicar_evidencias(a,[{'pagina':1,'texto':'UNIPAC'}])
    assert a['ementas'][0]['dados']['instituicao']=='Outra Faculdade'
