from pathlib import Path
import sys


RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))

from ementas_extracao.generico import analisar
from ementas_extracao.segmentacao import cabecalho


def test_palavra_conteudo_nao_abre_secao():
    assert cabecalho("conteúdo.") is None

    assert cabecalho("CONTEÚDO PROGRAMÁTICO") == (
        "conteudo_programatico",
        "",
    )


def test_metodologia_repetida_encerra_objetivos():
    textos = [
        "Disciplina: Biologia Celular",
        "Carga Horária: 40",
        "EMENTA",
        "Organização das células e processos de divisão celular.",
        "OBJETIVOS ESPECÍFICOS",
        "Identificar estruturas celulares e compreender suas funções.",
        "METODOLOGIA",
        "Material didático obrigatório para aprofundamento do",
        "conteúdo.",
        "Videoaulas e atividades no ambiente virtual.",
        "CONTEÚDO PROGRAMÁTICO",
        "Membrana plasmática, organelas, mitose e meiose.",
        "SISTEMA DE AVALIAÇÃO",
        "Prova presencial e atividades avaliativas.",
    ]

    linhas = [
        {
            "texto": texto,
            "pagina": 1,
            "bbox": [40, 40 + i * 15, 500, 50 + i * 15],
            "altura_pagina": 842,
            "indice": i,
            "margem_repetida": texto == "METODOLOGIA",
        }
        for i, texto in enumerate(textos)
    ]

    resultado = analisar(
        linhas,
        [{
            "pagina": 1,
            "caracteres": sum(len(texto) for texto in textos),
        }],
    )

    assert len(resultado["ementas"]) == 1
    dados = resultado["ementas"][0]["dados"]

    assert dados["objetivos"]["especificos"] == (
        "Identificar estruturas celulares e compreender suas funções."
    )

    assert dados["conteudo_programatico"] == (
        "Membrana plasmática, organelas, mitose e meiose."
    )