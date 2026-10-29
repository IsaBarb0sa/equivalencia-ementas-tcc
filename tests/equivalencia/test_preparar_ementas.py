import json

import pytest

from equivalencia_ementas.equivalencia.application.preparar_ementas import (
    ErroPreparacaoEmentas,
    preparar_disciplinas,
    preparar_disciplinas_json,
)


def test_preparar_disciplina_completa():
    dados = {
        "resultado": {
            "instituicao": "Instituição de Exemplo",
            "curso": "Curso de Exemplo",
            "disciplinas": [
                {
                    "nome": "Disciplina A",
                    "ementa": "Introdução ao conteúdo A.",
                    "conteudo_programatico": "Tema 1. Tema 2.",
                    "objetivos": {
                        "geral": "Compreender o conteúdo.",
                        "especificos": None,
                    },
                    "carga_horaria": {
                        "total": 80,
                        "teorica": 40,
                        "pratica": 40,
                        "unidade": "HORA_AULA",
                    },
                }
            ],
        }
    }

    disciplinas = preparar_disciplinas(dados)

    assert len(disciplinas) == 1

    disciplina = disciplinas[0]

    assert disciplina.nome == "Disciplina A"
    assert disciplina.instituicao == "Instituição de Exemplo"
    assert disciplina.curso == "Curso de Exemplo"
    assert disciplina.ementa == "Introdução ao conteúdo A."
    assert disciplina.objetivo_geral == "Compreender o conteúdo."
    assert disciplina.carga_horaria.total == 80
    assert disciplina.carga_horaria.teorica == 40
    assert disciplina.carga_horaria.pratica == 40


def test_preservar_disciplina_incompleta():
    dados = {
        "disciplinas": [
            {
                "nome": "Disciplina B",
                "carga_horaria": {"total": 60},
            }
        ]
    }

    disciplinas = preparar_disciplinas(dados)

    assert len(disciplinas) == 1
    assert disciplinas[0].nome == "Disciplina B"
    assert disciplinas[0].carga_horaria.total == 60
    assert not disciplinas[0].possui_conteudo_semantico()


def test_documento_com_varias_disciplinas():
    dados = {
        "disciplinas": [
            {"nome": "Disciplina A"},
            {"nome": "Disciplina B"},
            {"nome": "Disciplina C"},
        ]
    }

    disciplinas = preparar_disciplinas(dados)

    assert len(disciplinas) == 3
    assert [d.nome for d in disciplinas] == [
        "Disciplina A",
        "Disciplina B",
        "Disciplina C",
    ]


def test_documento_sem_disciplinas():
    dados = {"disciplinas": []}

    assert preparar_disciplinas(dados) == []


def test_rejeitar_lista_invalida():
    dados = {"disciplinas": "valor inválido"}

    with pytest.raises(ErroPreparacaoEmentas):
        preparar_disciplinas(dados)


def test_rejeitar_carga_horaria_invalida():
    dados = {
        "disciplinas": [
            {
                "nome": "Disciplina A",
                "carga_horaria": {"total": -20},
            }
        ]
    }

    with pytest.raises(ErroPreparacaoEmentas):
        preparar_disciplinas(dados)


def test_ler_json(tmp_path):
    caminho = tmp_path / "ementas.json"

    dados = {
        "resultado": {
            "instituicao": "Instituição Exemplo",
            "disciplinas": [
                {"nome": "Disciplina A"}
            ],
        }
    }

    caminho.write_text(
        json.dumps(dados),
        encoding="utf-8",
    )

    disciplinas = preparar_disciplinas_json(caminho)

    assert len(disciplinas) == 1
    assert disciplinas[0].nome == "Disciplina A"