from dataclasses import replace
from copy import deepcopy
import pytest
from equivalencia_ementas.academico.application.registrar_extracao import LoteExtracao, RegistrarExtracao

class Memoria:
    def __init__(self):self.chamadas=0
    def registrar_atomico(self,lote):self.chamadas+=1;return [1]

def lote():
    d={'documento':{'sha256':'a'*64,'total_paginas':1},'versao_extrator':'0.4.2',
       'ementas':[{'numero':1,'dados':{'instituicao':None}}]}
    return LoteExtracao('x.pdf','file:///x.pdf','a'*64,100,1,'0.4.2',d,deepcopy(d))

def test_registra_pendente_mesmo_sem_instituicao():
    a=Memoria();assert RegistrarExtracao(a).executar(lote())==[1]

@pytest.mark.parametrize('campo,valor',[('hash_sha256','b'*64),('paginas',2),('versao_extrator','outra')])
def test_recusa_documentos_divergentes(campo,valor):
    a=Memoria()
    with pytest.raises(ValueError):RegistrarExtracao(a).executar(replace(lote(),**{campo:valor}))
    assert a.chamadas==0

def test_recusa_dados_editados_sem_revisao():
    l=lote();l.academico['ementas'][0]['dados']['instituicao']='alterado'
    with pytest.raises(ValueError):RegistrarExtracao(Memoria()).executar(l)
