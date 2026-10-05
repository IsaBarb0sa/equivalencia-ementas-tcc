from datetime import UTC, datetime
from decimal import Decimal

import pytest

from equivalencia_ementas.academico.domain.entities import (
    Ementa,
    StatusEmenta,
    UnidadeCargaHoraria,
)


def test_deve_criar_ementa_valida() -> None:
    ementa = Ementa(
        disciplina_id=1,
        matriz_disciplina_id=1,
        versao=" 2019/2 ",
        ano_vigencia=2019,
        semestre_vigencia=2,
        resumo=" Realização do exame clínico. ",
        carga_horaria_declarada=Decimal("40"),
    )

    assert ementa.disciplina_id == 1
    assert ementa.matriz_disciplina_id == 1
    assert ementa.versao == "2019/2"
    assert ementa.resumo == "Realização do exame clínico."
    assert ementa.carga_horaria_declarada == Decimal("40")
    assert ementa.status == StatusEmenta.RASCUNHO


def test_deve_rejeitar_carga_horaria_igual_a_zero() -> None:
    with pytest.raises(
        ValueError,
        match="carga horária declarada deve ser maior que zero",
    ):
        Ementa(
            disciplina_id=1,
            versao="2019/2",
            carga_horaria_declarada=Decimal("0"),
        )


def test_deve_rejeitar_semestre_sem_ano() -> None:
    with pytest.raises(
        ValueError,
        match="Não é possível informar o semestre sem o ano",
    ):
        Ementa(
            disciplina_id=1,
            versao="2019/2",
            semestre_vigencia=2,
            carga_horaria_declarada=Decimal("40"),
        )


def test_deve_rejeitar_semestre_invalido() -> None:
    with pytest.raises(
        ValueError,
        match="semestre de vigência deve ser 1 ou 2",
    ):
        Ementa(
            disciplina_id=1,
            versao="2019/2",
            ano_vigencia=2019,
            semestre_vigencia=3,
            carga_horaria_declarada=Decimal("40"),
        )


def test_deve_exigir_duracao_quando_unidade_for_hora_aula() -> None:
    with pytest.raises(
        ValueError,
        match="duração da hora-aula deve ser informada",
    ):
        Ementa(
            disciplina_id=1,
            versao="2019/2",
            carga_horaria_declarada=Decimal("40"),
            unidade_carga_horaria=UnidadeCargaHoraria.HORA_AULA,
        )


def test_deve_rejeitar_confianca_de_parsing_invalida() -> None:
    with pytest.raises(
        ValueError,
        match="confiança do parsing deve estar entre zero e um",
    ):
        Ementa(
            disciplina_id=1,
            versao="2019/2",
            carga_horaria_declarada=Decimal("40"),
            confianca_parsing=Decimal("1.10"),
        )


def test_deve_publicar_ementa_com_texto() -> None:
    ementa = Ementa(
        disciplina_id=1,
        versao="2019/2",
        resumo="Realização do exame clínico.",
        carga_horaria_declarada=Decimal("40"),
    )

    ementa.publicar()

    assert ementa.status == StatusEmenta.PUBLICADA
    assert isinstance(ementa.publicada_em, datetime)
    assert ementa.publicada_em <= datetime.now(UTC).replace(tzinfo=None)


def test_nao_deve_publicar_ementa_sem_texto() -> None:
    ementa = Ementa(
        disciplina_id=1,
        versao="2019/2",
        carga_horaria_declarada=Decimal("40"),
    )

    with pytest.raises(
        ValueError,
        match="Não é possível publicar uma ementa sem texto",
    ):
        ementa.publicar()


def test_deve_atribuir_identificador_uma_unica_vez() -> None:
    ementa = Ementa(
        disciplina_id=1,
        versao="2019/2",
        carga_horaria_declarada=Decimal("40"),
    )

    ementa.atribuir_id(10)

    assert ementa.ementa_id == 10

    with pytest.raises(
        ValueError,
        match="já possui um identificador",
    ):
        ementa.atribuir_id(11)
