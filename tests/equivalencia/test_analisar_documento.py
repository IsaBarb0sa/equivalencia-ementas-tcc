from equivalencia_ementas.equivalencia.application.analisar_documento import AnalisarDocumento
from equivalencia_ementas.equivalencia.application.comparar_disciplina_com_matriz import (
    ComparacaoDisciplinaMatriz,
)
from equivalencia_ementas.equivalencia.domain.entities import DisciplinaParaEquivalencia


class ComparadorFalso:
    def executar(self, disciplina_origem, disciplinas_matriz, quantidade_melhores=3):
        return tuple(
            ComparacaoDisciplinaMatriz(indice, destino, "destino_sem_conteudo", None)
            for indice, destino in enumerate(disciplinas_matriz)
        )


def test_compara_todas_as_disciplinas_sem_selecao_manual():
    origens = [DisciplinaParaEquivalencia(nome="Origem A"), DisciplinaParaEquivalencia(nome="Origem B")]
    destinos = [DisciplinaParaEquivalencia(nome="Destino 1"), DisciplinaParaEquivalencia(nome="Destino 2")]
    resultado = AnalisarDocumento(ComparadorFalso()).executar(origens, destinos)
    assert [item.disciplina_origem for item in resultado] == ["Origem A", "Origem B"]
    assert all(len(item.sugestoes) == 2 for item in resultado)
    assert all(item.decisao_coordenador is None for grupo in resultado for item in grupo.sugestoes)
