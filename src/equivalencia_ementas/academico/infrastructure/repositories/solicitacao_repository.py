from sqlalchemy import text
from sqlalchemy.orm import Session


class SqlAlchemySolicitacaoRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def curso_disponivel(
        self,
        curso_id: int,
        instituicao_id: int,
    ) -> bool:
        statement = text("""
            SELECT CursoId
            FROM academico.Curso WITH (HOLDLOCK)
            WHERE CursoId = :curso_id
              AND InstituicaoId = :instituicao_id
              AND Ativo = 1
        """)

        resultado = self._session.execute(
            statement,
            {
                "curso_id": curso_id,
                "instituicao_id": instituicao_id,
            },
        ).scalar_one_or_none()

        return resultado is not None


    def criar(
        self,
        protocolo: str,
        curso_id: int,
        candidato_usuario_id: int,
    ) -> int:
        statement = text("""
            INSERT INTO processamento.Solicitacao (
                Protocolo,
                CursoDestinoId,
                CandidatoUsuarioId,
                Status
            )
            OUTPUT INSERTED.SolicitacaoId
            VALUES (
                :protocolo,
                :curso_id,
                :candidato_usuario_id,
                'RECEBIDA'
            )
        """)

        return self._session.execute(
            statement,
            {
                "protocolo": protocolo,
                "curso_id": curso_id,
                "candidato_usuario_id": candidato_usuario_id,
            },
        ).scalar_one()


    def obter_ou_criar_documento(
        self,
        *,
        nome: str,
        uri: str,
        hash_sha256: str,
        tamanho: int,
        paginas: int,
    ) -> int:
        # O bloqueio evita duas inserções concorrentes do mesmo hash.
        existente = self._session.execute(
            text("""
                SELECT DocumentoFonteId
                FROM processamento.DocumentoFonte WITH (UPDLOCK, HOLDLOCK)
                WHERE HashSha256 = :hash
            """),
            {"hash": hash_sha256},
        ).scalar_one_or_none()

        if existente is not None:
            # O upload atual garante uma cópia local disponível.
            # Preserva o status e a auditoria do documento existente.
            self._session.execute(
                text("""
                    UPDATE processamento.DocumentoFonte
                    SET UriArmazenamento = :uri
                    WHERE DocumentoFonteId = :documento_id
                """),
                {
                    "uri": uri,
                    "documento_id": existente,
                },
            )
            return existente

        statement = text("""
            INSERT INTO processamento.DocumentoFonte (
                NomeArquivo,
                UriArmazenamento,
                MimeType,
                HashSha256,
                TamanhoBytes,
                QuantidadePaginas,
                Status
            )
            OUTPUT INSERTED.DocumentoFonteId
            VALUES (
                :nome,
                :uri,
                'application/pdf',
                :hash,
                :tamanho,
                :paginas,
                'RECEBIDO'
            )
        """)

        return self._session.execute(
            statement,
            {
                "nome": nome,
                "uri": uri,
                "hash": hash_sha256,
                "tamanho": tamanho,
                "paginas": paginas,
            },
        ).scalar_one()

    def vincular_documento(
        self,
        solicitacao_id: int,
        documento_id: int,
        nome_enviado: str,
    ) -> None:
        self._session.execute(
            text("""
                INSERT INTO processamento.SolicitacaoDocumento (
                    SolicitacaoId,
                    DocumentoFonteId,
                    NomeArquivoEnviado
                )
                VALUES (
                    :solicitacao_id,
                    :documento_id,
                    :nome
                )
            """),
            {
                "solicitacao_id": solicitacao_id,
                "documento_id": documento_id,
                "nome": nome_enviado,
            },
        )



    def listar_solicitacoes(
        self,
        instituicao_id: int,
        candidato_usuario_id: int,
        limite: int = 50,
    ) -> list[dict]:
        statement = text("""
            SELECT TOP (:limite)
                S.SolicitacaoId AS solicitacao_id,
                S.Protocolo AS protocolo,
                S.Status AS status,
                S.CriadoEm AS criado_em,
                C.CursoId AS curso_id,
                C.Nome AS curso_destino,
                COUNT(SD.DocumentoFonteId) AS quantidade_documentos
            FROM processamento.Solicitacao S
            INNER JOIN academico.Curso C
                ON C.CursoId = S.CursoDestinoId
            LEFT JOIN processamento.SolicitacaoDocumento SD
                ON SD.SolicitacaoId = S.SolicitacaoId
            WHERE C.InstituicaoId = :instituicao_id
              AND S.CandidatoUsuarioId = :candidato_usuario_id
            GROUP BY
                S.SolicitacaoId,
                S.Protocolo,
                S.Status,
                S.CriadoEm,
                C.CursoId,
                C.Nome
            ORDER BY
                S.CriadoEm DESC,
                S.SolicitacaoId DESC
        """)

        resultado = self._session.execute(
            statement,
            {
                "instituicao_id": instituicao_id,
                "candidato_usuario_id": candidato_usuario_id,
                "limite": max(1, min(limite, 100)),
            },
        )

        return [
            dict(linha)
            for linha in resultado.mappings().all()
        ]


    def buscar_por_protocolo(
        self,
        protocolo: str,
        instituicao_id: int,
        candidato_usuario_id: int,
    ) -> dict | None:
        statement = text("""
            SELECT
                S.SolicitacaoId AS solicitacao_id,
                S.Protocolo AS protocolo,
                S.Status AS status,
                S.CriadoEm AS criado_em,
                C.CursoId AS curso_id,
                C.Nome AS curso_destino
            FROM processamento.Solicitacao S
            INNER JOIN academico.Curso C
                ON C.CursoId = S.CursoDestinoId
            WHERE S.Protocolo = :protocolo
              AND C.InstituicaoId = :instituicao_id
              AND S.CandidatoUsuarioId = :candidato_usuario_id
        """)

        resultado = self._session.execute(
            statement,
            {
                "protocolo": protocolo,
                "instituicao_id": instituicao_id,
                "candidato_usuario_id": candidato_usuario_id,
            },
        ).mappings().one_or_none()

        if resultado is None:
            return None

        solicitacao = dict(resultado)

        documentos_statement = text("""
            SELECT
                SD.DocumentoFonteId AS documento_id,
                SD.NomeArquivoEnviado AS nome_arquivo,
                DF.QuantidadePaginas AS quantidade_paginas,
                DF.TamanhoBytes AS tamanho_bytes,
                DF.Status AS status_documento
            FROM processamento.SolicitacaoDocumento SD
            INNER JOIN processamento.DocumentoFonte DF
                ON DF.DocumentoFonteId = SD.DocumentoFonteId
            WHERE SD.SolicitacaoId = :solicitacao_id
            ORDER BY SD.DocumentoFonteId
        """)

        documentos = self._session.execute(
            documentos_statement,
            {
                "solicitacao_id": solicitacao["solicitacao_id"],
            },
        )

        solicitacao["documentos"] = [
            dict(linha)
            for linha in documentos.mappings().all()
        ]

        solicitacao["quantidade_documentos"] = len(
            solicitacao["documentos"]
        )

        return solicitacao


    def listar_solicitacoes_coordenador(
        self,
        instituicao_id: int,
        coordenador_usuario_id: int,
        limite: int = 50,
    ) -> list[dict]:
        """
        Lista somente solicitações de cursos vinculados
        ao coordenador autenticado.

        A autorização é aplicada diretamente no SQL.
        """

        statement = text("""
            SELECT TOP (:limite)
                S.SolicitacaoId AS solicitacao_id,
                S.Protocolo AS protocolo,
                S.Status AS status,
                S.CriadoEm AS criado_em,
                C.CursoId AS curso_id,
                C.Nome AS curso_destino,
                COUNT(SD.DocumentoFonteId) AS quantidade_documentos

            FROM processamento.Solicitacao S

            INNER JOIN academico.Curso C
                ON C.CursoId = S.CursoDestinoId

            LEFT JOIN processamento.SolicitacaoDocumento SD
                ON SD.SolicitacaoId = S.SolicitacaoId

            WHERE C.InstituicaoId = :instituicao_id

              AND EXISTS (
                  SELECT 1
                  FROM seguranca.CoordenadorCurso CC
                  WHERE CC.UsuarioId = :coordenador_usuario_id
                    AND CC.CursoId = S.CursoDestinoId
                    AND CC.Ativo = 1
              )

            GROUP BY
                S.SolicitacaoId,
                S.Protocolo,
                S.Status,
                S.CriadoEm,
                C.CursoId,
                C.Nome

            ORDER BY
                S.CriadoEm DESC,
                S.SolicitacaoId DESC
        """)

        resultado = self._session.execute(
            statement,
            {
                "instituicao_id": instituicao_id,
                "coordenador_usuario_id": coordenador_usuario_id,
                "limite": max(1, min(limite, 100)),
            },
        )

        return [
            dict(linha)
            for linha in resultado.mappings().all()
        ]

    def buscar_por_protocolo_coordenador(
        self,
        protocolo: str,
        instituicao_id: int,
        coordenador_usuario_id: int,
    ) -> dict | None:
        """
        Consulta uma solicitação somente se o coordenador
        possuir vínculo ativo com o curso de destino.
        """

        statement = text("""
            SELECT
                S.SolicitacaoId AS solicitacao_id,
                S.Protocolo AS protocolo,
                S.Status AS status,
                S.CriadoEm AS criado_em,
                C.CursoId AS curso_id,
                C.Nome AS curso_destino
            FROM processamento.Solicitacao S
            INNER JOIN academico.Curso C
                ON C.CursoId = S.CursoDestinoId
            WHERE S.Protocolo = :protocolo
              AND C.InstituicaoId = :instituicao_id
              AND EXISTS (
                  SELECT 1
                  FROM seguranca.CoordenadorCurso CC
                  WHERE CC.UsuarioId = :coordenador_usuario_id
                    AND CC.CursoId = S.CursoDestinoId
                    AND CC.Ativo = 1
              )
        """)

        registro = self._session.execute(
            statement,
            {
                "protocolo": protocolo,
                "instituicao_id": instituicao_id,
                "coordenador_usuario_id": coordenador_usuario_id,
            },
        ).mappings().one_or_none()

        if registro is None:
            return None

        solicitacao = dict(registro)

        documentos_statement = text("""
            SELECT
                SD.DocumentoFonteId AS documento_id,
                SD.NomeArquivoEnviado AS nome_arquivo,
                DF.QuantidadePaginas AS quantidade_paginas,
                DF.TamanhoBytes AS tamanho_bytes,
                DF.Status AS status_documento
            FROM processamento.SolicitacaoDocumento SD
            INNER JOIN processamento.DocumentoFonte DF
                ON DF.DocumentoFonteId = SD.DocumentoFonteId
            WHERE SD.SolicitacaoId = :solicitacao_id
            ORDER BY SD.DocumentoFonteId
        """)

        documentos = self._session.execute(
            documentos_statement,
            {
                "solicitacao_id": solicitacao["solicitacao_id"],
            },
        ).mappings().all()

        solicitacao["documentos"] = [
            dict(documento)
            for documento in documentos
        ]

        solicitacao["quantidade_documentos"] = len(
            solicitacao["documentos"]
        )

        return solicitacao

    def buscar_arquivo_documento_coordenador(
        self,
        protocolo: str,
        documento_id: int,
        instituicao_id: int,
        coordenador_usuario_id: int,
    ) -> dict | None:
        """
        Retorna os metadados do PDF somente se:
        - o documento pertencer à solicitação;
        - o curso pertencer à instituição;
        - o coordenador tiver vínculo ativo com o curso.
        """

        statement = text("""
            SELECT
                DF.DocumentoFonteId AS documento_id,
                SD.NomeArquivoEnviado AS nome_arquivo,
                DF.HashSha256 AS hash_sha256
            FROM processamento.Solicitacao S

            INNER JOIN academico.Curso C
                ON C.CursoId = S.CursoDestinoId

            INNER JOIN processamento.SolicitacaoDocumento SD
                ON SD.SolicitacaoId = S.SolicitacaoId

            INNER JOIN processamento.DocumentoFonte DF
                ON DF.DocumentoFonteId = SD.DocumentoFonteId

            WHERE S.Protocolo = :protocolo
              AND DF.DocumentoFonteId = :documento_id
              AND C.InstituicaoId = :instituicao_id

              AND EXISTS (
                  SELECT 1
                  FROM seguranca.CoordenadorCurso CC
                  WHERE CC.UsuarioId = :coordenador_usuario_id
                    AND CC.CursoId = S.CursoDestinoId
                    AND CC.Ativo = 1
              )
        """)

        resultado = self._session.execute(
            statement,
            {
                "protocolo": protocolo,
                "documento_id": documento_id,
                "instituicao_id": instituicao_id,
                "coordenador_usuario_id": coordenador_usuario_id,
            },
        ).mappings().one_or_none()

        return dict(resultado) if resultado is not None else None

    def atualizar_texto_bibliografia_coordenador(
        self,
        *,
        matriz_disciplina_id: int,
        ementa_id: int,
        bibliografia_id: int,
        instituicao_id: int,
        coordenador_usuario_id: int,
        versao_linha: str,
        texto_bibliografia: str,
    ) -> str:
        """
        Atualiza uma bibliografia existente.

        Retornos:
            atualizado
            nao_encontrado
            conflito

        O commit/rollback é responsabilidade do chamador.
        """

        parametros = {
            "matriz_disciplina_id": matriz_disciplina_id,
            "ementa_id": ementa_id,
            "bibliografia_id": bibliografia_id,
            "instituicao_id": instituicao_id,
            "coordenador_usuario_id": coordenador_usuario_id,
            "versao_linha": versao_linha,
            "texto_bibliografia": texto_bibliografia,
        }

        # Confirma que a bibliografia pertence à ementa
        # e que o coordenador está autorizado.
        autorizado = self._session.execute(
            text("""
                SELECT B.BibliografiaId
                FROM academico.Bibliografia B
                INNER JOIN academico.Ementa E
                    ON E.EmentaId = B.EmentaId
                INNER JOIN academico.MatrizDisciplina MD
                    ON MD.MatrizDisciplinaId = E.MatrizDisciplinaId
                   AND MD.DisciplinaId = E.DisciplinaId
                INNER JOIN academico.Disciplina D
                    ON D.DisciplinaId = E.DisciplinaId
                INNER JOIN academico.MatrizCurricular M
                    ON M.MatrizCurricularId = MD.MatrizCurricularId
                INNER JOIN academico.Curso C
                    ON C.CursoId = M.CursoId

                WHERE B.BibliografiaId = :bibliografia_id
                  AND B.EmentaId = :ementa_id
                  AND MD.MatrizDisciplinaId = :matriz_disciplina_id
                  AND C.InstituicaoId = :instituicao_id
                  AND D.InstituicaoId = C.InstituicaoId
                  AND C.Ativo = 1

                  AND EXISTS (
                      SELECT 1
                      FROM seguranca.CoordenadorCurso CC
                      WHERE CC.CursoId = C.CursoId
                        AND CC.UsuarioId = :coordenador_usuario_id
                        AND CC.Ativo = 1
                  )
            """),
            parametros,
        ).scalar_one_or_none()

        if autorizado is None:
            return "nao_encontrado"

        # Verifica a versão e gera uma nova rowversion.
        resultado_ementa = self._session.execute(
            text("""
                UPDATE E
                SET E.AtualizadoEm = SYSUTCDATETIME()
                FROM academico.Ementa E
                INNER JOIN academico.MatrizDisciplina MD
                    ON MD.MatrizDisciplinaId = E.MatrizDisciplinaId
                   AND MD.DisciplinaId = E.DisciplinaId
                INNER JOIN academico.Disciplina D
                    ON D.DisciplinaId = E.DisciplinaId
                INNER JOIN academico.MatrizCurricular M
                    ON M.MatrizCurricularId = MD.MatrizCurricularId
                INNER JOIN academico.Curso C
                    ON C.CursoId = M.CursoId

                WHERE E.EmentaId = :ementa_id
                  AND MD.MatrizDisciplinaId = :matriz_disciplina_id
                  AND C.InstituicaoId = :instituicao_id
                  AND D.InstituicaoId = C.InstituicaoId
                  AND C.Ativo = 1
                  AND E.Status IN ('RASCUNHO', 'EM_REVISAO')
                  AND E.VersaoLinha = CONVERT(
                      VARBINARY(8), :versao_linha, 1
                  )

                  AND EXISTS (
                      SELECT 1
                      FROM seguranca.CoordenadorCurso CC
                      WHERE CC.CursoId = C.CursoId
                        AND CC.UsuarioId = :coordenador_usuario_id
                        AND CC.Ativo = 1
                  )
            """),
            parametros,
        )

        if resultado_ementa.rowcount == 0:
            return "conflito"

        if resultado_ementa.rowcount != 1:
            raise RuntimeError(
                "Não foi possível confirmar a versão da ementa."
            )

        resultado_bibliografia = self._session.execute(
            text("""
                UPDATE academico.Bibliografia
                SET ReferenciaTexto = :texto_bibliografia
                WHERE BibliografiaId = :bibliografia_id
                  AND EmentaId = :ementa_id
            """),
            parametros,
        )

        if resultado_bibliografia.rowcount != 1:
            raise RuntimeError(
                "Não foi possível atualizar a bibliografia."
            )

        return "atualizado"
