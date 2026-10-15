SET XACT_ABORT ON;
BEGIN TRY
    BEGIN TRANSACTION;
    IF OBJECT_ID(N'governanca.VersaoSchema', N'U') IS NULL
        THROW 50000, 'Selecione o banco do projeto.', 1;
    IF NOT EXISTS (SELECT 1 FROM governanca.VersaoSchema WHERE Versao = '1.2.0')
        THROW 50001, 'Aplique a migration 003 primeiro.', 1;
    IF EXISTS (SELECT 1 FROM governanca.VersaoSchema WHERE Versao = '1.3.0')
    BEGIN
        COMMIT;
        RETURN;
    END;
    ALTER TABLE academico.Ementa DROP CONSTRAINT CK_Ementa_CargasComponentes;
    ALTER TABLE academico.Ementa DROP CONSTRAINT CK_Ementa_UnidadeDesconhecida;
    ALTER TABLE academico.Ementa DROP CONSTRAINT CK_Ementa_CargaDeclarada;
    ALTER TABLE academico.Ementa DROP CONSTRAINT CK_Ementa_CargaNormalizada;
    ALTER TABLE academico.Ementa ALTER COLUMN CargaHorariaDeclarada DECIMAL(8,2) NULL;
    ALTER TABLE academico.Ementa ALTER COLUMN CargaHorariaNormalizadaMin DECIMAL(12,2) NULL;
    ALTER TABLE academico.Ementa ADD
        CargaHorariaTotalHoraAula DECIMAL(8,2) NULL,
        CargaHorariaTotalHoraRelogio DECIMAL(8,2) NULL,
        CargaHorariaTeoricaSemanal DECIMAL(8,2) NULL,
        CargaHorariaPraticaSemanal DECIMAL(8,2) NULL,
        CargaHorariaTotalSemanal DECIMAL(8,2) NULL,
        UnidadeCargaTeorica VARCHAR(10) NOT NULL CONSTRAINT DF_Ementa_UnidadeCargaTeorica DEFAULT ('NAO_INFO') WITH VALUES,
        UnidadeCargaPratica VARCHAR(10) NOT NULL CONSTRAINT DF_Ementa_UnidadeCargaPratica DEFAULT ('NAO_INFO') WITH VALUES,
        UnidadeCargaTeoricaSemanal VARCHAR(10) NOT NULL CONSTRAINT DF_Ementa_UnidadeCargaTeoricaSemanal DEFAULT ('NAO_INFO') WITH VALUES,
        UnidadeCargaPraticaSemanal VARCHAR(10) NOT NULL CONSTRAINT DF_Ementa_UnidadeCargaPraticaSemanal DEFAULT ('NAO_INFO') WITH VALUES,
        UnidadeCargaTotalSemanal VARCHAR(10) NOT NULL CONSTRAINT DF_Ementa_UnidadeCargaTotalSemanal DEFAULT ('NAO_INFO') WITH VALUES;
    EXEC(N'ALTER TABLE academico.Ementa WITH CHECK ADD CONSTRAINT CK_Ementa_CargaV130 CHECK (
(CargaHorariaDeclarada IS NULL OR CargaHorariaDeclarada > 0) AND
(CargaHorariaNormalizadaMin IS NULL OR CargaHorariaNormalizadaMin > 0) AND
(CargaHorariaTotalHoraAula IS NULL OR CargaHorariaTotalHoraAula > 0) AND
(CargaHorariaTotalHoraRelogio IS NULL OR CargaHorariaTotalHoraRelogio > 0) AND
(CargaHorariaTeoricaSemanal IS NULL OR CargaHorariaTeoricaSemanal >= 0) AND
(CargaHorariaPraticaSemanal IS NULL OR CargaHorariaPraticaSemanal >= 0) AND
(CargaHorariaTotalSemanal IS NULL OR CargaHorariaTotalSemanal >= 0) AND
UnidadeCargaTeorica IN (''HORA'',''HORA_AULA'',''CREDITO'',''NAO_INFO'') AND
UnidadeCargaPratica IN (''HORA'',''HORA_AULA'',''CREDITO'',''NAO_INFO'') AND
UnidadeCargaTeoricaSemanal IN (''HORA'',''HORA_AULA'',''CREDITO'',''NAO_INFO'') AND
UnidadeCargaPraticaSemanal IN (''HORA'',''HORA_AULA'',''CREDITO'',''NAO_INFO'') AND
UnidadeCargaTotalSemanal IN (''HORA'',''HORA_AULA'',''CREDITO'',''NAO_INFO'') AND
(CargaHorariaTeorica IS NULL OR CargaHorariaTeorica >= 0) AND
(CargaHorariaPratica IS NULL OR CargaHorariaPratica >= 0) AND
(CargaHorariaDeclarada IS NULL OR UnidadeCargaHoraria = ''NAO_INFO'' OR (CASE WHEN UnidadeCargaTeorica = UnidadeCargaHoraria THEN COALESCE(CargaHorariaTeorica,0) ELSE 0 END + CASE WHEN UnidadeCargaPratica = UnidadeCargaHoraria THEN COALESCE(CargaHorariaPratica,0) ELSE 0 END) <= CargaHorariaDeclarada) AND
(CargaHorariaTotalHoraAula IS NULL OR ''HORA_AULA'' = ''NAO_INFO'' OR (CASE WHEN UnidadeCargaTeorica = ''HORA_AULA'' THEN COALESCE(CargaHorariaTeorica,0) ELSE 0 END + CASE WHEN UnidadeCargaPratica = ''HORA_AULA'' THEN COALESCE(CargaHorariaPratica,0) ELSE 0 END) <= CargaHorariaTotalHoraAula) AND
(CargaHorariaTotalHoraRelogio IS NULL OR ''HORA'' = ''NAO_INFO'' OR (CASE WHEN UnidadeCargaTeorica = ''HORA'' THEN COALESCE(CargaHorariaTeorica,0) ELSE 0 END + CASE WHEN UnidadeCargaPratica = ''HORA'' THEN COALESCE(CargaHorariaPratica,0) ELSE 0 END) <= CargaHorariaTotalHoraRelogio) AND
(CargaHorariaTotalSemanal IS NULL OR UnidadeCargaTotalSemanal = ''NAO_INFO'' OR (CASE WHEN UnidadeCargaTeoricaSemanal = UnidadeCargaTotalSemanal THEN COALESCE(CargaHorariaTeoricaSemanal,0) ELSE 0 END + CASE WHEN UnidadeCargaPraticaSemanal = UnidadeCargaTotalSemanal THEN COALESCE(CargaHorariaPraticaSemanal,0) ELSE 0 END) <= CargaHorariaTotalSemanal));');
    EXEC(N'ALTER TABLE academico.Ementa WITH CHECK ADD CONSTRAINT CK_Ementa_PublicacaoCarga
        CHECK (Status <> ''PUBLICADA'' OR (UnidadeCargaHoraria <> ''NAO_INFO'' AND
            (CargaHorariaDeclarada IS NOT NULL OR CargaHorariaTotalHoraAula IS NOT NULL OR CargaHorariaTotalHoraRelogio IS NOT NULL)));');
    INSERT INTO governanca.VersaoSchema (Versao, Descricao)
    VALUES ('1.3.0', N'Cargas parciais, totais explícitos, unidades dos componentes e cargas semanais.');
    COMMIT;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    THROW;
END CATCH;
