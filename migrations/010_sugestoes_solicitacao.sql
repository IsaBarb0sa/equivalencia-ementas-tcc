/*
 * Sugestões automáticas de aproveitamento vinculadas à solicitação.
 */
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(N'equivalencia.SugestaoSolicitacao', N'U') IS NULL
    BEGIN
        CREATE TABLE equivalencia.SugestaoSolicitacao (
            SugestaoSolicitacaoId BIGINT IDENTITY(1,1) NOT NULL,
            SolicitacaoId BIGINT NOT NULL,
            ResultadoExtracaoId BIGINT NOT NULL,
            EmentaMatrizId BIGINT NOT NULL,
            VersaoMotor NVARCHAR(50) NOT NULL,
            PoliticaVersao NVARCHAR(50) NOT NULL,
            Indicacao VARCHAR(25) NOT NULL,
            CoberturaDestino DECIMAL(6,5) NULL,
            CargaCompativel BIT NULL,
            EvidenciasJson NVARCHAR(MAX) NOT NULL,
            JustificativasJson NVARCHAR(MAX) NOT NULL,
            Status VARCHAR(25) NOT NULL
                CONSTRAINT DF_SugestaoSolicitacao_Status DEFAULT ('AGUARDANDO_VALIDACAO'),
            CriadoEm DATETIME2(3) NOT NULL
                CONSTRAINT DF_SugestaoSolicitacao_CriadoEm DEFAULT (SYSUTCDATETIME()),

            CONSTRAINT PK_SugestaoSolicitacao PRIMARY KEY (SugestaoSolicitacaoId),
            CONSTRAINT FK_SugestaoSolicitacao_Solicitacao FOREIGN KEY (SolicitacaoId)
                REFERENCES processamento.Solicitacao (SolicitacaoId),
            CONSTRAINT FK_SugestaoSolicitacao_Extracao FOREIGN KEY (ResultadoExtracaoId)
                REFERENCES processamento.ResultadoExtracao (ResultadoExtracaoId),
            CONSTRAINT FK_SugestaoSolicitacao_Ementa FOREIGN KEY (EmentaMatrizId)
                REFERENCES academico.Ementa (EmentaId),

            CONSTRAINT UQ_SugestaoSolicitacao_Identidade UNIQUE (
                SolicitacaoId, ResultadoExtracaoId, EmentaMatrizId, VersaoMotor, PoliticaVersao
            ),
            CONSTRAINT CK_SugestaoSolicitacao_Indicacao CHECK (
                Indicacao IN ('APTO_A_DISPENSA', 'TALVEZ_APTO', 'NAO_APTO')
            ),
            CONSTRAINT CK_SugestaoSolicitacao_Cobertura CHECK (
                CoberturaDestino IS NULL OR CoberturaDestino BETWEEN 0 AND 1
            ),
            CONSTRAINT CK_SugestaoSolicitacao_EvidenciasJson CHECK (ISJSON(EvidenciasJson) = 1),
            CONSTRAINT CK_SugestaoSolicitacao_JustificativasJson CHECK (ISJSON(JustificativasJson) = 1),
            CONSTRAINT CK_SugestaoSolicitacao_Status CHECK (
                Status IN ('AGUARDANDO_VALIDACAO', 'VALIDADA')
            )
        );
    END;

    IF OBJECT_ID(N'equivalencia.ParecerSugestao', N'U') IS NULL
    BEGIN
        CREATE TABLE equivalencia.ParecerSugestao (
            ParecerSugestaoId BIGINT IDENTITY(1,1) NOT NULL,
            SugestaoSolicitacaoId BIGINT NOT NULL,
            CoordenadorUsuarioId BIGINT NOT NULL,
            Decisao VARCHAR(20) NOT NULL,
            Justificativa NVARCHAR(MAX) NOT NULL,
            EmitidoEm DATETIME2(3) NOT NULL
                CONSTRAINT DF_ParecerSugestao_EmitidoEm DEFAULT (SYSUTCDATETIME()),

            CONSTRAINT PK_ParecerSugestao PRIMARY KEY (ParecerSugestaoId),
            CONSTRAINT FK_ParecerSugestao_Sugestao FOREIGN KEY (SugestaoSolicitacaoId)
                REFERENCES equivalencia.SugestaoSolicitacao (SugestaoSolicitacaoId),
            CONSTRAINT FK_ParecerSugestao_Usuario FOREIGN KEY (CoordenadorUsuarioId)
                REFERENCES seguranca.Usuario (UsuarioId),
            CONSTRAINT CK_ParecerSugestao_Decisao CHECK (
                Decisao IN ('APROVADA', 'REJEITADA', 'INCONCLUSIVA')
            ),
            CONSTRAINT CK_ParecerSugestao_Justificativa CHECK (
                LEN(LTRIM(RTRIM(Justificativa))) > 0
            )
        );
    END;

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'equivalencia.SugestaoSolicitacao')
          AND name = N'IX_SugestaoSolicitacao_Solicitacao'
    )
        CREATE INDEX IX_SugestaoSolicitacao_Solicitacao
            ON equivalencia.SugestaoSolicitacao (SolicitacaoId, Status, CriadoEm DESC);

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE object_id = OBJECT_ID(N'equivalencia.ParecerSugestao')
          AND name = N'IX_ParecerSugestao_Sugestao'
    )
        CREATE INDEX IX_ParecerSugestao_Sugestao
            ON equivalencia.ParecerSugestao (SugestaoSolicitacaoId, EmitidoEm DESC);

    IF NOT EXISTS (SELECT 1 FROM governanca.VersaoSchema WHERE Versao = '1.10.0')
        INSERT INTO governanca.VersaoSchema (Versao, Descricao)
        VALUES ('1.10.0', N'Sugestões automáticas vinculadas a solicitações e pareceres de coordenadores.');

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;

