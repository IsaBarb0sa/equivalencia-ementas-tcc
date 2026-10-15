"""Testes locais: nenhuma chamada às APIs nem ao banco."""
import tempfile
import unittest
from pathlib import Path

from equivalencia_ementas.infraestrutura.ia.modelos_extracao import (
    CargaHorariaExtraida as Carga, DisciplinaExtraida as Disciplina,
    DocumentoAcademicoExtraido as Documento, ObjetivosExtraidos,
)
from equivalencia_ementas.infraestrutura.ia.processador_documento import (
    ProcessadorDocumentoIA as Processador, VERSAO_CACHE_GEMINI,
)
from equivalencia_ementas.academico.application.normalizar_extracao import normalizar_extracao


class TestExtracaoSimplificada(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.extrator = type('ExtratorFalso', (), {'modelo': 'modelo-teste'})()
        self.proc = Processador(self.extrator, pasta_cache=Path(self.temp.name))

    def test_contrato_tem_apenas_quatro_campos(self):
        self.assertEqual(set(Carga.model_json_schema()['properties']),
                         {'total', 'teorica', 'pratica', 'unidade'})

    def test_campos_legados_nao_viram_totais(self):
        c = Carga.model_validate({'total_semanal': 4, 'teorica_semanal': 4})
        self.assertEqual(c.model_dump(), dict(total=None, teorica=None, pratica=None, unidade=None))

    def test_ausencias_nao_sao_calculadas(self):
        c = Carga(total=80, teorica=40)
        self.assertIsNone(c.pratica)
        self.assertIsNone(Carga(teorica=40, pratica=40).total)

    def test_zero_explicito_e_preservado(self):
        self.assertEqual(Carga(pratica=0).pratica, 0)

    def test_mescla_mesma_unidade(self):
        c = self.proc._mesclar_carga_horaria(Carga(total=80, unidade='HORA'),
                                           Carga(teorica=40, pratica=40, unidade='HORA'))
        self.assertEqual((c.total, c.teorica, c.pratica), (80, 40, 40))

    def test_nao_mescla_unidades_diferentes(self):
        a, b = Carga(total=80, unidade='HORA_AULA'), Carga(teorica=30, unidade='HORA')
        self.assertTrue(self.proc._cargas_conflitam(a, b))
        self.assertEqual(self.proc._mesclar_carga_horaria(a, b), a)

    def test_nao_atribui_unidade_de_outro_bloco(self):
        a, b = Carga(total=80), Carga(unidade='HORA')
        self.assertTrue(self.proc._cargas_conflitam(a, b))
        self.assertIsNone(self.proc._mesclar_carga_horaria(a, b).unidade)

    def test_conflito_numerico_tem_auditoria(self):
        a = Disciplina(nome='Disciplina', carga_horaria=Carga(total=80))
        b = Disciplina(nome='Disciplina', carga_horaria=Carga(total=60))
        r = self.proc._mesclar_disciplinas(a, b)
        self.assertEqual(r.carga_horaria.total, 80)
        self.assertIn('60', r.observacoes[0])
        self.assertEqual(a.observacoes, [])

    def test_conteudo_continua_entre_blocos(self):
        a = Disciplina(nome='Disciplina', conteudo_programatico='Tema A\nTema B.')
        b = Disciplina(nome='Disciplina', conteudo_programatico='Tema B\nTema C')
        r = self.proc._mesclar_disciplinas(a, b)
        self.assertEqual(r.conteudo_programatico, 'Tema A\nTema B.\nTema C')

    def test_normalizacao_nao_reclassifica_objetivos_ou_nome(self):
        d = Documento(instituicao='Universidade Exemplo - UE', disciplinas=[
            Disciplina(nome='Disciplina', objetivos=ObjetivosExtraidos(nao_classificados='Aprender.'))])
        r = normalizar_extracao(d)
        self.assertEqual(r.instituicao, d.instituicao)
        self.assertIsNone(r.disciplinas[0].objetivos.geral)
        self.assertIsNone(r.disciplinas[0].objetivos.especificos)
        self.assertEqual(r.disciplinas[0].objetivos.nao_classificados, 'Aprender.')

    def test_cache_novo_nao_reutiliza_v9(self):
        self.assertEqual(VERSAO_CACHE_GEMINI, '10')
        p = self.proc._caminho_cache_bloco('abc', 0, 9)
        self.assertIn('__v10__', p.name)

    def test_cache_preserva_novo_contrato(self):
        p = Path(self.temp.name)/'cache.json'
        d = Documento(disciplinas=[Disciplina(nome='Disciplina', carga_horaria=Carga(total=80))])
        self.proc._salvar_cache_bloco(p, Path('teste.pdf'), 'abc', 0, 9, d)
        self.assertEqual(self.proc._carregar_cache_bloco(p), d)


if __name__ == '__main__':
    unittest.main()
