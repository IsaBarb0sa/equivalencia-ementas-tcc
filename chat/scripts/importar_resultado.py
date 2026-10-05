"""Revisão e importação de resultado persistido; preparação e simulação sem gravação."""
import argparse
import json
from pathlib import Path
from equivalencia_ementas.academico.application.importar_resultado import ImportarResultado


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='acao',required=True)
    p=sub.add_parser('preparar');p.add_argument('--resultado-id',required=True,type=int);p.add_argument('--saida',required=True,type=Path)
    for acao in ('validar','importar'):
        p=sub.add_parser(acao);p.add_argument('--revisao',required=True,type=Path)
    args=parser.parse_args()
    from equivalencia_ementas.shared.database.session import SessionFactory
    from equivalencia_ementas.academico.infrastructure.repositories.importacao_resultado_repository import SqlAlchemyImportacaoResultado
    caso=ImportarResultado(SqlAlchemyImportacaoResultado(SessionFactory))
    try:
        if args.acao=='preparar':
            form=caso.preparar(args.resultado_id)
            args.saida.parent.mkdir(parents=True,exist_ok=True)
            # Não sobrescrever revisão que a usuária já editou.
            with args.saida.open('x',encoding='utf-8') as f:json.dump(form,f,ensure_ascii=False,indent=2,allow_nan=False)
            print(f'Revisão criada em {args.saida}. Preencha cadastro, confira dados, informe revisado_por e confirmado.')
        else:
            form=json.loads(args.revisao.read_text(encoding='utf-8-sig'))
            resultado=caso.executar(form,simular=args.acao=='validar')
            print(json.dumps(resultado,ensure_ascii=False,indent=2))
    except (ValueError,KeyError,FileExistsError) as erro:
        parser.exit(1,f'Não concluído: {erro}\n')


if __name__=='__main__':main()
