"""Integração em SQLite com schemas anexados; não valida locks/DDL do SQL Server."""
import json
from copy import deepcopy
from decimal import Decimal
import pytest
from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker
from equivalencia_ementas.academico.application.importar_resultado import ImportarResultado,validar
from equivalencia_ementas.academico.infrastructure.repositories.importacao_resultado_repository import SqlAlchemyImportacaoResultado

DADOS={'instituicao':'Instituição Teste','curso':'Odontologia','disciplina':'Anatomia',
    'ementa':'Morfologia da cabeça e pescoço.','carga_horaria':{'total':80,'teorica':40,'pratica':40,'unidade':'nao_identificada'},
    'objetivos':{'nao_classificados':'Identificar estruturas.'},'competencias_habilidades':'Reconhecer estruturas.',
    'conteudo_programatico':'Osteologia\nMiologia', 'bibliografia':{'basica':'Livro A\nLivro B','complementar':'Livro C'}}

@pytest.fixture
def banco():
    engine=create_engine('sqlite://')
    ddl=[
    '''CREATE TABLE processamento.ResultadoExtracao(ResultadoExtracaoId INTEGER PRIMARY KEY,
    DocumentoFonteId INTEGER,NumeroEmenta INTEGER,VersaoExtrator TEXT,DadosExtraidosJson TEXT,
    AuditoriaJson TEXT,DadosRevisadosJson TEXT,Status TEXT,EmentaId INTEGER,RevisadoPor TEXT,RevisadoEm DATETIME)''',
    '''CREATE TABLE academico.Instituicao(InstituicaoId INTEGER PRIMARY KEY AUTOINCREMENT,Codigo TEXT UNIQUE,Nome TEXT,Ativa BOOLEAN)''',
    '''CREATE TABLE academico.Curso(CursoId INTEGER PRIMARY KEY AUTOINCREMENT,InstituicaoId INTEGER,Codigo TEXT,Nome TEXT,Nivel TEXT,Modalidade TEXT,Ativo BOOLEAN,UNIQUE(InstituicaoId,Codigo))''',
    '''CREATE TABLE academico.Disciplina(DisciplinaId INTEGER PRIMARY KEY AUTOINCREMENT,InstituicaoId INTEGER,Codigo TEXT,Nome TEXT,Ativa BOOLEAN,UNIQUE(InstituicaoId,Codigo))''',
    '''CREATE TABLE academico.Ementa(EmentaId INTEGER PRIMARY KEY AUTOINCREMENT,DisciplinaId INTEGER,MatrizDisciplinaId INTEGER,DocumentoFonteId INTEGER,Versao TEXT,Idioma TEXT,Resumo TEXT,CargaHorariaDeclarada NUMERIC,CargaHorariaTeorica NUMERIC,CargaHorariaPratica NUMERIC,CompetenciasHabilidades TEXT,UnidadeCargaHoraria TEXT,DuracaoHoraAulaMinutos INTEGER,CargaHorariaNormalizadaMin INTEGER,Status TEXT)''',
    '''CREATE TABLE academico.EmentaCurso(EmentaId INTEGER,CursoId INTEGER,PRIMARY KEY(EmentaId,CursoId))''',
    '''CREATE TABLE academico.ObjetivoEmenta(ObjetivoEmentaId INTEGER PRIMARY KEY AUTOINCREMENT,EmentaId INTEGER,Ordem INTEGER,Tipo TEXT,Texto TEXT)''',
    '''CREATE TABLE academico.ConteudoProgramatico(ConteudoProgramaticoId INTEGER PRIMARY KEY AUTOINCREMENT,EmentaId INTEGER,Ordem INTEGER,TextoOriginal TEXT)''',
    '''CREATE TABLE academico.Bibliografia(BibliografiaId INTEGER PRIMARY KEY AUTOINCREMENT,EmentaId INTEGER,Ordem INTEGER,Tipo TEXT,ReferenciaTexto TEXT)''']
    with engine.begin() as c:
        for schema in ('academico','processamento'):c.exec_driver_sql(f"ATTACH DATABASE ':memory:' AS {schema}")
        for sql in ddl:c.exec_driver_sql(sql)
        c.execute(text('''INSERT INTO processamento.ResultadoExtracao(ResultadoExtracaoId,DocumentoFonteId,NumeroEmenta,VersaoExtrator,DadosExtraidosJson,AuditoriaJson,Status)
        VALUES(1,1,1,'0.4.2',:dados,'{}','PENDENTE')'''),{'dados':json.dumps(DADOS)})
    caso=ImportarResultado(SqlAlchemyImportacaoResultado(sessionmaker(engine)))
    yield engine,caso
    engine.dispose()


def formulario(caso):
    form=caso.preparar(1);form['confirmado']=True;form['revisado_por']='Revisora'
    form['cadastro']={'instituicao_codigo':'TESTE','curso_codigo':'ODONTO','disciplina_codigo':'ANATOMIA',
        'curso_nivel':'GRADUACAO','curso_modalidade':'PRESENCIAL','versao_ementa':'2019-1'}
    return form


def count(engine,tabela):
    with engine.connect() as c:return c.scalar(text(f'SELECT COUNT(*) FROM academico.{tabela}'))


def test_preparar_sem_mudar_banco(banco):
    engine,caso=banco;form=caso.preparar(1)
    assert form['dados']==DADOS and form['confirmado'] is False
    assert count(engine,'Ementa')==0


def test_aceita_envelope_legado(banco):
    engine,caso=banco
    with engine.begin() as c:c.execute(text('UPDATE processamento.ResultadoExtracao SET DadosExtraidosJson=:d'),{'d':json.dumps({'dados':DADOS,'numero':1})})
    assert caso.preparar(1)['dados']==DADOS


def test_simular_sem_inserir(banco):
    engine,caso=banco;r=caso.executar(formulario(caso))
    assert r['situacao']=='simulacao_sem_gravacao'
    for t in ('Instituicao','Curso','Disciplina','Ementa'):assert count(engine,t)==0


def test_importa_banco_vazio_preservando_original_e_textos(banco):
    engine,caso=banco;r=caso.executar(formulario(caso),False)
    assert r['situacao']=='importado'
    for t in ('Instituicao','Curso','Disciplina','Ementa','EmentaCurso','ObjetivoEmenta','ConteudoProgramatico'):assert count(engine,t)==1
    assert count(engine,'Bibliografia')==2
    with engine.connect() as c:
        row=c.execute(text('SELECT * FROM processamento.ResultadoExtracao')).mappings().one()
        assert json.loads(row['DadosExtraidosJson'])==DADOS
        assert row['Status']=='IMPORTADO' and row['EmentaId']==r['ementa_id']
        e=c.execute(text('SELECT * FROM academico.Ementa')).mappings().one()
        assert e['Status']=='EM_REVISAO' and e['UnidadeCargaHoraria']=='NAO_INFO'
        assert e['CargaHorariaNormalizadaMin'] is None and e['MatrizDisciplinaId'] is None
        assert e['CargaHorariaTeorica']==40
        assert c.scalar(text('SELECT Tipo FROM academico.ObjetivoEmenta'))=='NAO_CLASSIF'
        assert c.scalar(text("SELECT ReferenciaTexto FROM academico.Bibliografia WHERE Tipo='BASICA'"))=='Livro A\nLivro B'


def test_repeticao_nao_duplica(banco):
    engine,caso=banco;form=formulario(caso)
    primeiro=caso.executar(form,False);segundo=caso.executar(form,False)
    assert primeiro['ementa_id']==segundo['ementa_id'] and segundo['situacao']=='ja_importado'
    assert count(engine,'Ementa')==1


def test_impede_revisao_divergente_apos_importar(banco):
    engine,caso=banco;form=formulario(caso);caso.executar(form,False)
    form['dados']['ementa']='Mudança'
    with pytest.raises(ValueError,match='outra revisão'):caso.executar(form,False)


def test_impede_origem_alterada(banco):
    engine,caso=banco;form=formulario(caso)
    with engine.begin() as c:c.execute(text("UPDATE processamento.ResultadoExtracao SET AuditoriaJson='{} '"))
    with pytest.raises(ValueError,match='Origem mudou'):caso.executar(form,False)
    assert count(engine,'Instituicao')==0


def test_rollback_integral_falha_bibliografia(banco):
    engine,caso=banco
    with engine.begin() as c:c.exec_driver_sql("CREATE TRIGGER academico.falhar BEFORE INSERT ON Bibliografia BEGIN SELECT RAISE(ABORT,'falha simulada'); END")
    with pytest.raises(Exception,match='falha simulada'):caso.executar(formulario(caso),False)
    for t in ('Instituicao','Curso','Disciplina','Ementa','EmentaCurso','ObjetivoEmenta'):assert count(engine,t)==0
    with engine.connect() as c:assert c.scalar(text('SELECT Status FROM processamento.ResultadoExtracao'))=='PENDENTE'


def test_codigo_existente_divergente(banco):
    engine,caso=banco
    with engine.begin() as c:c.execute(text("INSERT INTO academico.Instituicao(Codigo,Nome,Ativa) VALUES('TESTE','Outro nome',1)"))
    with pytest.raises(ValueError,match='dados diferentes'):caso.executar(formulario(caso),False)


def test_reutiliza_cadastros(banco):
    engine,caso=banco
    with engine.begin() as c:
        c.execute(text("INSERT INTO academico.Instituicao VALUES(7,'TESTE','Instituição Teste',1)"))
        c.execute(text("INSERT INTO academico.Curso VALUES(8,7,'ODONTO','Odontologia','GRADUACAO','PRESENCIAL',1)"))
        c.execute(text("INSERT INTO academico.Disciplina VALUES(9,7,'ANATOMIA','Anatomia',1)"))
    r=caso.executar(formulario(caso),False)
    assert r['instituicao_id']==7 and r['curso_id']==8 and r['disciplina_id']==9
    for t in ('Instituicao','Curso','Disciplina'):assert count(engine,t)==1


@pytest.mark.parametrize('alteracao',[
    lambda f:f.update(confirmado=False),
    lambda f:f.update(revisado_por=''),
    lambda f:f['cadastro'].update(curso_codigo=None),
    lambda f:f['cadastro'].update(curso_modalidade='SEM_DADO'),
    lambda f:f['dados']['carga_horaria'].update(total=0),
    lambda f:f['dados']['carga_horaria'].update(total=float('nan')),
    lambda f:f['dados']['carga_horaria'].update(teorica=50),
    lambda f:f['dados']['carga_horaria'].update(pratica=-1),
    lambda f:f['dados']['carga_horaria'].update(unidade='HORA_AULA'),
])
def test_bloqueia_revisao_invalida(banco,alteracao):
    engine,caso=banco;f=formulario(caso);alteracao(f)
    with pytest.raises(ValueError):caso.executar(f,False)
    assert count(engine,'Ementa')==0


def test_hora_aula_confirmada(banco):
    _,caso=banco;f=formulario(caso)
    f['dados']['carga_horaria'].update(unidade='HORA_AULA',duracao_hora_aula_minutos=50)
    assert validar(f).duracao_hora_aula_minutos==50

def test_importa_registro_parcial_com_campos_nulos(banco):
    engine, caso = banco
    f = formulario(caso)
    f['dados'].update(ementa=None, objetivos=None, competencias_habilidades=None,
                      conteudo_programatico=None, bibliografia=None)
    f['dados']['carga_horaria'].update(teorica=None, pratica=None)
    r = caso.executar(f, False)
    assert r['situacao'] == 'importado'
    with engine.connect() as c:
        e = c.execute(text('SELECT * FROM academico.Ementa')).mappings().one()
        assert e['Resumo'] is None
        assert e['CargaHorariaDeclarada'] == 80
        assert e['CargaHorariaTeorica'] is None
        assert e['CompetenciasHabilidades'] is None
        assert e['Status'] == 'EM_REVISAO'
    for tabela in ('ObjetivoEmenta', 'Bibliografia', 'ConteudoProgramatico'):
        assert count(engine, tabela) == 0
