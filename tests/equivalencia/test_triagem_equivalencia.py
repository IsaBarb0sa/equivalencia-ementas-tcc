from equivalencia_ementas.equivalencia.application.comparar_disciplina_com_matriz import (
    ComparacaoDisciplinaMatriz,
)
from equivalencia_ementas.equivalencia.application.consolidar_evidencias import (
    consolidar_evidencias,
)
from equivalencia_ementas.equivalencia.application.triagem_equivalencia import (
    IndicacaoEquivalencia,
    sugerir_equivalencia,
)
from equivalencia_ementas.equivalencia.domain.entities import (
    CargaHorariaEquivalencia,
    CorrespondenciaTrecho,
    DisciplinaParaEquivalencia,
    ResultadoComparacaoTrechos,
    TrechoAcademico,
)


def disciplina(nome, horas=None, unidade="HORA"):
    return DisciplinaParaEquivalencia(
        nome=nome,
        carga_horaria=CargaHorariaEquivalencia(total=horas, unidade=unidade),
    )


def comparacao(destino, pontuacoes):
    correspondencias = []
    for indice, similaridade in enumerate(pontuacoes):
        correspondencias.append(CorrespondenciaTrecho(
            trecho_destino=TrechoAcademico("ementa", indice, f"destino {indice}", 2),
            trecho_origem=TrechoAcademico("ementa", indice, f"origem {indice}", 2),
            similaridade=similaridade,
        ))
    resultado = ResultadoComparacaoTrechos("falso", tuple(correspondencias), len(pontuacoes), len(pontuacoes))
    return ComparacaoDisciplinaMatriz(0, destino, "comparado", resultado, consolidar_evidencias(resultado))


def test_sugere_apto_com_cobertura_e_carga_comprovadas():
    origem = disciplina("Banco de Dados I", 80)
    resultado = sugerir_equivalencia(origem, comparacao(disciplina("Banco de Dados", 80), [.9, .95]))
    assert resultado.indicacao == IndicacaoEquivalencia.APTO_A_DISPENSA
    assert resultado.decisao_coordenador is None


def test_nao_apto_carga_inferior_com_mesma_unidade():
    resultado = sugerir_equivalencia(disciplina("A", 40), comparacao(disciplina("B", 80), [.9]))
    assert resultado.indicacao == IndicacaoEquivalencia.NAO_APTO


def test_nao_apto_baixa_cobertura():
    resultado = sugerir_equivalencia(disciplina("A", 80), comparacao(disciplina("B", 80), [.1, .2, .9, .2]))
    assert resultado.indicacao == IndicacaoEquivalencia.NAO_APTO


def test_talvez_apto_quando_carga_desconhecida():
    resultado = sugerir_equivalencia(disciplina("A"), comparacao(disciplina("B", 80), [.95]))
    assert resultado.indicacao == IndicacaoEquivalencia.TALVEZ_APTO


def test_talvez_apto_unidades_diferentes():
    resultado = sugerir_equivalencia(
        disciplina("A", 80, "HORA_AULA"),
        comparacao(disciplina("B", 80, "HORA"), [.99]),
    )
    assert resultado.carga_horaria_compativel is None
    assert resultado.indicacao == IndicacaoEquivalencia.TALVEZ_APTO


def test_sem_conteudo_nao_se_torna_nao_apto():
    origem = disciplina("A")
    resultado = sugerir_equivalencia(origem, ComparacaoDisciplinaMatriz(0, disciplina("B"), "origem_sem_conteudo", None))
    assert resultado.indicacao == IndicacaoEquivalencia.TALVEZ_APTO
    assert resultado.cobertura_destino is None
