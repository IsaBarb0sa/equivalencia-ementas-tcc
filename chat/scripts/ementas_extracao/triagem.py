"""Classificação existente; não implementa ainda a separação de anexos mistos."""
from ementas_extracao.comum.documento import normalizar
from ementas_extracao.comum.segmentacao import cabecalho

def classificar(linhas, paginas, registros, inicios, administrativo):
    sinais = []
    for l in linhas:
        if administrativo.match(l['texto']):
            sinais.append({'pagina': l['pagina'], 'tipo': normalizar(l['texto']).split(':')[0][:60]})
    sem_texto = [p['pagina'] for p in paginas if p['caracteres'] < 30]
    if registros:
        classe = 'contem_ementas'
        motivo = 'Identidade, conteúdo acadêmico e evidências auxiliares encontrados nos segmentos.'
    elif all(p['caracteres'] < 30 for p in paginas):
        classe, motivo = 'ilegivel', 'Texto insuficiente; não é possível concluir qual é o tipo documental.'
    elif sinais and not inicios and not any(cabecalho(l['texto']) for l in linhas):
        classe, motivo = 'nao_identificado_como_ementa', 'Sinais de documento administrativo, sem estrutura de ementa identificada.'
    else:
        classe, motivo = 'revisao_necessaria', 'Evidências insuficientes ou estrutura desconhecida; não equivale a documento inválido.'
    return classe, motivo, sinais, sem_texto
