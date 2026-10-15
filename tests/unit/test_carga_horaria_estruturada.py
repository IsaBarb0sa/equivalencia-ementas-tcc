from decimal import Decimal

import pytest
from sqlalchemy import text

from equivalencia_ementas.academico.domain.entities import Ementa, UnidadeCargaHoraria as U
from .test_importacao_resultado import banco, formulario


def ementa(**kwargs):
    return Ementa(disciplina_id=1, versao='v1', **kwargs)


def test_sem_total_preserva_componentes_sem_inventar_normalizacao():
    e = ementa(carga_horaria_teorica=40, unidade_carga_teorica=U.HORA,
               carga_horaria_total_semanal=4, unidade_carga_total_semanal=U.HORA_AULA)
    assert e.carga_horaria_declarada is None
    assert e.carga_horaria_normalizada_min is None
    with pytest.raises(ValueError):
        e.publicar()


def test_totais_explicitos_e_fracao_de_minuto():
    e = ementa(carga_horaria_total_hora_aula=80,
               carga_horaria_total_hora_relogio=Decimal('66.67'))
    assert e.carga_horaria_normalizada_min == Decimal('4000.20')
    assert e.carga_horaria_total_hora_aula == 80


def test_conflito_de_conversao_mantem_originais_sem_normalizar():
    e = ementa(carga_horaria_total_hora_aula=80,
               carga_horaria_total_hora_relogio=Decimal('66.67'),
               duracao_hora_aula_minutos=50)
    assert e.carga_horaria_normalizada_min is None
    assert e.carga_horaria_total_hora_relogio == Decimal('66.67')


def test_componentes_so_comparam_unidades_compativeis():
    ementa(carga_horaria_declarada=60, carga_horaria_teorica=80,
           unidade_carga_teorica=U.HORA_AULA)
    with pytest.raises(ValueError, match='total compatível'):
        ementa(carga_horaria_declarada=60, carga_horaria_teorica=80,
               unidade_carga_teorica=U.HORA)


def test_carga_semanal_nao_compara_com_total_semestral():
    ementa(carga_horaria_declarada=2, carga_horaria_total_semanal=4)
    with pytest.raises(ValueError, match='total compatível'):
        ementa(carga_horaria_total_semanal=4, unidade_carga_total_semanal=U.HORA_AULA,
               carga_horaria_teorica_semanal=5, unidade_carga_teorica_semanal=U.HORA_AULA)


@pytest.mark.parametrize('valor', [True, -1, float('nan'), float('inf'), Decimal('1.001')])
def test_rejeita_numeros_invalidos(valor):
    with pytest.raises(ValueError):
        ementa(carga_horaria_total_hora_aula=valor)


def test_nao_aceita_minutos_inventados():
    with pytest.raises(ValueError, match='evidência'):
        ementa(carga_horaria_declarada=80, unidade_carga_horaria=U.HORA_AULA,
               carga_horaria_normalizada_min=4000)


def test_importador_preserva_novos_campos_e_repeticao(banco):
    engine, caso = banco
    f = formulario(caso)
    f['dados']['carga_horaria'] = {
        'total': None, 'total_hora_aula': 80, 'total_hora_relogio': 66.67,
        'teorica_semanal': 3, 'pratica_semanal': 1, 'total_semanal': 4,
        'unidade_teorica_semanal': 'HORA_AULA',
        'unidade_pratica_semanal': 'HORA_AULA', 'unidade_total_semanal': 'HORA_AULA',
    }
    caso.executar(f, False)
    assert caso.executar(f, False)['situacao'] == 'ja_importado'
    with engine.connect() as c:
        row = c.execute(text('SELECT * FROM academico.Ementa')).mappings().one()
        assert row['CargaHorariaDeclarada'] is None
        assert row['CargaHorariaTotalHoraAula'] == 80
        assert row['CargaHorariaTotalHoraRelogio'] == pytest.approx(66.67)
        assert row['CargaHorariaNormalizadaMin'] == pytest.approx(4000.2)
        assert row['CargaHorariaTeoricaSemanal'] == 3
        assert row['CargaHorariaPraticaSemanal'] == 1
        assert row['UnidadeCargaTotalSemanal'] == 'HORA_AULA'
        assert row['Status'] == 'EM_REVISAO'


def test_importador_aceita_sem_carga(banco):
    engine, caso = banco
    f = formulario(caso)
    f['dados']['carga_horaria'] = {}
    caso.executar(f, False)
    with engine.connect() as c:
        assert c.scalar(text('SELECT CargaHorariaDeclarada FROM academico.Ementa')) is None


def test_simulacao_detecta_migration_ausente(banco):
    engine, caso = banco
    with engine.begin() as c:
        c.exec_driver_sql('ALTER TABLE academico.Ementa DROP COLUMN CargaHorariaTotalHoraAula')
    with pytest.raises(ValueError, match='migration 004'):
        caso.executar(formulario(caso))


def test_repositorio_orm_preserva_cargas_e_unidades():
    from equivalencia_ementas.academico.infrastructure.repositories.ementa_repository import SqlAlchemyEmentaRepository

    class Sessao:
        def add(self, model):
            self.model = model
        def flush(self):
            self.model.ementa_id = 99

    sessao = Sessao()
    repo = SqlAlchemyEmentaRepository(sessao)
    original = ementa(carga_horaria_total_hora_relogio=Decimal('66.67'),
                      carga_horaria_total_hora_aula=80,
                      carga_horaria_teorica_semanal=4,
                      unidade_carga_teorica_semanal=U.HORA_AULA)
    repo.adicionar(original)
    restaurada = repo._converter_para_entidade(sessao.model)
    assert restaurada == original


def test_totais_duplicados_conflitantes_impedem_normalizacao():
    e = ementa(carga_horaria_declarada=60, unidade_carga_horaria=U.HORA_AULA,
               carga_horaria_total_hora_aula=80, carga_horaria_total_hora_relogio=40)
    assert e.carga_horaria_normalizada_min is None
