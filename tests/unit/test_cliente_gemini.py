import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from equivalencia_ementas.infraestrutura.ia.cliente_gemini import ExtratorGemini


@pytest.fixture
def extrator():
    cliente = ExtratorGemini.__new__(ExtratorGemini)
    cliente._modelo = "modelo-teste"
    cliente._cliente = Mock()
    cliente._cliente.files.upload.return_value = SimpleNamespace(
        uri="mock://documento", mime_type="application/pdf"
    )
    return cliente


def test_requisicao_exige_disciplinas_e_preserva_registro_parcial(extrator, tmp_path):
    pdf = tmp_path / "documento.pdf"
    pdf.touch()
    extrator._cliente.interactions.create.return_value = SimpleNamespace(
        output_text=json.dumps({
            "instituicao": None,
            "curso": None,
            "disciplinas": [{"nome": "Disciplina parcial"}],
            "observacoes_documento": [],
        })
    )

    resultado = extrator.extrair(pdf)

    esquema = extrator._cliente.interactions.create.call_args.kwargs[
        "response_format"
    ]["schema"]
    assert "disciplinas" in esquema["required"]
    assert esquema["properties"]["disciplinas"]["type"] == "array"
    assert resultado.disciplinas[0].nome == "Disciplina parcial"
    assert resultado.disciplinas[0].carga_horaria.total is None
    assert resultado.disciplinas[0].ementa is None


def test_resposta_sem_disciplinas_nao_vira_lista_vazia(extrator, tmp_path):
    pdf = tmp_path / "documento.pdf"
    pdf.touch()
    extrator._cliente.interactions.create.return_value = SimpleNamespace(
        output_text='{"instituicao": "Instituição"}'
    )

    with pytest.raises(ValueError, match="campo disciplinas ausente"):
        extrator.extrair(pdf)


def test_lista_explicitamente_vazia_emite_aviso(extrator, tmp_path, caplog):
    pdf = tmp_path / "documento.pdf"
    pdf.touch()
    extrator._cliente.interactions.create.return_value = SimpleNamespace(
        output_text='{"disciplinas": [], "observacoes_documento": ["Só capa"]}'
    )

    assert extrator.extrair(pdf).disciplinas == []
    assert "zero disciplinas" in caplog.text
