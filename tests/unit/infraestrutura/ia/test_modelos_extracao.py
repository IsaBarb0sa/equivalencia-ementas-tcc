from equivalencia_ementas.infraestrutura.ia.modelos_extracao import (
    CargaHorariaExtraida,
)


def test_carga_horaria_simples():
    carga = CargaHorariaExtraida(
        total=60,
        unidade="HORA_AULA",
    )

    assert carga.total == 60
    assert carga.total_hora_aula is None
    assert carga.total_hora_relogio is None


def test_carga_horaria_com_hora_aula_e_hora_relogio():
    carga = CargaHorariaExtraida(
        total_hora_aula=72,
        total_hora_relogio=60,
        teorica_semanal=3,
        pratica_semanal=1,
    )

    assert carga.total is None
    assert carga.total_hora_aula == 72
    assert carga.total_hora_relogio == 60
    assert carga.teorica_semanal == 3
    assert carga.pratica_semanal == 1


def test_modelo_continua_aceitando_formato_antigo():
    carga = CargaHorariaExtraida(
        total=72,
        teorica=3,
        pratica=1,
        unidade="HORA_AULA",
    )

    assert carga.total == 72
    assert carga.teorica == 3
    assert carga.pratica == 1