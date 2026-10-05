"""Verificações pontuais, NÃO uma avaliação de acurácia de todos os campos.

Ativar com EMENTAS_TESTE apontando para os PDFs fornecidos; não distribuir dados pessoais.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from pypdf import PdfReader, PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from extrair_ementas import processar
from ementas_extracao.ocr import ConfigOCR


@unittest.skipUnless(os.environ.get('EMENTAS_TESTE'), 'Defina EMENTAS_TESTE para testar os originais.')
class AmostrasReaisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pasta = Path(os.environ['EMENTAS_TESTE'])
        cls.cache = {}

    def ler(self, chave):
        if chave not in self.cache:
            candidatos = sorted(self.pasta.glob('*' + chave + '*.pdf'))
            self.assertTrue(candidatos, chave)
            self.cache[chave] = processar(candidatos[0], ConfigOCR(modo='nunca'))
        return self.cache[chave]

    def test_unir_52_identidades_separadas(self):
        d, _ = self.ler('2370-25')
        self.assertEqual(len(d['ementas']), 52)
        self.assertEqual([r['dados']['disciplina'] for r in d['ementas'][:3]],
            ['METODOLOGIA DO TRABALHO CIENTÍFICO', 'SOCIOLOGIA', 'ANTROPOLOGIA CULTURAL'])
        self.assertEqual(d['ementas'][0]['dados']['carga_horaria']['teorica'], 40)
        self.assertEqual(d['ementas'][0]['dados']['carga_horaria']['pratica'], 20)
        self.assertEqual(d['ementas'][1]['dados']['carga_horaria']['pratica'], 0)
        self.assertEqual(d['ementas'][0]['paginas_com_evidencias'], [1])
        self.assertNotIn('assinado eletronicamente', str(d['ementas'][0]['dados']).lower())

    def test_uniube_nao_cria_disciplina_a_partir_de_prosa(self):
        d, _ = self.ler('2379-32')
        self.assertEqual(len(d['ementas']), 1)
        r = d['ementas'][0]['dados']
        self.assertEqual(r['carga_horaria']['total'], 72)
        self.assertEqual(r['carga_horaria']['unidade'], 'hora_aula')
        self.assertIn('disciplina diferencia', r['ementa'])
        self.assertIsNone(r['carga_horaria']['pratica'])

    def test_ppc_duas_disciplinas_iniciam_na_mesma_pagina(self):
        d, a = self.ler('2383-5')
        rs = {r['dados']['disciplina']: r for r in a['ementas']}
        for nome in ('PROGRAMAÇÃO DE COMPUTADOR', 'QUÍMICA GERAL'):
            self.assertEqual(rs[nome]['inicio']['pagina'], 39)
        self.assertNotIn('QUÍMICA GERAL', rs['PROGRAMAÇÃO DE COMPUTADOR']['dados']['ementa'])

    def test_numero_da_turma_nao_vira_carga_horaria(self):
        d, _ = self.ler('2367-10')
        self.assertEqual(d['ementas'][0]['dados']['carga_horaria']['total'], 20)
        self.assertEqual(d['ementas'][0]['dados']['curso'], 'ENGENHARIA DE SOFTWARE')

    def test_documentos_administrativos_reais_nao_geram_ementas(self):
        p = next(self.pasta.glob('*2361-4*.pdf'))
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / 'administrativo.pdf'
            writer = PdfWriter(); reader = PdfReader(p)
            for i in range(7):
                writer.add_page(reader.pages[i])
            writer.write(destino)
            d, _ = processar(destino, ConfigOCR(modo='nunca'))
        self.assertFalse(d['ementas'])
        self.assertFalse(d['gravacao_no_banco_autorizada'])

    def test_perfil_aprendizagem_preserva_legal(self):
        d, a = self.ler('Odontologia Legal')
        self.assertEqual(len(d['ementas']), 1)
        r = d['ementas'][0]['dados']
        self.assertEqual(r['disciplina'], 'Odontologia Legal')
        self.assertIn('regulamentação', r['ementa'])
        self.assertIsNone(r['objetivos']['geral'])
        self.assertNotIn('generalista', str(r['objetivos']))

    def test_perfil_aprendizagem_preserva_matematica(self):
        d, _ = self.ler('NIVELAMENTO')
        r = d['ementas'][0]['dados']
        self.assertEqual(r['carga_horaria']['total'], 20)
        self.assertIn('TRINÔMIO', r['conteudo_programatico'])


@unittest.skipUnless(os.environ.get('EMENTAS_TESTE') and os.environ.get('TESTAR_OCR') == '1',
                     'OCR real exige TESTAR_OCR=1 e EMENTAS_TESTE; opcional TESSDATA_TESTE.')
class OCRRealTest(unittest.TestCase):
    def test_ementa_real_escaneada(self):
        pasta = Path(os.environ['EMENTAS_TESTE'])
        origem = next(pasta.glob('*2379-5*.pdf'))
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'epidemiologia.pdf'
            writer = PdfWriter(); reader = PdfReader(origem)
            for i in range(90, 94):
                writer.add_page(reader.pages[i])
            writer.write(p)
            d, a = processar(p, ConfigOCR(tessdata=os.environ.get('TESSDATA_TESTE'),
                                          executavel=os.environ.get('TESSERACT_TESTE')))
        self.assertEqual(len(d['ementas']), 1)
        self.assertIn('EPIDEMIOLOGIA', d['ementas'][0]['dados']['disciplina'].upper())
        self.assertIn('epidemiologia', d['ementas'][0]['dados']['ementa'].lower())
        self.assertEqual([p['metodo'] for p in a['processamento_paginas']], ['ocr'] * 4)


if __name__ == '__main__':
    unittest.main()
