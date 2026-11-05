
from equivalencia_ementas.academico.application.adaptar_extracao_gemini import (
    criar_lote_extracao_gemini,
)
from equivalencia_ementas.academico.application.registrar_extracao import RegistrarExtracao
from equivalencia_ementas.infraestrutura.ia.modelos_extracao import (
    DisciplinaExtraida,
    DocumentoAcademicoExtraido,
)


class Memoria:
    def __init__(self):
        self.lote = None

    def registrar_atomico(self, lote):
        self.lote = lote
        return list(range(1, len(lote.academico["ementas"]) + 1))


def _kwargs():
    return {
        "nome_arquivo": "ementas.pdf",
        "uri_armazenamento": "/tmp/ementas.pdf",
        "hash_sha256": "a" * 64,
        "tamanho_bytes": 100,
        "paginas": 3,
        "versao_extrator": "gemini-blocos-v12",
    }


def test_converte_multiplas_disciplinas_para_contrato_existente():
    documento = DocumentoAcademicoExtraido(disciplinas=[
        DisciplinaExtraida(nome="Banco de Dados", ementa="SQL"),
        DisciplinaExtraida(nome="Álgebra"),
    ])
    lote = criar_lote_extracao_gemini(documento=documento, **_kwargs())
    memoria = Memoria()
    ids = RegistrarExtracao(memoria).executar(lote)

    assert ids == [1, 2]
    assert lote.academico["ementas"][1]["dados"]["ementa"] is None
    assert lote.academico["ementas"][0]["numero"] == 1
    assert lote.academico["ementas"][1]["numero"] == 2


def test_sem_disciplinas_sinaliza_ausencia_sem_gravar():
    assert criar_lote_extracao_gemini(
        documento=DocumentoAcademicoExtraido(), **_kwargs()
    ) is None

