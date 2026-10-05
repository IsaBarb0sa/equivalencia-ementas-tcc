"""Registra extração pendente no SQL Server. Sem --gravar, apenas valida arquivos."""
import argparse
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader
from equivalencia_ementas.academico.application.registrar_extracao import LoteExtracao, RegistrarExtracao


class Simulacao:
    def registrar_atomico(self, lote):
        print(f'Arquivos consistentes: {len(lote.academico["ementas"])} ementa(s). Nenhuma gravação realizada.')
        return []


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf',required=True,type=Path)
    parser.add_argument('--academico',required=True,type=Path)
    parser.add_argument('--auditoria',required=True,type=Path)
    parser.add_argument('--gravar',action='store_true')
    args=parser.parse_args()
    with args.pdf.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
    academico=json.loads(args.academico.read_text(encoding='utf-8-sig'))
    auditoria=json.loads(args.auditoria.read_text(encoding='utf-8-sig'))
    lote=LoteExtracao(args.pdf.name,args.pdf.resolve().as_uri(),digest,args.pdf.stat().st_size,
        len(PdfReader(args.pdf).pages),academico['versao_extrator'],academico,auditoria)
    armazenamento=Simulacao()
    if args.gravar:
        from equivalencia_ementas.shared.database.session import SessionFactory
        from equivalencia_ementas.academico.infrastructure.repositories.resultado_extracao_repository import SqlAlchemyArmazenamentoExtracao
        armazenamento=SqlAlchemyArmazenamentoExtracao(SessionFactory)
    ids=RegistrarExtracao(armazenamento).executar(lote)
    if args.gravar: print(f'Resultados registrados/reutilizados: {ids}. Status PENDENTE; ementas ainda não publicadas.')


if __name__=='__main__':main()
