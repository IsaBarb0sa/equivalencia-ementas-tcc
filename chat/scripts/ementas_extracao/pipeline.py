"""Fluxo compartilhado: PDF, OCR, extração, enriquecimento e auditoria."""
from dataclasses import asdict
from pathlib import Path
import tempfile
from .comum.documento import Limites, inspecionar, ler_linhas
from .comum.ocr import ConfigOCR, preparar
from .comum.tabelas import enriquecer
from .comum.cobertura import atualizar_cobertura
from .extratores.unipac.instituicao import identificar
from .roteamento import selecionar
from .comum.registros import aproveitar_disciplinas


def processar(origem: Path, config: ConfigOCR, limites: Limites = Limites(), instituicao: str = "generico"):
    extrair, roteamento = selecionar(instituicao)
    documento = inspecionar(origem, limites)
    with tempfile.TemporaryDirectory(prefix='ementas_v4_') as temporario:
        if config.modo == 'nunca':
            entrada = origem
            processamento = [{'pagina': i, 'metodo': 'digital', 'motivo': 'OCR desativado pelo operador'}
                             for i in range(1, documento['total_paginas'] + 1)]
        else:
            entrada = Path(temporario) / 'intermediario.pdf'
            processamento = preparar(origem, entrada, config)
        linhas, paginas = ler_linhas(entrada)
        auditoria = extrair(entrada, linhas, paginas)
        auditoria = enriquecer(entrada, linhas, auditoria)
        auditoria = identificar(origem, auditoria, config)
        auditoria = aproveitar_disciplinas(auditoria)
        auditoria = atualizar_cobertura(auditoria, linhas, paginas)
    auditoria.update(documento=documento, versao_extrator='0.6.0-dev3', processamento_paginas=processamento)
    configuracao = asdict(config)
    configuracao['paginas_forcadas'] = sorted(config.paginas_forcadas)
    auditoria['configuracao'] = configuracao
    auditoria['limites'] = asdict(limites)
    # Linhas originais completas são locais e opcionais de consultar no arquivo de
    # auditoria. Não enviar automaticamente a serviços externos.
    auditoria['linhas'] = linhas
    auditoria['roteamento'] = roteamento
    resultado = {k: auditoria[k] for k in ('documento', 'versao_extrator', 'classificacao', 'status', 'gravacao_no_banco_autorizada')}
    resultado['ementas'] = [{k: r[k] for k in ('numero', 'status', 'dados', 'paginas_com_evidencias', 'paginas_com_campos_extraidos', 'avisos')}
                            for r in auditoria['ementas']]
    resultado['quantidade_candidatos_inconclusivos'] = len(auditoria['candidatos_inconclusivos'])
    return resultado, auditoria