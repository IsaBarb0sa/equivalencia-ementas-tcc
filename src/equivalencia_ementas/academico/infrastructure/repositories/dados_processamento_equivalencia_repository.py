"""Consultas de leitura para processamento automático de solicitações."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from equivalencia_ementas.academico.application.use_cases.processar_solicitacao_equivalencia import (
    DocumentoDaSolicitacao,
)
from equivalencia_ementas.equivalencia.domain.entities import (
    CargaHorariaEquivalencia,
    DisciplinaParaEquivalencia,
)


class SqlAlchemyDadosProcessamentoEquivalenciaRepository:

    def __init__(self, session: Session) -> None:
        self._session = session

    def listar_documentos(
        self,
        protocolo: str,
    ) -> list[DocumentoDaSolicitacao]:

        statement = text("""
            SELECT
                DF.DocumentoFonteId,
                DF.UriArmazenamento,
                SD.NomeArquivoEnviado,
                DF.HashSha256,
                DF.TamanhoBytes,
                DF.QuantidadePaginas

            FROM processamento.Solicitacao S

            INNER JOIN processamento.SolicitacaoDocumento SD
                ON SD.SolicitacaoId = S.SolicitacaoId

            INNER JOIN processamento.DocumentoFonte DF
                ON DF.DocumentoFonteId = SD.DocumentoFonteId

            WHERE S.Protocolo = :protocolo

            ORDER BY DF.DocumentoFonteId
        """)

        linhas = self._session.execute(
            statement,
            {"protocolo": protocolo},
        ).mappings().all()

        return [
            DocumentoDaSolicitacao(
                documento_fonte_id=int(item["DocumentoFonteId"]),
                caminho_pdf=Path(item["UriArmazenamento"]),
                nome_arquivo=item["NomeArquivoEnviado"],
                hash_sha256=item["HashSha256"],
                tamanho_bytes=int(item["TamanhoBytes"]),
                paginas=int(item["QuantidadePaginas"]),
            )
            for item in linhas
        ]

    def listar_matrizes_solicitacao(
        self,
        protocolo: str,
    ) -> list[dict]:
        """
        Lista as matrizes do curso de destino.

        Não escolhe automaticamente uma matriz quando
        existem várias disponíveis.
        """

        statement = text("""
            SELECT
                MC.MatrizCurricularId AS matriz_id,
                MC.Codigo AS codigo,
                MC.Status AS status

            FROM processamento.Solicitacao S

            INNER JOIN academico.MatrizCurricular MC
                ON MC.CursoId = S.CursoDestinoId

            WHERE S.Protocolo = :protocolo

            ORDER BY
                MC.AnoInicioVigencia DESC,
                MC.SemestreInicio DESC,
                MC.MatrizCurricularId DESC
        """)

        linhas = self._session.execute(
            statement,
            {"protocolo": protocolo},
        ).mappings().all()

        return [
            dict(linha)
            for linha in linhas
        ]

    def listar_disciplinas_matriz(
        self,
        *,
        matriz_id: int,
        protocolo: str,
    ) -> list[DisciplinaParaEquivalencia]:
        """
        Recupera as disciplinas da matriz curricular
        associada ao curso de destino da solicitação.

        Inclui as informações das ementas disponíveis.
        """

        statement = text("""
            WITH EmentaOrdenada AS (
                SELECT
                    E.*,

                    ROW_NUMBER() OVER (
                        PARTITION BY E.MatrizDisciplinaId

                        ORDER BY
                            CASE
                                WHEN E.Status = 'PUBLICADA'
                                THEN 0
                                ELSE 1
                            END,
                            E.AtualizadoEm DESC,
                            E.EmentaId DESC
                    ) AS rn

                FROM academico.Ementa E

                WHERE E.Status <> 'ARQUIVADA'
            )

            SELECT
                D.Nome,
                E.EmentaId,
                E.Resumo,
                E.CompetenciasHabilidades,
                E.CargaHorariaDeclarada,
                E.UnidadeCargaHoraria,
                E.CargaHorariaTeorica,
                E.CargaHorariaPratica

            FROM processamento.Solicitacao S

            INNER JOIN academico.MatrizCurricular MC
                ON MC.CursoId = S.CursoDestinoId

            INNER JOIN academico.MatrizDisciplina MD
                ON MD.MatrizCurricularId = MC.MatrizCurricularId
                AND MD.Ativa = 1

            INNER JOIN academico.Disciplina D
                ON D.DisciplinaId = MD.DisciplinaId

            LEFT JOIN EmentaOrdenada E
                ON E.MatrizDisciplinaId = MD.MatrizDisciplinaId
                AND E.rn = 1

            WHERE
                S.Protocolo = :protocolo
                AND MC.MatrizCurricularId = :matriz_id

            ORDER BY
                MD.PeriodoSugerido,
                D.Nome
        """)

        linhas = self._session.execute(
            statement,
            {
                "protocolo": protocolo,
                "matriz_id": matriz_id,
            },
        ).mappings().all()

        if not linhas:
            return []

        # Identifica as ementas encontradas.

        ementa_ids = [
            int(item["EmentaId"])
            for item in linhas
            if item["EmentaId"] is not None
        ]

        conteudos: dict[int, list[str]] = {}
        objetivos: dict[int, dict[str, list[str]]] = {}

        # Recupera conteúdos e objetivos separadamente.
        # Isso evita multiplicar registros nas consultas.

        if ementa_ids:

            consulta_conteudos = text("""
                SELECT
                    EmentaId,
                    TextoOriginal

                FROM academico.ConteudoProgramatico

                WHERE EmentaId IN :ids

                ORDER BY EmentaId, Ordem
            """).bindparams(
                bindparam("ids", expanding=True)
            )

            consulta_objetivos = text("""
                SELECT
                    EmentaId,
                    Tipo,
                    Texto

                FROM academico.ObjetivoEmenta

                WHERE EmentaId IN :ids

                ORDER BY EmentaId, Ordem
            """).bindparams(
                bindparam("ids", expanding=True)
            )

            # Conteúdos programáticos

            linhas_conteudos = self._session.execute(
                consulta_conteudos,
                {"ids": ementa_ids},
            ).mappings()

            for item in linhas_conteudos:

                ementa_id = int(item["EmentaId"])

                conteudos.setdefault(
                    ementa_id,
                    [],
                ).append(
                    item["TextoOriginal"]
                )

            # Objetivos das ementas

            linhas_objetivos = self._session.execute(
                consulta_objetivos,
                {"ids": ementa_ids},
            ).mappings()

            for item in linhas_objetivos:

                ementa_id = int(item["EmentaId"])
                tipo = item["Tipo"]

                objetivos.setdefault(
                    ementa_id,
                    {},
                ).setdefault(
                    tipo,
                    [],
                ).append(
                    item["Texto"]
                )

        # Converte os resultados para os objetos
        # utilizados pelo motor de equivalência.

        disciplinas = []

        for item in linhas:

            ementa_id = (
                int(item["EmentaId"])
                if item["EmentaId"] is not None
                else None
            )

            objetivos_ementa = objetivos.get(
                ementa_id,
                {},
            )

            def juntar_textos(valores):
                return "; ".join(valores) if valores else None

            disciplina = DisciplinaParaEquivalencia(
                nome=item["Nome"],

                identificador=(
                    str(ementa_id)
                    if ementa_id is not None
                    else None
                ),

                ementa=item["Resumo"],

                conteudo_programatico=juntar_textos(
                    conteudos.get(ementa_id, [])
                ),

                objetivo_geral=juntar_textos(
                    objetivos_ementa.get("GERAL", [])
                ),

                objetivos_especificos=juntar_textos(
                    objetivos_ementa.get("ESPECIFICO", [])
                ),

                objetivos_nao_classificados=juntar_textos(
                    objetivos_ementa.get("NAO_CLASSIF", [])
                ),

                competencias_habilidades=item[
                    "CompetenciasHabilidades"
                ],

                carga_horaria=CargaHorariaEquivalencia(
                    total=(
                        float(item["CargaHorariaDeclarada"])
                        if item["CargaHorariaDeclarada"] is not None
                        else None
                    ),

                    teorica=(
                        float(item["CargaHorariaTeorica"])
                        if item["CargaHorariaTeorica"] is not None
                        else None
                    ),

                    pratica=(
                        float(item["CargaHorariaPratica"])
                        if item["CargaHorariaPratica"] is not None
                        else None
                    ),

                    unidade=item["UnidadeCargaHoraria"],
                ),
            )

            disciplinas.append(disciplina)

        return disciplinas