"""Protege comportamentos conferidos da extração institucional.

Escopo: leitura estrutural do PDF e normalização.
Não testa OCR, identificação da instituição nem gravação no banco.
"""

from pathlib import Path
import sys

import pytest


RAIZ = Path(__file__).resolve().parents[4]

# O extrator ainda está dentro de scripts, fora do pacote em src.
# Permite importar seus módulos ao executar pytest pela raiz do projeto.
sys.path.insert(0, str(RAIZ / "scripts"))

from ementas_extracao.extratores.unipac.estrutural import extrair
from ementas_extracao.extratores.unipac.normalizacao import projetar


PASTA_PDFS = RAIZ / "tests" / "fixtures" / "ementas" / "unipac"


@pytest.fixture(scope="module")
def extrair_referencia():
    cache = {}

    def executar(nome_arquivo):
        caminho = PASTA_PDFS / nome_arquivo

        if not caminho.is_file():
            pytest.fail(
                f"PDF de referência não encontrado: {caminho}. "
                "Coloque uma cópia do documento conferido nessa pasta."
            )

        if nome_arquivo not in cache:
            auditoria = extrair(caminho)
            cache[nome_arquivo] = projetar(auditoria)

        return cache[nome_arquivo]

    return executar


@pytest.mark.parametrize(
    (
        "arquivo",
        "disciplina",
        "total",
        "teorica",
        "pratica",
    ),
    [
        (
            "cirurgia.pdf",
            "Cirurgia e Traumatologia",
            40,
            None,
            None,
        ),
        (
            "semiologia.pdf",
            "Semiologia",
            40,
            40,
            0,
        ),
        (
            "anatomia.pdf",
            "Anatomia Cabeça e Pescoço",
            80,
            40,
            40,
        ),
    ],
)
def test_identidade_e_carga_horaria(
    extrair_referencia,
    arquivo,
    disciplina,
    total,
    teorica,
    pratica,
):
    dados = extrair_referencia(arquivo)

    assert dados["disciplina"] == disciplina

    carga = dados["carga_horaria"]
    assert carga["total"] == total
    assert carga["teorica"] == teorica
    assert carga["pratica"] == pratica

    # Não presumir hora-relógio quando o documento não a esclarece.
    assert carga["unidade"] == "nao_identificada"


def test_cirurgia_preserva_topicos_clinicos(extrair_referencia):
    dados = extrair_referencia("cirurgia.pdf")
    itens = dados["conteudo_programatico"]["itens"]

    esperados = {
        "Avaliação pré-operatória dos pacientes",
        "Exames complementares em odontologia",
        "Alveolite dentária",
        "Parestesia pós-operatória",
        "Autotransplante de dentes",
        "Cirurgias endodônticas",
    }

    assert esperados.issubset(set(itens))

    texto = "\n".join(itens).casefold()
    assert "enviar via portal" not in texto


def test_semiologia_separa_temas_de_avaliacoes(extrair_referencia):
    dados = extrair_referencia("semiologia.pdf")
    itens = dados["conteudo_programatico"]["itens"]

    for inicio in (
        "Exame clínico:",
        "Exames complementares:",
        "Diagnóstico diferenciado:",
    ):
        assert sum(item.startswith(inicio) for item in itens) == 1

    texto = "\n".join(itens).casefold()

    for trecho in (
        "exame especial",
        "100 pontos",
        "semana da odontologia",
    ):
        assert trecho not in texto


def test_anatomia_preserva_topicos(extrair_referencia):
    dados = extrair_referencia("anatomia.pdf")
    itens = dados["conteudo_programatico"]["itens"]

    esperados = {
        "Osteologia Geral da Cabeça e Pescoço",
        "Artrologia Geral e ATM",
        "Bases Anatômicas da Anestesia Local",
        "Disseminação das infecções dentais",
    }

    assert esperados.issubset(set(itens))