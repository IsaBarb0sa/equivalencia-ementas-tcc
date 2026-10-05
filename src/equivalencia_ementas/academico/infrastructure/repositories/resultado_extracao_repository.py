"""Persiste o lote em uma única transação, sem publicar ementas."""
import json

from sqlalchemy import MetaData, Table, select

from equivalencia_ementas.academico.application.registrar_extracao import (
    LoteExtracao,
    registros_por_numero,
)


class SqlAlchemyArmazenamentoExtracao:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    def registrar_atomico(self, lote: LoteExtracao) -> list[int]:
        registros = registros_por_numero(lote.academico)
        auditoria_json = json.dumps(lote.auditoria, ensure_ascii=False, allow_nan=False)
        ids = []
        with self._session_factory.begin() as session:
            # Usa o schema aplicado pelas migrations, inclusive defaults e identidades.
            metadata = MetaData()
            conexao = session.connection()
            documentos = Table("DocumentoFonte", metadata, schema="processamento",
                               autoload_with=conexao, resolve_fks=False)
            resultados = Table("ResultadoExtracao", metadata, schema="processamento",
                              autoload_with=conexao, resolve_fks=False)
            consulta = select(documentos).where(documentos.c.HashSha256 == lote.hash_sha256)
            # Serializa a criação da identidade no SQL Server, inclusive quando ausente.
            consulta = consulta.with_hint(documentos, "WITH (UPDLOCK, HOLDLOCK)", "mssql")
            documento = session.execute(consulta).mappings().one_or_none()
            if documento is None:
                insercao = session.execute(documentos.insert().values(
                    NomeArquivo=lote.nome_arquivo, UriArmazenamento=lote.uri_armazenamento,
                    MimeType="application/pdf", HashSha256=lote.hash_sha256,
                    TamanhoBytes=lote.tamanho_bytes, QuantidadePaginas=lote.paginas,
                    Status="PROCESSADO",
                ))
                documento_id = insercao.inserted_primary_key[0]
            else:
                if (documento["TamanhoBytes"] != lote.tamanho_bytes
                        or documento["QuantidadePaginas"] != lote.paginas):
                    raise ValueError("Metadados divergentes para o documento já registrado.")
                documento_id = documento["DocumentoFonteId"]
            existentes = session.execute(select(resultados).where(
                resultados.c.DocumentoFonteId == documento_id,
                resultados.c.VersaoExtrator == lote.versao_extrator,
            )).mappings().all()
            por_numero = {r["NumeroEmenta"]: r for r in existentes}
            if por_numero and por_numero.keys() != registros.keys():
                raise ValueError("Conjunto de ementas divergente do lote já registrado.")
            for numero, registro in registros.items():
                dados_json = json.dumps(registro["dados"], ensure_ascii=False, allow_nan=False)
                existente = por_numero.get(numero)
                if existente is not None:
                    if (json.loads(existente["DadosExtraidosJson"]) != registro["dados"]
                            or json.loads(existente["AuditoriaJson"]) != lote.auditoria):
                        raise ValueError("Resultado divergente; o registro existente foi preservado.")
                    ids.append(existente["ResultadoExtracaoId"])
                    continue
                insercao = session.execute(resultados.insert().values(
                    DocumentoFonteId=documento_id, NumeroEmenta=numero,
                    VersaoExtrator=lote.versao_extrator, DadosExtraidosJson=dados_json,
                    AuditoriaJson=auditoria_json, Status="PENDENTE",
                ))
                ids.append(insercao.inserted_primary_key[0])
        return ids
