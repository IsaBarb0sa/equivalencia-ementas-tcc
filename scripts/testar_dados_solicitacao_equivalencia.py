"""Diagnóstico somente leitura dos dados necessários ao processamento."""

import argparse

from equivalencia_ementas.academico.infrastructure.repositories.dados_processamento_equivalencia_repository import (
    SqlAlchemyDadosProcessamentoEquivalenciaRepository,
)
from equivalencia_ementas.shared.database.session import SessionFactory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocolo", required=True)
    parser.add_argument("--matriz-id", type=int)
    argumentos = parser.parse_args()

    with SessionFactory() as session:
        repositorio = SqlAlchemyDadosProcessamentoEquivalenciaRepository(session)
        documentos = repositorio.listar_documentos(argumentos.protocolo)
        matrizes = repositorio.listar_matrizes_solicitacao(argumentos.protocolo)

        print(f"Documentos associados: {len(documentos)}")
        for item in documentos:
            print(f"  {item.documento_fonte_id}: {item.nome_arquivo} ({item.paginas} páginas)")
        print(f"Matrizes encontradas: {len(matrizes)}")
        for matriz in matrizes:
            print(f"  {matriz['matriz_id']}: {matriz['codigo']} [{matriz['status']}]")

        if argumentos.matriz_id is not None:
            disciplinas = repositorio.listar_disciplinas_matriz(
                matriz_id=argumentos.matriz_id,
                protocolo=argumentos.protocolo,
            )
            print(f"Disciplinas da matriz: {len(disciplinas)}")
            for disciplina in disciplinas:
                print(f"  {disciplina.nome} | tem conteúdo: {disciplina.possui_conteudo_semantico()}")


if __name__ == "__main__":
    main()
