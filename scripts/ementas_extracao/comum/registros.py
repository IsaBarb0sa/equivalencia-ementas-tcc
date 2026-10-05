"""Preserva disciplinas identificadas, mesmo sem texto acadêmico suficiente."""
from math import isfinite


def aproveitar_disciplinas(analise):
    registros = analise['ementas']
    restantes = []
    for registro in analise['candidatos_inconclusivos']:
        dados = registro['dados']
        nome = dados.get('disciplina')
        total = (dados.get('carga_horaria') or {}).get('total')
        evidencias = registro.get('evidencias', {})
        identidade = registro.get('criterios', {}).get('identidade')
        if (identidade and isinstance(nome, str) and nome.strip()
                and type(total) in (int, float) and isfinite(total) and total > 0
                and evidencias.get('disciplina')
                and (evidencias.get('carga_horaria') or evidencias.get('carga_horaria.total'))):
            registro['identificacao'] = 'disciplina_identificada'
            registro['status'] = 'pendente_revisao'
            registro['avisos'] = [a for a in registro['avisos']
                if a != 'identidade_sem_conteudo_academico_suficiente']
            if 'registro_parcial' not in registro['avisos']:
                registro['avisos'].append('registro_parcial')
            registros.append(registro)
        else:
            restantes.append(registro)
    registros.sort(key=lambda r: (r.get('inicio', {}).get('pagina', 0),
                                  r.get('inicio', {}).get('bbox', [0, 0])[1]))
    for numero, registro in enumerate(registros, 1):
        registro['numero'] = numero
    analise['candidatos_inconclusivos'] = restantes
    if registros and not any(r.get('identificacao') == 'ementa_identificada' for r in registros):
        analise['classificacao'].update(resultado='contem_disciplinas',
            motivo='Disciplinas com nome e carga horária identificados; conteúdo parcial preservado.')
    return analise
