
from sqlalchemy import text
from sqlalchemy.orm import Session
from decimal import Decimal


class SqlAlchemyCatalogoInstitucionalRepository:

    def __init__(self, session: Session) -> None:
        self._session = session

    def listar_cursos_coordenador(
        self,
        instituicao_id: int,
        coordenador_usuario_id: int,
    ) -> list[dict]:

        statement = text("""
            SELECT
                C.CursoId AS curso_id,
                C.Codigo AS codigo,
                C.Nome AS nome,
                C.Nivel AS nivel,
                C.Modalidade AS modalidade
            FROM academico.Curso C

            WHERE C.InstituicaoId = :instituicao_id
              AND C.Ativo = 1
              AND EXISTS (
                  SELECT 1
                  FROM seguranca.CoordenadorCurso CC
                  WHERE CC.CursoId = C.CursoId
                    AND CC.UsuarioId = :coordenador_usuario_id
                    AND CC.Ativo = 1
              )

            ORDER BY C.Nome, C.CursoId
        """)

        resultado = self._session.execute(
            statement,
            {
                "instituicao_id": instituicao_id,
                "coordenador_usuario_id": coordenador_usuario_id,
            },
        )

        return [
            dict(linha)
            for linha in resultado.mappings().all()
        ]

    def listar_matrizes_coordenador(
        self,
        curso_id: int,
        instituicao_id: int,
        coordenador_usuario_id: int,
    ) -> list[dict] | None:

        # Confirma o vínculo antes de consultar as matrizes.
        autorizado = self._session.execute(
            text("""
                SELECT C.CursoId
                FROM academico.Curso C
                WHERE C.CursoId = :curso_id
                  AND C.InstituicaoId = :instituicao_id
                  AND C.Ativo = 1
                  AND EXISTS (
                      SELECT 1
                      FROM seguranca.CoordenadorCurso CC
                      WHERE CC.CursoId = C.CursoId
                        AND CC.UsuarioId = :coordenador_usuario_id
                        AND CC.Ativo = 1
                  )
            """),
            {
                "curso_id": curso_id,
                "instituicao_id": instituicao_id,
                "coordenador_usuario_id": coordenador_usuario_id,
            },
        ).scalar_one_or_none()

        if autorizado is None:
            return None

        statement = text("""
            SELECT
                M.MatrizCurricularId AS matriz_curricular_id,
                M.CursoId AS curso_id,
                M.Codigo AS codigo,
                M.Nome AS nome,
                M.AnoInicioVigencia AS ano_inicio_vigencia,
                M.SemestreInicio AS semestre_inicio,
                M.AnoFimVigencia AS ano_fim_vigencia,
                M.SemestreFim AS semestre_fim,
                M.Status AS status
            FROM academico.MatrizCurricular M
            WHERE M.CursoId = :curso_id
              AND EXISTS (
                  SELECT 1
                  FROM academico.Curso C
                  INNER JOIN seguranca.CoordenadorCurso CC
                      ON CC.CursoId = C.CursoId
                  WHERE C.CursoId = M.CursoId
                    AND C.InstituicaoId = :instituicao_id
                    AND C.Ativo = 1
                    AND CC.UsuarioId = :coordenador_usuario_id
                    AND CC.Ativo = 1
              )
            ORDER BY
                M.AnoInicioVigencia DESC,
                M.SemestreInicio DESC,
                M.MatrizCurricularId DESC
        """)

        resultado = self._session.execute(
            statement,
            {
                "curso_id": curso_id,
                "instituicao_id": instituicao_id,
                "coordenador_usuario_id": coordenador_usuario_id,
            },
        )

        return [
            dict(linha)
            for linha in resultado.mappings().all()
        ]

    def listar_disciplinas_matriz_coordenador(
        self,
        matriz_curricular_id: int,
        instituicao_id: int,
        coordenador_usuario_id: int,
    ) -> list[dict] | None:

        autorizado = self._session.execute(
            text("""
                SELECT M.MatrizCurricularId
                FROM academico.MatrizCurricular M
                INNER JOIN academico.Curso C
                    ON C.CursoId = M.CursoId
                WHERE M.MatrizCurricularId = :matriz_id
                  AND C.InstituicaoId = :instituicao_id
                  AND C.Ativo = 1
                  AND EXISTS (
                      SELECT 1
                      FROM seguranca.CoordenadorCurso CC
                      WHERE CC.CursoId = C.CursoId
                        AND CC.UsuarioId = :usuario_id
                        AND CC.Ativo = 1
                  )
            """),
            {
                "matriz_id": matriz_curricular_id,
                "instituicao_id": instituicao_id,
                "usuario_id": coordenador_usuario_id,
            },
        ).scalar_one_or_none()

        if autorizado is None:
            return None

        statement = text("""
            SELECT
                MD.MatrizDisciplinaId AS matriz_disciplina_id,
                D.DisciplinaId AS disciplina_id,
                D.Codigo AS codigo,
                D.Nome AS nome,
                MD.PeriodoSugerido AS periodo_sugerido,
                MD.Natureza AS natureza,

                COALESCE(EV.quantidade_ementas, 0)
                    AS quantidade_ementas,

                EV.ementa_id,
                EV.versao,
                EV.status_ementa,
                EV.carga_horaria

            FROM academico.MatrizDisciplina MD

            INNER JOIN academico.MatrizCurricular M
                ON M.MatrizCurricularId = MD.MatrizCurricularId

            INNER JOIN academico.Curso C
                ON C.CursoId = M.CursoId

            INNER JOIN academico.Disciplina D
                ON D.DisciplinaId = MD.DisciplinaId
               AND D.InstituicaoId = C.InstituicaoId

            OUTER APPLY (
                SELECT TOP (1)
                    E.EmentaId AS ementa_id,
                    E.Versao AS versao,
                    E.Status AS status_ementa,
                    E.CargaHorariaDeclarada AS carga_horaria,

                    COUNT(*) OVER ()
                        AS quantidade_ementas

                FROM academico.Ementa E

                WHERE E.DisciplinaId = MD.DisciplinaId
                  AND E.MatrizDisciplinaId = MD.MatrizDisciplinaId

                ORDER BY
                    CASE WHEN E.Status = 'PUBLICADA'
                         THEN 0 ELSE 1 END,
                    E.EmentaId DESC
            ) EV

            WHERE MD.MatrizCurricularId = :matriz_id
              AND MD.Ativa = 1
              AND D.Ativa = 1
              AND C.InstituicaoId = :instituicao_id
              AND C.Ativo = 1

              AND EXISTS (
                  SELECT 1
                  FROM seguranca.CoordenadorCurso CC
                  WHERE CC.CursoId = C.CursoId
                    AND CC.UsuarioId = :usuario_id
                    AND CC.Ativo = 1
              )

            ORDER BY
                MD.PeriodoSugerido,
                D.Nome,
                MD.MatrizDisciplinaId
        """)

        resultado = self._session.execute(
            statement,
            {
                "matriz_id": matriz_curricular_id,
                "instituicao_id": instituicao_id,
                "usuario_id": coordenador_usuario_id,
            },
        )

        return [
            dict(linha)
            for linha in resultado.mappings().all()
        ]

    def buscar_ementa_coordenador(
        self,
        matriz_disciplina_id: int,
        ementa_id: int,
        instituicao_id: int,
        coordenador_usuario_id: int,
    ) -> dict | None:
        """
        Consulta uma ementa vinculada à disciplina da matriz,
        respeitando os cursos autorizados ao coordenador.
        """

        statement = text("""
            SELECT
                E.EmentaId AS ementa_id,
                E.MatrizDisciplinaId AS matriz_disciplina_id,
                E.DisciplinaId AS disciplina_id,
                D.Codigo AS codigo_disciplina,
                D.Nome AS nome_disciplina,
                M.MatrizCurricularId AS matriz_curricular_id,
                M.Codigo AS codigo_matriz,
                M.Nome AS nome_matriz,
                C.CursoId AS curso_id,
                C.Nome AS nome_curso,

                E.Versao AS versao,
                E.Status AS status,
                E.Idioma AS idioma,
                E.AnoVigencia AS ano_vigencia,
                E.SemestreVigencia AS semestre_vigencia,

                E.Resumo AS resumo,
                E.CompetenciasHabilidades AS competencias_habilidades,

                E.CargaHorariaDeclarada AS carga_horaria_total,
                E.CargaHorariaTeorica AS carga_horaria_teorica,
                E.CargaHorariaPratica AS carga_horaria_pratica,
                E.UnidadeCargaHoraria AS unidade_carga_horaria,

                E.CriadoEm AS criado_em,
                E.AtualizadoEm AS atualizado_em,    
                CONVERT(VARCHAR(18), CONVERT(VARBINARY(8), E.VersaoLinha), 1) AS versao_linha

            FROM academico.Ementa E

            INNER JOIN academico.MatrizDisciplina MD
                ON MD.MatrizDisciplinaId = E.MatrizDisciplinaId
               AND MD.DisciplinaId = E.DisciplinaId

            INNER JOIN academico.Disciplina D
                ON D.DisciplinaId = MD.DisciplinaId

            INNER JOIN academico.MatrizCurricular M
                ON M.MatrizCurricularId = MD.MatrizCurricularId

            INNER JOIN academico.Curso C
                ON C.CursoId = M.CursoId

            WHERE E.EmentaId = :ementa_id
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
        """)

        registro = self._session.execute(
            statement,
            {
                "ementa_id": ementa_id,
                "matriz_disciplina_id": matriz_disciplina_id,
                "instituicao_id": instituicao_id,
                "coordenador_usuario_id": coordenador_usuario_id,
            },
        ).mappings().one_or_none()


        if registro is None:
            return None

        ementa = dict(registro)

        parametros = {
            "ementa_id": ementa["ementa_id"],
        }

        # Objetivos da ementa
        objetivos = self._session.execute(
            text("""
                SELECT
                    ObjetivoEmentaId AS objetivo_id,
                    Ordem AS ordem,
                    Tipo AS tipo,
                    Texto AS texto
                FROM academico.ObjetivoEmenta
                WHERE EmentaId = :ementa_id
                ORDER BY Ordem, ObjetivoEmentaId
            """),
            parametros,
        ).mappings().all()

        # Conteúdo programático
        conteudos = self._session.execute(
            text("""
                SELECT
                    ConteudoProgramaticoId AS conteudo_id,
                    Ordem AS ordem,
                    Titulo AS titulo,
                    TextoOriginal AS texto
                FROM academico.ConteudoProgramatico
                WHERE EmentaId = :ementa_id
                ORDER BY Ordem, ConteudoProgramaticoId
            """),
            parametros,
        ).mappings().all()

        # Referências bibliográficas
        bibliografias = self._session.execute(
            text("""
                SELECT
                    BibliografiaId AS bibliografia_id,
                    Ordem AS ordem,
                    Tipo AS tipo,
                    ReferenciaTexto AS referencia,
                    Isbn AS isbn
                FROM academico.Bibliografia
                WHERE EmentaId = :ementa_id
                ORDER BY Ordem, BibliografiaId
            """),
            parametros,
        ).mappings().all()

        ementa["objetivos"] = [
            dict(item) for item in objetivos
        ]

        ementa["conteudos_programaticos"] = [
            dict(item) for item in conteudos
        ]

        ementa["bibliografias"] = [
            dict(item) for item in bibliografias
        ]

        return ementa

    def atualizar_ementa_coordenador(
        self,
        *,
        matriz_disciplina_id: int,
        ementa_id: int,
        instituicao_id: int,
        coordenador_usuario_id: int,
        versao_linha: str,
        resumo: str | None,
        competencias_habilidades: str | None,
        carga_horaria_total: Decimal | None,
        carga_horaria_teorica: Decimal | None,
        carga_horaria_pratica: Decimal | None,
    ) -> str:
        """
        Atualiza campos principais da ementa.

        Retornos:
        - "atualizado": alteração realizada
        - "nao_encontrado": ementa inexistente ou sem autorização
        - "conflito": versão desatualizada ou ementa não editável

        A transação deve ser controlada pelo chamador.
        """

        statement = text("""
            UPDATE E
            SET
                E.Resumo = :resumo,
                E.CompetenciasHabilidades = :competencias,
                E.CargaHorariaDeclarada = :carga_total,
                E.CargaHorariaTeorica = :carga_teorica,
                E.CargaHorariaPratica = :carga_pratica,
                E.AtualizadoEm = SYSUTCDATETIME()

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
                  VARBINARY(8),
                  :versao_linha,
                  1
              )

              AND EXISTS (
                  SELECT 1
                  FROM seguranca.CoordenadorCurso CC
                  WHERE CC.CursoId = C.CursoId
                    AND CC.UsuarioId = :coordenador_usuario_id
                    AND CC.Ativo = 1
              )
        """)

        parametros = {
            "ementa_id": ementa_id,
            "matriz_disciplina_id": matriz_disciplina_id,
            "instituicao_id": instituicao_id,
            "coordenador_usuario_id": coordenador_usuario_id,
            "versao_linha": versao_linha,
            "resumo": resumo,
            "competencias": competencias_habilidades,
            "carga_total": carga_horaria_total,
            "carga_teorica": carga_horaria_teorica,
            "carga_pratica": carga_horaria_pratica,
        }

        resultado = self._session.execute(
            statement,
            parametros,
        )

        if resultado.rowcount == 1:
            return "atualizado"

        if resultado.rowcount != 0:
            raise RuntimeError(
                "Não foi possível confirmar a atualização da ementa."
            )

        # Identifica se a falha ocorreu por falta de autorização
        # ou por uma edição concorrente / status não editável.
        verificacao = self._session.execute(
            text("""
                SELECT E.EmentaId
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

                  AND EXISTS (
                      SELECT 1
                      FROM seguranca.CoordenadorCurso CC
                      WHERE CC.CursoId = C.CursoId
                        AND CC.UsuarioId = :coordenador_usuario_id
                        AND CC.Ativo = 1
                  )
            """),
            {
                "ementa_id": ementa_id,
                "matriz_disciplina_id": matriz_disciplina_id,
                "instituicao_id": instituicao_id,
                "coordenador_usuario_id": coordenador_usuario_id,
            },
        ).scalar_one_or_none()

        if verificacao is None:
            return "nao_encontrado"

        return "conflito"


    def atualizar_texto_objetivo_coordenador(
        self,
        *,
        matriz_disciplina_id: int,
        ementa_id: int,
        objetivo_id: int,
        instituicao_id: int,
        coordenador_usuario_id: int,
        versao_linha: str,
        texto_objetivo: str,
    ) -> str:
        """
        Atualiza o texto de um objetivo existente.

        Retornos:
            atualizado
            nao_encontrado
            conflito

        O commit/rollback é responsabilidade do chamador.
        """

        parametros = {
            "matriz_disciplina_id": matriz_disciplina_id,
            "ementa_id": ementa_id,
            "objetivo_id": objetivo_id,
            "instituicao_id": instituicao_id,
            "coordenador_usuario_id": coordenador_usuario_id,
            "versao_linha": versao_linha,
            "texto_objetivo": texto_objetivo,
        }

        # Primeiro confirma que o objetivo pertence à ementa
        # e que o coordenador pode acessar esse registro.
        objetivo = self._session.execute(
            text("""
                SELECT O.ObjetivoEmentaId
                FROM academico.ObjetivoEmenta O
                INNER JOIN academico.Ementa E
                    ON E.EmentaId = O.EmentaId
                INNER JOIN academico.MatrizDisciplina MD
                    ON MD.MatrizDisciplinaId = E.MatrizDisciplinaId
                   AND MD.DisciplinaId = E.DisciplinaId
                INNER JOIN academico.Disciplina D
                    ON D.DisciplinaId = E.DisciplinaId
                INNER JOIN academico.MatrizCurricular M
                    ON M.MatrizCurricularId = MD.MatrizCurricularId
                INNER JOIN academico.Curso C
                    ON C.CursoId = M.CursoId
                WHERE O.ObjetivoEmentaId = :objetivo_id
                  AND E.EmentaId = :ementa_id
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

        if objetivo is None:
            return "nao_encontrado"

        # Atualiza a ementa apenas se a versão ainda for atual.
        # Isso também gera uma nova VersaoLinha.
        resultado = self._session.execute(
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

        if resultado.rowcount == 0:
            return "conflito"

        if resultado.rowcount != 1:
            raise RuntimeError(
                "Não foi possível confirmar a versão da ementa."
            )

        # A alteração do objetivo ocorre na mesma transação.
        resultado_objetivo = self._session.execute(
            text("""
                UPDATE academico.ObjetivoEmenta
                SET Texto = :texto_objetivo
                WHERE ObjetivoEmentaId = :objetivo_id
                  AND EmentaId = :ementa_id
            """),
            parametros,
        )

        if resultado_objetivo.rowcount != 1:
            raise RuntimeError(
                "O objetivo não pôde ser atualizado."
            )

        return "atualizado"

    def atualizar_texto_conteudo_coordenador(
        self,
        *,
        matriz_disciplina_id: int,
        ementa_id: int,
        conteudo_id: int,
        instituicao_id: int,
        coordenador_usuario_id: int,
        versao_linha: str,
        texto_conteudo: str,
    ) -> str:
        """
        Atualiza o texto original de um tópico programático.

        Retornos:
          atualizado
          nao_encontrado
          conflito

        A transação é controlada pelo chamador.
        """

        parametros = {
            "matriz_disciplina_id": matriz_disciplina_id,
            "ementa_id": ementa_id,
            "conteudo_id": conteudo_id,
            "instituicao_id": instituicao_id,
            "coordenador_usuario_id": coordenador_usuario_id,
            "versao_linha": versao_linha,
            "texto_conteudo": texto_conteudo,
        }

        # Confirma a existência do tópico e a autorização.
        autorizado = self._session.execute(
            text("""
                SELECT CP.ConteudoProgramaticoId
                FROM academico.ConteudoProgramatico CP
                INNER JOIN academico.Ementa E
                    ON E.EmentaId = CP.EmentaId
                INNER JOIN academico.MatrizDisciplina MD
                    ON MD.MatrizDisciplinaId = E.MatrizDisciplinaId
                   AND MD.DisciplinaId = E.DisciplinaId
                INNER JOIN academico.Disciplina D
                    ON D.DisciplinaId = E.DisciplinaId
                INNER JOIN academico.MatrizCurricular M
                    ON M.MatrizCurricularId = MD.MatrizCurricularId
                INNER JOIN academico.Curso C
                    ON C.CursoId = M.CursoId
                WHERE CP.ConteudoProgramaticoId = :conteudo_id
                  AND E.EmentaId = :ementa_id
                  AND MD.MatrizDisciplinaId = :matriz_disciplina_id
                  AND D.InstituicaoId = C.InstituicaoId
                  AND C.InstituicaoId = :instituicao_id
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

        # Bloqueia alterações baseadas em versões antigas
        # e gera uma nova VersaoLinha da ementa.
        resultado = self._session.execute(
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
                  AND D.InstituicaoId = C.InstituicaoId
                  AND C.InstituicaoId = :instituicao_id
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

        if resultado.rowcount == 0:
            return "conflito"

        if resultado.rowcount != 1:
            raise RuntimeError(
                "Não foi possível confirmar a versão da ementa."
            )

        # Atualiza apenas o tópico solicitado.
        resultado_conteudo = self._session.execute(
            text("""
                UPDATE academico.ConteudoProgramatico
                SET TextoOriginal = :texto_conteudo
                WHERE ConteudoProgramaticoId = :conteudo_id
                  AND EmentaId = :ementa_id
            """),
            parametros,
        )

        if resultado_conteudo.rowcount != 1:
            raise RuntimeError(
                "Não foi possível atualizar o tópico."
            )

        return "atualizado"
