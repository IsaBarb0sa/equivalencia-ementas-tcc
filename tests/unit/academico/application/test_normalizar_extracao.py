from equivalencia_ementas.academico.application.normalizar_extracao import (
    normalizar_extracao,
    normalizar_texto,
)
from equivalencia_ementas.infraestrutura.ia.modelos_extracao import (
    BibliografiaExtraida,
    CargaHorariaExtraida,
    DisciplinaExtraida,
    DocumentoAcademicoExtraido,
)


def test_normalizar_texto_nao_ha_para_none():
    assert normalizar_texto("Não há") is None


def test_normalizar_texto_nao_se_aplica_para_none():
    assert normalizar_texto("Não se aplica.") is None


def test_normalizar_texto_remove_espacos_extras():
    resultado = normalizar_texto(
        "  Direito   Civil   V  "
    )

    assert resultado == "Direito Civil V"


def test_normalizar_paginas_repetidas():
    documento = DocumentoAcademicoExtraido(
        instituicao="Teste",
        disciplinas=[
            DisciplinaExtraida(
                nome="Cálculo I",
                paginas_origem=[
                    3,
                    1,
                    3,
                    2,
                    2,
                ],
            )
        ],
    )

    resultado = normalizar_extracao(
        documento
    )

    assert (
        resultado.disciplinas[0].paginas_origem
        == [1, 2, 3]
    )


def test_normalizar_observacoes_repetidas():
    documento = DocumentoAcademicoExtraido(
        disciplinas=[
            DisciplinaExtraida(
                nome="Cálculo I",
                observacoes=[
                    "Disciplina optativa",
                    "Disciplina optativa",
                    "  Disciplina optativa  ",
                ],
            )
        ]
    )

    resultado = normalizar_extracao(
        documento
    )

    assert (
        resultado.disciplinas[0].observacoes
        == ["Disciplina optativa"]
    )


def test_normalizar_bibliografia_ausente():
    documento = DocumentoAcademicoExtraido(
        disciplinas=[
            DisciplinaExtraida(
                nome="Atividades de Extensão",
                carga_horaria=CargaHorariaExtraida(
                    total=40,
                    unidade="HORA_AULA",
                ),
                bibliografia=BibliografiaExtraida(
                    basica="Não há",
                    complementar="Não se aplica.",
                ),
            )
        ]
    )

    resultado = normalizar_extracao(
        documento
    )

    disciplina = resultado.disciplinas[0]

    assert disciplina.bibliografia.basica is None
    assert disciplina.bibliografia.complementar is None

def test_normalizar_bibliografia_com_rotulo_e_nao_ha():
    resultado = normalizar_texto(
        "BIBLIOGRAFIA BÁSICA COMPLEMENTAR: Não há"
    )

    assert resultado is None