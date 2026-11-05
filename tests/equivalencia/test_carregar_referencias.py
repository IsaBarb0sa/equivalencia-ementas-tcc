import json

import pytest

from equivalencia_ementas.equivalencia.application.carregar_referencias import (
    carregar_referencias_validadas,
)


def criar_referencia(
    identificador,
    classificacao,
):
    return {
        "id": identificador,
        "area": "Área de teste",
        "origem": {
            "arquivo": "origem.json",
            "disciplina": "Disciplina A",
            "secao": "ementa",
            "texto": "Conteúdo A",
        },
        "destino": {
            "arquivo": "destino.json",
            "disciplina": "Disciplina B",
            "secao": "ementa",
            "texto": "Conteúdo B",
        },
        "classificacao_proposta": "correspondente",
        "classificacao_validada": classificacao,
        "justificativa": "Classificação de teste.",
    }


def salvar_referencias(caminho, referencias):
    caminho.write_text(
        json.dumps(
            {"referencias": referencias},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_carregar_referencia_validada(tmp_path):
    arquivo = tmp_path / "referencias.json"

    salvar_referencias(
        arquivo,
        [
            criar_referencia(
                "REF001",
                "correspondente",
            )
        ],
    )

    resultado = carregar_referencias_validadas(
        arquivo
    )

    assert len(resultado) == 1
    assert resultado[0].identificador == "REF001"
    assert resultado[0].classificacao == "correspondente"


def test_ignorar_referencias_pendentes(tmp_path):
    arquivo = tmp_path / "referencias.json"

    salvar_referencias(
        arquivo,
        [
            criar_referencia(
                "REF001",
                "correspondente",
            ),
            criar_referencia(
                "REF002",
                None,
            ),
        ],
    )

    resultado = carregar_referencias_validadas(
        arquivo
    )

    assert len(resultado) == 1
    assert resultado[0].identificador == "REF001"


def test_rejeitar_classificacao_invalida(tmp_path):
    arquivo = tmp_path / "referencias.json"

    salvar_referencias(
        arquivo,
        [
            criar_referencia(
                "REF001",
                "aprovado_automaticamente",
            )
        ],
    )

    with pytest.raises(
        ValueError,
        match="Classificação inválida",
    ):
        carregar_referencias_validadas(arquivo)


def test_rejeitar_identificadores_duplicados(tmp_path):
    arquivo = tmp_path / "referencias.json"

    salvar_referencias(
        arquivo,
        [
            criar_referencia(
                "REF001",
                "correspondente",
            ),
            criar_referencia(
                "REF001",
                "nao_correspondente",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="Identificador duplicado",
    ):
        carregar_referencias_validadas(arquivo)


def test_rejeitar_conjunto_sem_validacoes(tmp_path):
    arquivo = tmp_path / "referencias.json"

    salvar_referencias(
        arquivo,
        [
            criar_referencia(
                "REF001",
                None,
            )
        ],
    )

    with pytest.raises(
        ValueError,
        match="Nenhuma referência",
    ):
        carregar_referencias_validadas(arquivo)


def test_preservar_dados_dos_trechos(tmp_path):
    arquivo = tmp_path / "referencias.json"

    salvar_referencias(
        arquivo,
        [
            criar_referencia(
                "REF001",
                "parcialmente_relacionado",
            )
        ],
    )

    resultado = carregar_referencias_validadas(
        arquivo
    )

    referencia = resultado[0]

    assert referencia.origem.disciplina == "Disciplina A"
    assert referencia.destino.disciplina == "Disciplina B"
    assert referencia.origem.texto == "Conteúdo A"
    assert referencia.destino.texto == "Conteúdo B"