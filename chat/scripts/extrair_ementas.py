"""Uma entrada para PDFs, triagem, segmentação e extração. Não grava no banco."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from ementas_extracao.comum.documento import DocumentoRecusado, Limites, inspecionar
from ementas_extracao.comum.ocr import ConfigOCR
from ementas_extracao.pipeline import processar
from ementas_extracao.roteamento import PERFIS, PENDENTES


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
    parser.add_argument('--instituicao', choices=sorted(PERFIS), default='generico',
                        help='Perfil de extração; não substitui a instituição encontrada no PDF.')
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
    if args.instituicao in PENDENTES:
        print('Perfil específico ainda não implementado; será usado o extrator genérico.', flush=True)
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
            resultado, auditoria = processar(arquivo, config, limites, instituicao=args.instituicao)
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
