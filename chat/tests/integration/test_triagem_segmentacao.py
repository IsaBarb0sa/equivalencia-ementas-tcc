"""Testes autocontidos: critérios e limites, sem depender dos PDFs dos alunos."""
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / 'scripts'))
from ementas_extracao.documento import DocumentoRecusado, Limites, inspecionar
from ementas_extracao.generico import analisar
from ementas_extracao.segmentacao import cabecalho
from pypdf import PdfWriter


def documento(*paginas):
    linhas, resumo = [], []
    for pagina, texto in enumerate(paginas, 1):
        atuais = texto.strip().splitlines()
        for i, t in enumerate(atuais):
            linhas.append({'texto': t.strip(), 'pagina': pagina, 'bbox': [40, 100+i*12, 550, 111+i*12],
                'altura_pagina': 800, 'indice': len(linhas), 'margem_repetida': False})
        resumo.append({'pagina': pagina, 'caracteres': len(texto), 'linhas': len(atuais)})
    return analisar(linhas, resumo)


EMENTA = '''Disciplina: Algoritmos
Carga Horária: 60 horas
EMENTA
Estruturas de controle, variáveis, funções e desenvolvimento de algoritmos.
OBJETIVO GERAL
Desenvolver o raciocínio lógico para resolver problemas computacionais.
BIBLIOGRAFIA BÁSICA
AUTOR. Introdução à programação de computadores. Editora, 2020.'''


class SegmentacaoTest(unittest.TestCase):
    def test_duas_disciplinas_na_mesma_pagina(self):
        d = documento(EMENTA + '\n' + EMENTA.replace('Algoritmos', 'Banco de Dados').replace('Estruturas de controle', 'Modelagem relacional'))
        self.assertEqual(len(d['ementas']), 2)
        self.assertNotIn('Modelagem relacional', d['ementas'][0]['dados']['ementa'])

    def test_secao_continua_na_pagina_seguinte(self):
        a, b = EMENTA.split('OBJETIVO GERAL')
        d = documento(a, 'Continuação sobre recursão e estruturas de dados.\nOBJETIVO GERAL' + b)
        self.assertIn('recursão', d['ementas'][0]['dados']['ementa'])

    def test_historico_nao_vira_ementa(self):
        d = documento('HISTÓRICO ESCOLAR\nDISCIPLINA NOTA CARGA HORÁRIA\nAlgoritmos 9,0 60\nCálculo 8,0 80')
        self.assertFalse(d['ementas'])

    def test_diploma_isolado(self):
        d = documento('DIPLOMA\nCertificamos a conclusão do curso superior de Engenharia e concedemos o título de bacharel.')
        self.assertEqual(d['classificacao']['resultado'], 'nao_identificado_como_ementa')

    def test_misto_aproveita_apenas_ementa(self):
        d = documento('DIPLOMA\nPessoa concluiu o curso em 2024 e recebeu este diploma.', EMENTA)
        self.assertEqual(len(d['ementas']), 1)
        self.assertNotIn('diploma', str(d['ementas'][0]['dados']).lower())
        self.assertIn(1, d['classificacao']['paginas_sem_campos_extraidos'])

    def test_texto_desconhecido_e_inconclusivo(self):
        d = documento('Relatório de uma reunião administrativa com decisões e encaminhamentos para a próxima semana.')
        self.assertEqual(d['classificacao']['resultado'], 'revisao_necessaria')

    def test_nome_e_palavra_ementa_nao_bastam(self):
        d = documento('Disciplina: Algoritmos\nEMENTA\nTexto curto')
        self.assertFalse(d['ementas'])

    def test_ausencia_nao_equivale_a_zero(self):
        r = documento(EMENTA)['ementas'][0]['dados']
        self.assertIsNone(r['carga_horaria']['pratica'])
        self.assertIsNone(r['curso'])

    def test_instituicao_nao_propaga_entre_disciplinas(self):
        d = documento('UNIVERSIDADE EXEMPLO\n' + EMENTA, EMENTA.replace('Algoritmos', 'Física'))
        self.assertEqual(d['ementas'][0]['dados']['instituicao'], 'UNIVERSIDADE EXEMPLO')
        self.assertIsNone(d['ementas'][1]['dados']['instituicao'])

    def test_objetivo_curso_nao_e_objetivo_disciplina(self):
        d = documento(EMENTA + '\nOBJETIVOS DO CURSO\nFormar um profissional com visão generalista.')
        self.assertNotIn('generalista', str(d['ementas'][0]['dados']['objetivos']))

    def test_cronograma_nao_e_conteudo(self):
        d = documento(EMENTA + '\nCRONOGRAMA DE AULAS\nAula 1 apresentação. Aula 2 prova. Aula 3 correção.')
        self.assertNotIn('Aula 1', str(d['ementas'][0]['dados']))

    def test_titulo_antes_da_ementa(self):
        d = documento(EMENTA.replace('Disciplina: Algoritmos\nCarga Horária: 60 horas', 'PROGRAMAÇÃO DE COMPUTADORES'))
        self.assertEqual(d['ementas'][0]['dados']['disciplina'], 'PROGRAMAÇÃO DE COMPUTADORES')

    def test_carga_conflitante_nao_escolhe_valor(self):
        d = documento(EMENTA.replace('Carga Horária: 60 horas', 'Carga Horária: 60 horas\nCarga Horária: 80 horas'))
        self.assertIsNone(d['ementas'][0]['dados']['carga_horaria']['total'])
        self.assertIn('valores_conflitantes:carga_horaria.total', d['ementas'][0]['avisos'])

    def test_bibliografia_nao_classificada(self):
        d = documento(EMENTA.replace('BIBLIOGRAFIA BÁSICA', 'REFERÊNCIAS'))
        self.assertIsNotNone(d['ementas'][0]['dados']['bibliografia']['nao_classificada'])

    def test_ilegivel_nao_e_rejeicao_semantica(self):
        self.assertEqual(documento('')['classificacao']['resultado'], 'ilegivel')

    def test_cabecalho_numerado(self):
        self.assertEqual(cabecalho('2. Ementa: Texto.'), ('ementa', 'Texto.'))

    def test_disciplina_no_corpo_nao_divide(self):
        d = documento(EMENTA.replace('Estruturas de controle,', 'disciplina diferencia os conceitos de controle,'))
        self.assertEqual(len(d['ementas']), 1)
        self.assertEqual(d['ementas'][0]['dados']['disciplina'], 'Algoritmos')

    def test_cabecalho_seguinte_nao_contamina_bibliografia(self):
        d = documento(EMENTA, 'MINISTÉRIO DA EDUCAÇÃO\nUNIVERSIDADE EXEMPLO\n' + EMENTA.replace('Algoritmos', 'Física'))
        self.assertNotIn('MINISTÉRIO', str(d['ementas'][0]['dados']['bibliografia']))
        self.assertEqual(d['ementas'][0]['paginas_com_evidencias'], [1])


class ArquivoTest(unittest.TestCase):
    def test_extensao_pdf_nao_basta(self):
        with tempfile.TemporaryDirectory() as pasta:
            p = Path(pasta) / 'falso.pdf'; p.write_text('Não é um PDF')
            with self.assertRaises(DocumentoRecusado) as erro:
                inspecionar(p, Limites())
            self.assertEqual(erro.exception.codigo, 'arquivo_invalido')

    def test_pdf_com_senha(self):
        with tempfile.TemporaryDirectory() as pasta:
            p = Path(pasta) / 'protegido.pdf'
            writer = PdfWriter(); writer.add_blank_page(595, 842); writer.encrypt('senha')
            writer.write(p)
            with self.assertRaises(DocumentoRecusado) as erro:
                inspecionar(p, Limites())
            self.assertEqual(erro.exception.codigo, 'pdf_protegido')

    def test_limite_paginas(self):
        with tempfile.TemporaryDirectory() as pasta:
            p = Path(pasta) / 'grande.pdf'
            writer = PdfWriter(); writer.add_blank_page(595, 842); writer.add_blank_page(595, 842); writer.write(p)
            with self.assertRaises(DocumentoRecusado) as erro:
                inspecionar(p, Limites(max_paginas=1))
            self.assertEqual(erro.exception.codigo, 'limite_excedido')


if __name__ == '__main__':
    unittest.main()
