"""Regressão dos títulos de bibliografia e dos limites da seção."""
import pytest
from ementas_extracao.extratores.generico import analisar


@pytest.mark.parametrize('titulo', ['BIBLIOGRAFIA', 'BIBLIOGRAFIAS'])
@pytest.mark.parametrize('margem_repetida', [False, True])
def test_bibliografia_separa_tipos_e_respeita_fim_da_secao(titulo, margem_repetida):
    basica = 'AUTOR A. Fundamentos da disciplina. Editora A, 2020.'
    complementar = 'AUTOR B. Estudos complementares. Editora B, 2021.'
    textos = [
        'DISCIPLINA: Disciplina de teste', 'EMENTA',
        'Estudo dos fundamentos e aplicações dos conceitos da disciplina.',
        'OBJETIVOS', 'Compreender os fundamentos e aplicar os conceitos estudados.',
        titulo, 'BÁSICA', basica, 'COMPLEMENTAR', complementar,
        'METODOLOGIA', 'Aulas expositivas e atividades em grupo.',
    ]
    linhas = [
        {'texto': texto, 'pagina': 1, 'bbox': [50, 50 + i*20, 550, 65 + i*20],
         'altura_pagina': 842, 'indice': i,
         'margem_repetida': margem_repetida and texto in ('BÁSICA', 'COMPLEMENTAR')}
        for i, texto in enumerate(textos)
    ]
    resultado = analisar(linhas, [{'pagina': 1, 'caracteres': sum(map(len, textos))}])
    assert len(resultado['ementas']) == 1
    assert resultado['ementas'][0]['dados']['bibliografia'] == {
        'basica': basica, 'complementar': complementar, 'nao_classificada': None,
    }
