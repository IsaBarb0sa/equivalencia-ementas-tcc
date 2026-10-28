from equivalencia_ementas.infraestrutura.ia.modelos_extracao import (
    CargaHorariaExtraida,
)


def test_carga_horaria_simples():
    carga = CargaHorariaExtraida(
        total=60,
        unidade="HORA_AULA",
    )

    assert carga.total == 60
    assert carga.teorica is None
    assert carga.pratica is None
    assert carga.unidade == "HORA_AULA"


def test_campos_antigos_nao_sao_utilizados():
    carga = CargaHorariaExtraida.model_validate(
        {
            "total_hora_aula": 72,
            "total_hora_relogio": 60,
            "teorica_semanal": 3,
            "pratica_semanal": 1,
        }
    )

    assert carga.total is None
    assert carga.teorica is None
    assert carga.pratica is None
    assert carga.unidade is None


def test_modelo_aceita_campos_atuais():
    carga = CargaHorariaExtraida(
        total=72,
        teorica=40,
        pratica=32,
        unidade="HORA_AULA",
    )

    assert carga.total == 72
    assert carga.teorica == 40
    assert carga.pratica == 32
    assert carga.unidade == "HORA_AULA"


def test_carga_horaria_ausente():
    carga = CargaHorariaExtraida()

    assert carga.total is None
    assert carga.teorica is None
    assert carga.pratica is None
    assert carga.unidade is None


def test_carga_horaria_nao_calcula_valores_ausentes():
    carga = CargaHorariaExtraida(
        teorica=40,
        pratica=40,
    )

    assert carga.total is None