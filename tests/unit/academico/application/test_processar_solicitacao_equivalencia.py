
from pathlib import Path

from equivalencia_ementas.academico.application.use_cases.processar_solicitacao_equivalencia import (
    DocumentoDaSolicitacao,
    ProcessarSolicitacaoEquivalencia,
)
from equivalencia_ementas.equivalencia.domain.entities import DisciplinaParaEquivalencia
from equivalencia_ementas.infraestrutura.ia.modelos_extracao import (
    DisciplinaExtraida,
    DocumentoAcademicoExtraido,
)


class ExtratorFalso:
    def __init__(self, resultados):
        self.resultados = iter(resultados)

    def processar(self, caminho_pdf):
        return next(self.resultados)


class RegistradorFalso:
    def __init__(self):
        self.lotes = []

    def executar(self, lote):
        self.lotes.append(lote)
        return [1]


class AnalisadorFalso:
    def __init__(self):
        self.recebidos = None

    def executar(self, origens, matriz):
        self.recebidos = (origens, matriz)
        return ()


def _documento(numero):
    return DocumentoDaSolicitacao(numero, Path(f"{numero}.pdf"), f"{numero}.pdf", f"{numero:064x}", 200, 3)


def test_extrai_todos_os_documentos_e_analisa_todas_as_disciplinas():
    extrator = ExtratorFalso([
        DocumentoAcademicoExtraido(disciplinas=[DisciplinaExtraida(nome="A"), DisciplinaExtraida(nome="B")]),
        DocumentoAcademicoExtraido(disciplinas=[DisciplinaExtraida(nome="C")]),
    ])
    registrador = RegistradorFalso()
    analisador = AnalisadorFalso()
    caso = ProcessarSolicitacaoEquivalencia(extrator, registrador, analisador, "v12")
    matriz = [DisciplinaParaEquivalencia(nome="Destino")]

    resultado = caso.executar(documentos=[_documento(1), _documento(2)], disciplinas_matriz=matriz)

    assert resultado.quantidade_documentos == 2
    assert resultado.quantidade_disciplinas == 3
    assert len(registrador.lotes) == 2
    assert [disc.nome for disc in analisador.recebidos[0]] == ["A", "B", "C"]


def test_documento_sem_disciplinas_eh_identificado():
    extrator = ExtratorFalso([DocumentoAcademicoExtraido()])
    registrador = RegistradorFalso()
    analisador = AnalisadorFalso()
    caso = ProcessarSolicitacaoEquivalencia(extrator, registrador, analisador, "v12")

    resultado = caso.executar(documentos=[_documento(1)], disciplinas_matriz=[])

    assert resultado.quantidade_sem_disciplinas == 1
    assert resultado.quantidade_disciplinas == 0
    assert registrador.lotes == []
    assert analisador.recebidos is None

