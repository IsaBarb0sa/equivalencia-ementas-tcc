SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(N'governanca.VersaoSchema', N'U') IS NULL
        THROW 50000, 'Selecione o banco do projeto.', 1;

    IF NOT EXISTS (
        SELECT 1
        FROM governanca.VersaoSchema
        WHERE Versao = '1.3.0'
    )
        THROW 50001, 'Aplique a migration 004 primeiro.', 1;

    IF EXISTS (
        SELECT 1
        FROM governanca.VersaoSchema
        WHERE Versao = '1.4.0'
    )
    BEGIN
        COMMIT;
        PRINT N'Migration 005 já aplicada.';
        RETURN;
    END;

    CREATE TABLE processamento.Solicitacao
    (
        SolicitacaoId BIGINT IDENTITY(1,1) NOT NULL,

        Protocolo UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT DF_Solicitacao_Protocolo DEFAULT (NEWID()),

        CursoDestinoId BIGINT NOT NULL,

        Status VARCHAR(30) NOT NULL
            CONSTRAINT DF_Solicitacao_Status DEFAULT ('RECEBIDA'),

        CriadoEm DATETIME2(3) NOT NULL
            CONSTRAINT DF_Solicitacao_CriadoEm DEFAULT (SYSUTCDATETIME()),

        AtualizadoEm DATETIME2(3) NOT NULL
            CONSTRAINT DF_Solicitacao_AtualizadoEm DEFAULT (SYSUTCDATETIME()),

        VersaoLinha ROWVERSION NOT NULL,

        CONSTRAINT PK_Solicitacao
            PRIMARY KEY CLUSTERED (SolicitacaoId),

        CONSTRAINT UQ_Solicitacao_Protocolo
            UNIQUE (Protocolo),

        CONSTRAINT FK_Solicitacao_CursoDestino
            FOREIGN KEY (CursoDestinoId)
            REFERENCES academico.Curso (CursoId),

        CONSTRAINT CK_Solicitacao_Status CHECK (
            Status IN (
                'RECEBIDA',
                'PROCESSANDO',
                'AGUARDANDO_REVISAO',
                'CONCLUIDA',
                'FALHA',
                'CANCELADA'
            )
        )
    );

    CREATE TABLE processamento.SolicitacaoDocumento
    (
        SolicitacaoId BIGINT NOT NULL,
        DocumentoFonteId BIGINT NOT NULL,

        NomeArquivoEnviado NVARCHAR(260) NOT NULL,

        VinculadoEm DATETIME2(3) NOT NULL
            CONSTRAINT DF_SolicitacaoDocumento_VinculadoEm
            DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_SolicitacaoDocumento
            PRIMARY KEY CLUSTERED (SolicitacaoId, DocumentoFonteId),

        CONSTRAINT FK_SolicitacaoDocumento_Solicitacao
            FOREIGN KEY (SolicitacaoId)
            REFERENCES processamento.Solicitacao (SolicitacaoId),

        CONSTRAINT FK_SolicitacaoDocumento_DocumentoFonte
            FOREIGN KEY (DocumentoFonteId)
            REFERENCES processamento.DocumentoFonte (DocumentoFonteId),

        CONSTRAINT CK_SolicitacaoDocumento_NomeArquivo CHECK (
            LEN(LTRIM(RTRIM(NomeArquivoEnviado))) > 0
        )
    );

    CREATE INDEX IX_Solicitacao_Curso_Status
        ON processamento.Solicitacao (
            CursoDestinoId,
            Status,
            CriadoEm DESC
        );

    CREATE INDEX IX_SolicitacaoDocumento_DocumentoFonte
        ON processamento.SolicitacaoDocumento (DocumentoFonteId);

    INSERT INTO governanca.VersaoSchema (Versao, Descricao)
    VALUES (
        '1.4.0',
        N'Solicitações de aproveitamento com protocolo, curso de destino e vínculos com documentos.'
    );

    COMMIT;

    PRINT N'Migration 005 aplicada com sucesso.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK;

    THROW;
END CATCH;