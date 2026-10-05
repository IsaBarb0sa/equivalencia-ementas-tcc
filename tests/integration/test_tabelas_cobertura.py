"""Regressões dos erros reportados pela usuária: tabelas, cobertura e fim do PPC."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from extrair_ementas import processar
from ementas_extracao.ocr import ConfigOCR, ambiente_tessdata
from ementas_extracao.cobertura import atualizar_cobertura
from ementas_extracao.tabelas import numero


class CoberturaTest(unittest.TestCase):
    def test_contexto_academico_sem_campo_nao_e_pagina_sem_ementa(self):
        linhas = [{'texto': 'PLANOS DE ENSINO – NUTRIÇÃO (PRESENCIAL)', 'pagina': 4}]
        a = {'ementas': [], 'candidatos_inconclusivos': [], 'classificacao': {'paginas_sem_evidencias_de_ementa': [4]}}
        atualizar_cobertura(a, linhas, [{'pagina': 4}])
        c = a['classificacao']
        self.assertNotIn('paginas_sem_evidencias_de_ementa', c)
        self.assertEqual(c['paginas_sem_campos_extraidos'], [4])
        self.assertEqual(c['paginas_com_sinais_academicos'], [4])
        self.assertEqual(c['paginas_sem_sinais_academicos_detectados'], [])

    def test_pagina_de_tabela_conta_como_fonte(self):
        r = {'numero': 1, 'evidencias': {'tabela': [{'pagina': 31}]}, 'rotulos': {}}
        a = {'ementas': [r], 'candidatos_inconclusivos': [], 'classificacao': {}}
        atualizar_cobertura(a, [], [{'pagina': 31}, {'pagina': 38}])
        self.assertEqual(r['paginas_com_campos_extraidos'], [31])

    def test_tema_consolidado_conta_como_fonte(self):
        r = {'numero': 1, 'evidencias': {}, 'rotulos': {}, 'auditoria_perfil': {
            'consolidacao_conteudo': [{'decisao': 'candidato_extraido', 'indices_itens': [0], 'fontes': [{'pagina': 15}]}]}}
        a = {'ementas': [r], 'candidatos_inconclusivos': [], 'classificacao': {}}
        atualizar_cobertura(a, [], [{'pagina': 15}])
        self.assertEqual(r['paginas_com_campos_extraidos'], [15])

    def test_numero_vazio_e_zero_sao_diferentes(self):
        self.assertIsNone(numero(''))
        self.assertEqual(numero('0h'), 0)
        self.assertEqual(numero('20h'), 20)
        self.assertIsNone(numero('20 40'))

    def test_tessdata_com_espacos_sem_aspas_literais_e_restaura_ambiente(self):
        with tempfile.TemporaryDirectory(prefix='tessdata com espacos ') as pasta:
            with patch.dict(os.environ, {'TESSDATA_PREFIX': 'anterior'}):
                with ambiente_tessdata(ConfigOCR(tessdata=pasta)):
                    self.assertEqual(os.environ['TESSDATA_PREFIX'], str(Path(pasta).resolve()))
                    self.assertNotIn('"', os.environ['TESSDATA_PREFIX'])
                self.assertEqual(os.environ['TESSDATA_PREFIX'], 'anterior')


@unittest.skipUnless(os.environ.get('EMENTAS_TESTE'), 'Defina EMENTAS_TESTE para validar os PDFs originais.')
class TabelasReaisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache = {}

    def ler(self, trecho):
        if trecho not in self.cache:
            pasta = Path(os.environ['EMENTAS_TESTE'])
            self.cache[trecho] = processar(next(pasta.glob('*' + trecho + '*.pdf')), ConfigOCR(modo='nunca'))
        return self.cache[trecho]

    def test_matriz_semanal_nao_se_confunde_com_total(self):
        d, a = self.ler('2383-5')
        registros = {r['dados']['disciplina']: r for r in d['ementas']}
        r = registros['INTRODUÇÃO À ENGENHARIA CIVIL']
        c = r['dados']['carga_horaria']
        self.assertEqual((c['total_hora_aula'], c['total_hora_relogio']), (54, 45))
        self.assertEqual(c['total'], 45)
        self.assertEqual(c['unidade'], 'hora_relogio')
        self.assertEqual(c['semanal']['teorica'], 3)
        self.assertIsNone(c['semanal']['pratica'])
        self.assertIsNone(c['teorica'])
        self.assertIn(31, r['paginas_com_campos_extraidos'])
        q = registros['QUÍMICA GERAL']['dados']['carga_horaria']
        self.assertEqual((q['semanal']['teorica'], q['semanal']['pratica']), (4, 2))
        self.assertEqual(q['total'], 90)

    def test_tabelas_fragmentadas_ate_decimo_periodo(self):
        _, a = self.ler('2383-5')
        self.assertEqual(sorted({t['pagina'] for t in a['tabelas_academicas']}), [31,32,33,34,35,36,37])

    def test_nao_inventa_conteudo_programatico(self):
        d, _ = self.ler('2383-5')
        self.assertTrue(all(r['dados']['conteudo_programatico'] is None for r in d['ementas']))

    def test_titulos_multilinha_no_ppc(self):
        d, _ = self.ler('2383-5')
        nomes = {r['dados']['disciplina'] for r in d['ementas']}
        self.assertIn('DESENHO AUXILIADO POR COMPUTADOR PARA ENGENHARIA E ARQUITETURA', nomes)
        self.assertIn('TRATAMENTO E DESTINAÇÃO FINAL DE RESÍDUOS SÓLIDOS DOMICILIARES', nomes)
        self.assertNotIn('ARQUITETURA', nomes)

    def test_fim_ementario_nao_captura_anexos(self):
        _, a = self.ler('2383-5')
        r = next(r for r in a['ementas'] + a['candidatos_inconclusivos'] if r['dados']['disciplina'] == 'TÓPICOS ESPECIAIS DE ENGENHARIA')
        self.assertLess(len(r['dados']['ementa']), 300)
        self.assertNotIn('Metodologia', r['dados']['ementa'])
        self.assertEqual(r['fim_do_intervalo']['pagina'], 111)

    def test_nutricao_modalidades_e_nomes_inteiros(self):
        d, _ = self.ler('2383-8')
        self.assertEqual(len(d['ementas']), 14)
        self.assertTrue(all(r['dados']['carga_horaria']['total'] is not None for r in d['ementas']))
        r = d['ementas'][0]['dados']
        self.assertEqual(r['carga_horaria']['modalidades'], {'teorica_presencial':40,'teorica_ead':20,'pratica_presencial':0,'pratica_ead':0,'extensao':0})
        self.assertEqual(r['carga_horaria']['teorica'], 60)
        self.assertEqual(r['carga_horaria']['pratica'], 0)
        nomes = {r['dados']['disciplina'] for r in d['ementas']}
        self.assertIn('DESENVOLVIMENTO PESSOAL E TRABALHABILIDADE', nomes)
        self.assertIn('ATIVIDADES PRÁTICAS INTERDISCIPLINARES DE EXTENSÃO I', nomes)
        self.assertIn('ATIVIDADES PRÁTICAS INTERDISCIPLINARES DE EXTENSÃO II', nomes)

    def test_cobertura_nutricao_metodologia_tem_sinais(self):
        d, _ = self.ler('2383-8')
        c = d['classificacao']
        self.assertNotIn('paginas_sem_evidencias_de_ementa', c)
        self.assertIn(4, c['paginas_com_sinais_academicos'])
        self.assertIn(4, c['paginas_sem_campos_extraidos'])
        self.assertIn(1, c['paginas_com_campos_extraidos'])

    def test_anatomia_preserva_horas_e_inclui_fontes_de_conteudo(self):
        d, _ = self.ler('ANATOMIA CABEÇA')
        r = d['ementas'][0]
        self.assertEqual(r['dados']['carga_horaria']['total'], 80)
        self.assertEqual(r['dados']['carga_horaria']['teorica'], 40)
        self.assertEqual(r['dados']['carga_horaria']['pratica'], 40)
        self.assertGreater(max(r['paginas_com_campos_extraidos']), 4)


if __name__ == '__main__':
    unittest.main()
