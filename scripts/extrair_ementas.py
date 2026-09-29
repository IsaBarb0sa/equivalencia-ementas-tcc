"""Uma entrada para PDFs, triagem, segmentação e extração. Não grava no banco."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import tempfile

from ementas_extracao.documento import DocumentoRecusado, Limites, inspecionar, ler_linhas
from ementas_extracao.generico import analisar
from ementas_extracao.adaptadores import aplicar_perfil_aprendizagem
from ementas_extracao.tabelas import enriquecer
from ementas_extracao.cobertura import atualizar_cobertura
from ementas_extracao.instituicao import identificar
from ementas_extracao.ocr import ConfigOCR, preparar


def processar(origem: Path, config: ConfigOCR, limites: Limites = Limites()):
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
        auditoria = analisar(linhas, paginas)
        auditoria = aplicar_perfil_aprendizagem(entrada, linhas, auditoria)
        auditoria = enriquecer(entrada, linhas, auditoria)
        auditoria = identificar(origem, auditoria, config)
        auditoria = atualizar_cobertura(auditoria, linhas, paginas)
    auditoria.update(documento=documento, versao_extrator='0.5.0-dev2', processamento_paginas=processamento)
    configuracao = asdict(config)
    configuracao['paginas_forcadas'] = sorted(config.paginas_forcadas)
    auditoria['configuracao'] = configuracao
    auditoria['limites'] = asdict(limites)
    # Linhas originais completas são locais e opcionais de consultar no arquivo de
    # auditoria. Não enviar automaticamente a serviços externos.
    auditoria['linhas'] = linhas
    resultado = {k: auditoria[k] for k in ('documento', 'versao_extrator', 'classificacao', 'status', 'gravacao_no_banco_autorizada')}
    resultado['ementas'] = [{k: r[k] for k in ('numero', 'status', 'dados', 'paginas_com_evidencias', 'paginas_com_campos_extraidos', 'avisos')}
                            for r in auditoria['ementas']]
    resultado['quantidade_candidatos_inconclusivos'] = len(auditoria['candidatos_inconclusivos'])
    return resultado, auditoria


def salvar(destino, obj):
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(destino.suffix + '.tmp')
    temporario.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
    temporario.replace(destino)


def positivo(valor):
    numero = int(valor)
    if numero <= 0:
        raise argparse.ArgumentTypeError('Informe um inteiro positivo.')
    return numero


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('entrada', type=Path)
    parser.add_argument('--saida', type=Path, default=Path('data/saida_v4'))
    parser.add_argument('--ocr', choices=['auto', 'sempre', 'nunca'], default='auto')
    parser.add_argument('--idioma', default='por')
    parser.add_argument('--dpi', type=int, choices=[200, 300, 400], default=300)
    parser.add_argument('--tesseract')
    parser.add_argument('--tessdata')
    parser.add_argument('--max-mb', type=positivo, default=100)
    parser.add_argument('--max-paginas', type=positivo, default=400)
    parser.add_argument('--max-paginas-ocr', type=positivo, default=30)
    parser.add_argument('--timeout-ocr', type=positivo, default=120)
    args = parser.parse_args()
    arquivos = sorted(p for p in args.entrada.iterdir() if p.is_file() and p.suffix.lower() == '.pdf') if args.entrada.is_dir() else [args.entrada]
    if not arquivos or not all(p.is_file() for p in arquivos):
        parser.error('Nenhum arquivo encontrado; a busca na pasta não é recursiva.')
    config = ConfigOCR(modo=args.ocr, idioma=args.idioma, dpi=args.dpi, executavel=args.tesseract,
        tessdata=args.tessdata, timeout=args.timeout_ocr, max_paginas_ocr=args.max_paginas_ocr)
    limites = Limites(args.max_mb, args.max_paginas)
    resumo, hashes = [], set()
    falhas = 0
    for arquivo in arquivos:
        print(f'Processando: {arquivo.name}', flush=True)
        try:
            doc = inspecionar(arquivo, limites)
            if doc['sha256'] in hashes:
                resumo.append({'arquivo': arquivo.name, 'execucao': 'duplicado_ignorado', 'sha256': doc['sha256']})
                continue
            resultado, auditoria = processar(arquivo, config, limites)
            hashes.add(doc['sha256'])
            nome = arquivo.stem + '_' + doc['sha256'][:8]
            salvar(args.saida / (nome + '.academico.json'), resultado)
            salvar(args.saida / 'auditoria' / (nome + '.auditoria.json'), auditoria)
            resumo.append({'arquivo': arquivo.name, 'execucao': 'concluida',
                'classificacao': resultado['classificacao']['resultado'], 'ementas': len(resultado['ementas']),
                'inconclusivos': resultado['quantidade_candidatos_inconclusivos'], 'resultado': nome + '.academico.json'})
            print(f"  {resumo[-1]['classificacao']}: {len(resultado['ementas'])} ementa(s); revisão obrigatória.", flush=True)
        except DocumentoRecusado as erro:
            resumo.append({'arquivo': arquivo.name, 'execucao': 'recusado', 'classificacao': erro.codigo, 'mensagem': str(erro)})
            falhas += 1
        except Exception as erro:
            resumo.append({'arquivo': arquivo.name, 'execucao': 'falhou', 'classificacao': 'falha_processamento',
                           'mensagem': f'{type(erro).__name__}: {erro}'})
            falhas += 1
    salvar(args.saida / 'resumo_execucao.json', resumo)
    return int(falhas > 0)


if __name__ == '__main__':
    raise SystemExit(main())
