from pathlib import Path
import sys

import pdfplumber


RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ / "scripts"))

from ementas_extracao.extratores.uniube.tabelas import presencial_nao_presencial


def test_carga_da_primeira_disciplina():
    caminho = (
        RAIZ / "tests" / "fixtures" / "ementas" / "uniube" / "ementa_15.pdf"
    )

    assert caminho.is_file(), f"PDF não encontrado: {caminho}"

    with pdfplumber.open(caminho) as pdf:
        registros = [
            registro
            for tabela in pdf.pages[0].find_tables()
            for registro in presencial_nao_presencial(tabela, 1)
        ]

    assert len(registros) == 1

    registro = registros[0]
    carga = registro["carga"]

    assert registro["disciplina"].startswith("926075 - ")
    assert registro["avisos"] == []

    assert carga["unidade"] == "hora_aula"
    assert carga["total"] == 96
    assert carga["teorica"] == 72
    assert carga["pratica"] == 24

    modalidades = carga["modalidades"]
    assert modalidades["presencial.teorica"] == 6
    assert modalidades["nao_presencial.teorica"] == 66
    assert modalidades["nao_presencial.pratica"] == 24

def test_carga_mista_nao_inventa_divisao():
    caminho = (
        RAIZ / "tests" / "fixtures" / "ementas" / "uniube" / "ementa_15.pdf"
    )

    assert caminho.is_file(), f"PDF não encontrado: {caminho}"

    with pdfplumber.open(caminho) as pdf:
        for numero_pagina in (136, 246):
            registros = [
                registro
                for tabela in pdf.pages[numero_pagina - 1].find_tables()
                for registro in presencial_nao_presencial(
                    tabela,
                    numero_pagina,
                )
            ]

            assert len(registros) == 1, (
                f"Tabela não reconhecida na página {numero_pagina}"
            )

            registro = registros[0]
            carga = registro["carga"]

            assert carga["total"] == 48
            assert carga["unidade"] == "hora_aula"
            assert carga["teorico_pratica"] == 48

            assert carga["teorica"] is None
            assert carga["pratica"] is None

            assert (
                carga["modalidades"]["nao_presencial.teoricapratica"]
                == 48
            )

            assert registro["avisos"] == [
                "carga_teorico_pratica_sem_divisao_declarada"
            ]