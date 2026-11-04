from equivalencia_ementas.equivalencia.application.comparar_trechos import (
    CompararTrechos,
)
from equivalencia_ementas.equivalencia.domain.entities import (
    TrechoAcademico,
)


class GeradorFalso:
    nome_modelo = "modelo-falso"

    def gerar(self, textos):
        vetores = {
            "Destino A": [1.0, 0.0],
            "Destino B": [0.0, 1.0],
            "Origem A": [0.9, 0.1],
            "Origem B": [0.1, 0.9],
        }

        return [vetores[texto] for texto in textos]


def criar_trecho(texto):
    return TrechoAcademico(
        secao="conteudo_programatico",
        indice=0,
        texto=texto,
        quantidade_tokens=2,
    )


def test_identificar_melhores_correspondencias():
    comparador = CompararTrechos(GeradorFalso())

    destino = [
        criar_trecho("Destino A"),
        criar_trecho("Destino B"),
    ]

    origem = [
        criar_trecho("Origem A"),
        criar_trecho("Origem B"),
    ]

    resultado = comparador.executar(
        trechos_origem=origem,
        trechos_destino=destino,
    )

    assert len(resultado.correspondencias) == 2

    assert (
        resultado.correspondencias[0].trecho_origem.texto
        == "Origem A"
    )

    assert (
        resultado.correspondencias[1].trecho_origem.texto
        == "Origem B"
    )


def test_preservar_identificacao_do_modelo():
    comparador = CompararTrechos(GeradorFalso())

    resultado = comparador.executar(
        trechos_origem=[criar_trecho("Origem A")],
        trechos_destino=[criar_trecho("Destino A")],
    )

    assert resultado.modelo == "modelo-falso"


def test_sem_trechos_de_origem():
    comparador = CompararTrechos(GeradorFalso())

    resultado = comparador.executar(
        trechos_origem=[],
        trechos_destino=[criar_trecho("Destino A")],
    )

    assert resultado.correspondencias == ()
    assert resultado.quantidade_trechos_destino == 1
    assert resultado.quantidade_trechos_origem == 0


def test_sem_trechos_de_destino():
    comparador = CompararTrechos(GeradorFalso())

    resultado = comparador.executar(
        trechos_origem=[criar_trecho("Origem A")],
        trechos_destino=[],
    )

    assert resultado.correspondencias == ()


def test_preservar_pontuacao():
    comparador = CompararTrechos(GeradorFalso())

    resultado = comparador.executar(
        trechos_origem=[criar_trecho("Origem A")],
        trechos_destino=[criar_trecho("Destino A")],
    )

    assert 0 <= resultado.correspondencias[0].similaridade <= 1