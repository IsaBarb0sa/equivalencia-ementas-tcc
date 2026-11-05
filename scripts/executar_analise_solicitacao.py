
"""Teste integrado controlado: PDF -> Gemini -> extrações -> sugestões.

Sem --executar: somente valida as informações e NÃO chama IA nem altera o banco.
Com --executar: pode consumir créditos Gemini e gravar ResultadoExtracao.
Não registra decisões acadêmicas nem persiste avaliações de equivalência.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from equivalencia_ementas.academico.application.registrar_extracao import RegistrarExtracao
from equivalencia_ementas.academico.application.use_cases.processar_solicitacao_equivalencia import (
    ProcessarSolicitacaoEquivalencia,
)
from equivalencia_ementas.academico.infrastructure.repositories.dados_processamento_equivalencia_repository import (
    SqlAlchemyDadosProcessamentoEquivalenciaRepository,
)
from equivalencia_ementas.academico.infrastructure.repositories.resultado_extracao_repository import (
    SqlAlchemyArmazenamentoExtracao,
)
from equivalencia_ementas.equivalencia.application.analisar_documento import AnalisarDocumento
from equivalencia_ementas.equivalencia.application.comparar_disciplina_com_matriz import (
    CompararDisciplinaComMatriz,
)
from equivalencia_ementas.equivalencia.application.comparar_trechos import CompararTrechos
from equivalencia_ementas.equivalencia.infrastructure.ia.sentence_transformer import (
    GeradorSentenceTransformer,
)
from equivalencia_ementas.infraestrutura.ia.cliente_gemini import ExtratorGemini
from equivalencia_ementas.infraestrutura.ia.processador_documento import (
    ProcessadorDocumentoIA,
    VERSAO_CACHE_GEMINI,
)
from equivalencia_ementas.shared.database.session import SessionFactory


def sha256(caminho: Path) -> str:
    digest = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocolo", required=True)
    parser.add_argument("--matriz-id", required=True, type=int)
    parser.add_argument("--executar", action="store_true", help="Chama Gemini e grava as extrações")
    args = parser.parse_args()

    with SessionFactory() as session:
        repository = SqlAlchemyDadosProcessamentoEquivalenciaRepository(session)
        documentos = repository.listar_documentos(args.protocolo)
        matrizes = repository.listar_matrizes_solicitacao(args.protocolo)
        if args.matriz_id not in {m["matriz_id"] for m in matrizes}:
            raise ValueError("Matriz não pertence ao curso desta solicitação.")
        matriz = repository.listar_disciplinas_matriz(
            matriz_id=args.matriz_id, protocolo=args.protocolo
        )

    if not documentos:
        raise ValueError("Solicitação sem documentos vinculados.")
    if not matriz:
        raise ValueError("Matriz sem disciplinas cadastradas.")

    for item in documentos:
        if not item.caminho_pdf.is_file():
            raise FileNotFoundError(f"PDF não encontrado: {item.caminho_pdf}")
        if sha256(item.caminho_pdf).lower() != item.hash_sha256.strip().lower():
            raise ValueError(f"Hash divergente: {item.nome_arquivo}")
        print(f"Documento OK: {item.nome_arquivo} ({item.paginas} páginas)")

    print(f"Matriz {args.matriz_id}: {len(matriz)} disciplinas")
    print(f"Documentos verificados: {len(documentos)}")
    if not args.executar:
        print("PRÉ-VALIDAÇÃO OK. Nenhuma IA chamada e nenhuma gravação efetuada.")
        print("Para processar de fato, acrescente --executar.")
        return

    # Cria clientes pesados apenas após a pré-validação e opção explícita.
    cliente = ExtratorGemini()
    extrator = ProcessadorDocumentoIA(cliente)
    embeddings = GeradorSentenceTransformer()
    comparar_matriz = CompararDisciplinaComMatriz(
        comparador=CompararTrechos(embeddings),
        contar_tokens=embeddings.contar_tokens,
        limite_tokens=embeddings.limite_tokens,
    )
    processamento = ProcessarSolicitacaoEquivalencia(
        extrator=extrator,
        registrador=RegistrarExtracao(SqlAlchemyArmazenamentoExtracao(SessionFactory)),
        analisador=AnalisarDocumento(comparar_matriz),
        versao_extrator=f"gemini-blocos-v{VERSAO_CACHE_GEMINI}",
    )
    resultado = processamento.executar(documentos=documentos, disciplinas_matriz=matriz)

    print(f"\nDisciplinas de origem extraídas: {resultado.quantidade_disciplinas}")
    print(f"Documentos sem disciplinas: {resultado.quantidade_sem_disciplinas}")
    print("PRÉ-ANÁLISE EXPERIMENTAL — NÃO É DECISÃO ACADÊMICA")
    for grupo in resultado.analises:
        print(f"\nORIGEM: {grupo.disciplina_origem}")
        # Exibe somente as três melhores coberturas para um relatório legível.
        sugestoes = sorted(
            grupo.sugestoes,
            key=lambda s: (s.cobertura_destino is not None, s.cobertura_destino or 0),
            reverse=True,
        )[:3]
        for sugestao in sugestoes:
            percentual = (
                f"{sugestao.cobertura_destino:.0%}"
                if sugestao.cobertura_destino is not None else "indisponível"
            )
            print(f"  -> {sugestao.disciplina_destino}: {sugestao.indicacao.value} "
                  f"(cobertura experimental: {percentual})")
    print("\nAs indicações NÃO foram gravadas como pareceres de coordenador.")


if __name__ == "__main__":
    main()