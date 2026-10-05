"""Contrato transacional em SQLite; não substitui teste da migration no SQL Server."""
from dataclasses import replace
from copy import deepcopy
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from equivalencia_ementas.academico.application.registrar_extracao import LoteExtracao
from equivalencia_ementas.academico.infrastructure.repositories.resultado_extracao_repository import SqlAlchemyArmazenamentoExtracao

@pytest.fixture
def banco():
    engine=create_engine('sqlite://')
    with engine.begin() as c:
        c.exec_driver_sql("ATTACH DATABASE ':memory:' AS processamento")
        c.exec_driver_sql('''CREATE TABLE processamento.DocumentoFonte (
          DocumentoFonteId INTEGER PRIMARY KEY AUTOINCREMENT, NomeArquivo TEXT, UriArmazenamento TEXT,
          MimeType TEXT, HashSha256 TEXT UNIQUE, TamanhoBytes INTEGER, QuantidadePaginas INTEGER,
          PossuiTextoNativo BOOLEAN, Status TEXT, RecebidoEm DATETIME DEFAULT CURRENT_TIMESTAMP,
          VersaoLinha BLOB DEFAULT X'00')''')
        c.exec_driver_sql('''CREATE TABLE processamento.ResultadoExtracao (
          ResultadoExtracaoId INTEGER PRIMARY KEY AUTOINCREMENT, DocumentoFonteId INTEGER,
          EmentaId INTEGER, NumeroEmenta INTEGER, VersaoExtrator TEXT, DadosExtraidosJson TEXT,
          AuditoriaJson TEXT, DadosRevisadosJson TEXT, Status TEXT, RevisadoPor TEXT, RevisadoEm DATETIME,
          CriadoEm DATETIME DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(DocumentoFonteId,VersaoExtrator,NumeroEmenta))''')
    yield engine,SqlAlchemyArmazenamentoExtracao(sessionmaker(engine))
    engine.dispose()

def lote():
    d={'ementas':[{'numero':1,'dados':{'ementa':'texto'}}]}
    return LoteExtracao('x.pdf','file:///x.pdf','a'*64,100,1,'0.4.2',d,deepcopy(d))

def test_reexecucao_nao_duplica(banco):
    engine,repo=banco
    assert repo.registrar_atomico(lote())==repo.registrar_atomico(lote())
    with engine.connect() as c:
        assert c.scalar(text('SELECT COUNT(*) FROM processamento.ResultadoExtracao'))==1
        assert c.scalar(text('SELECT COUNT(*) FROM processamento.DocumentoFonte'))==1

def test_falha_desfaz_documento_e_primeiro_resultado(banco):
    engine,repo=banco;l=lote()
    l.academico['ementas'].append({'numero':2,'dados':{'invalid':float('nan')}})
    with pytest.raises(ValueError):repo.registrar_atomico(l)
    with engine.connect() as c:
        assert c.scalar(text('SELECT COUNT(*) FROM processamento.ResultadoExtracao'))==0
        assert c.scalar(text('SELECT COUNT(*) FROM processamento.DocumentoFonte'))==0

def test_resultado_divergente_nao_sobrescreve(banco):
    engine,repo=banco;repo.registrar_atomico(lote());l=lote()
    l.academico['ementas'][0]['dados']['ementa']='outro'
    with pytest.raises(ValueError):repo.registrar_atomico(l)
    with engine.connect() as c:
        assert 'outro' not in c.scalar(text('SELECT DadosExtraidosJson FROM processamento.ResultadoExtracao'))
