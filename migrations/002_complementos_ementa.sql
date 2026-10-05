/* Versão 1.1.0. Alterações e registro da versão são atômicos. */
SET XACT_ABORT ON;
BEGIN TRY
    BEGIN TRANSACTION;
    IF OBJECT_ID(N'governanca.VersaoSchema', N'U') IS NULL
        THROW 50001, 'Selecione o banco do projeto com a migration 001 aplicada.', 1;
    IF EXISTS (SELECT 1 FROM governanca.VersaoSchema WHERE Versao = '1.1.0')
    BEGIN
        COMMIT;
        PRINT N'Versão 1.1.0 já aplicada.';
        RETURN;
    END;
    IF OBJECT_ID(N'academico.Ementa', N'U') IS NULL
        THROW 50002, 'Tabela academico.Ementa ausente.', 1;

    ALTER TABLE academico.Ementa ADD
        CargaHorariaTeorica DECIMAL(8,2) NULL,
        CargaHorariaPratica DECIMAL(8,2) NULL,
        CompetenciasHabilidades NVARCHAR(MAX) NULL;

    /* SQL dinâmico evita resolução das novas colunas antes do ALTER. */
    EXEC(N'ALTER TABLE academico.Ementa WITH CHECK ADD CONSTRAINT CK_Ementa_CargasComponentes CHECK (
        (CargaHorariaTeorica IS NULL OR (CargaHorariaTeorica >= 0 AND CargaHorariaTeorica <= CargaHorariaDeclarada)) AND
        (CargaHorariaPratica IS NULL OR (CargaHorariaPratica >= 0 AND CargaHorariaPratica <= CargaHorariaDeclarada)) AND
        (CargaHorariaTeorica IS NULL OR CargaHorariaPratica IS NULL OR
         CargaHorariaTeorica + CargaHorariaPratica <= CargaHorariaDeclarada));');

    ALTER TABLE academico.Ementa DROP CONSTRAINT CK_Ementa_UnidadeCarga;
    ALTER TABLE academico.Ementa WITH CHECK ADD CONSTRAINT CK_Ementa_UnidadeCarga
        CHECK (UnidadeCargaHoraria IN ('HORA', 'HORA_AULA', 'CREDITO', 'NAO_INFO'));
    ALTER TABLE academico.Ementa WITH CHECK ADD CONSTRAINT CK_Ementa_UnidadeDesconhecida
        CHECK (UnidadeCargaHoraria <> 'NAO_INFO' OR
          (CargaHorariaNormalizadaMin IS NULL AND DuracaoHoraAulaMinutos IS NULL AND Status <> 'PUBLICADA'));

    ALTER TABLE academico.ObjetivoEmenta DROP CONSTRAINT CK_ObjetivoEmenta_Tipo;
    ALTER TABLE academico.ObjetivoEmenta WITH CHECK ADD CONSTRAINT CK_ObjetivoEmenta_Tipo
        CHECK (Tipo IN ('GERAL', 'ESPECIFICO', 'NAO_CLASSIF'));

    CREATE TABLE processamento.ResultadoExtracao (
        ResultadoExtracaoId BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        DocumentoFonteId BIGINT NOT NULL,
        EmentaId BIGINT NULL,
        NumeroEmenta INT NOT NULL,
        VersaoExtrator NVARCHAR(50) NOT NULL,
        DadosExtraidosJson NVARCHAR(MAX) NOT NULL,
        AuditoriaJson NVARCHAR(MAX) NOT NULL,
        DadosRevisadosJson NVARCHAR(MAX) NULL,
        Status VARCHAR(20) NOT NULL CONSTRAINT DF_ResultadoExtracao_Status DEFAULT ('PENDENTE'),
        RevisadoPor NVARCHAR(200) NULL,
        RevisadoEm DATETIME2(3) NULL,
        CriadoEm DATETIME2(3) NOT NULL CONSTRAINT DF_ResultadoExtracao_CriadoEm DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_ResultadoExtracao_Documento FOREIGN KEY (DocumentoFonteId)
            REFERENCES processamento.DocumentoFonte (DocumentoFonteId),
        CONSTRAINT FK_ResultadoExtracao_Ementa FOREIGN KEY (EmentaId)
            REFERENCES academico.Ementa (EmentaId),
        CONSTRAINT UQ_ResultadoExtracao_Identidade UNIQUE (DocumentoFonteId, VersaoExtrator, NumeroEmenta),
        CONSTRAINT CK_ResultadoExtracao_Numero CHECK (NumeroEmenta > 0),
        CONSTRAINT CK_ResultadoExtracao_Dados CHECK (ISJSON(DadosExtraidosJson)=1),
        CONSTRAINT CK_ResultadoExtracao_Auditoria CHECK (ISJSON(AuditoriaJson)=1),
        CONSTRAINT CK_ResultadoExtracao_Revisados CHECK (DadosRevisadosJson IS NULL OR ISJSON(DadosRevisadosJson)=1),
        CONSTRAINT CK_ResultadoExtracao_Status CHECK (Status IN ('PENDENTE','REVISADO','IMPORTADO','REJEITADO')),
        CONSTRAINT CK_ResultadoExtracao_Revisao CHECK (Status NOT IN ('REVISADO','IMPORTADO') OR
            (RevisadoPor IS NOT NULL AND LEN(LTRIM(RTRIM(RevisadoPor)))>0 AND RevisadoEm IS NOT NULL AND DadosRevisadosJson IS NOT NULL)),
        CONSTRAINT CK_ResultadoExtracao_Importacao CHECK
            ((Status='IMPORTADO' AND EmentaId IS NOT NULL) OR (Status<>'IMPORTADO' AND EmentaId IS NULL))
    );
    INSERT INTO governanca.VersaoSchema (Versao, Descricao)
    VALUES ('1.1.0', N'Cargas componentes, competências, objetivos não classificados e resultados de extração para revisão.');
    COMMIT;
    PRINT N'Migration 002 aplicada. Versão 1.1.0.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    THROW;
END CATCH;
