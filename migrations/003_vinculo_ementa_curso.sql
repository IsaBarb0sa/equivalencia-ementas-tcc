SET XACT_ABORT ON;
BEGIN TRY
 BEGIN TRANSACTION;
 IF OBJECT_ID(N'governanca.VersaoSchema',N'U') IS NULL
    THROW 50001, 'Selecione o banco do projeto.', 1;
 IF NOT EXISTS(SELECT 1 FROM governanca.VersaoSchema WHERE Versao='1.1.0')
    THROW 50002, 'Aplique primeiro a migration 002.', 1;
 IF EXISTS(SELECT 1 FROM governanca.VersaoSchema WHERE Versao='1.2.0')
 BEGIN
    COMMIT;
    PRINT N'Migration 003 já aplicada.';
    RETURN;
 END;
 CREATE TABLE academico.EmentaCurso (
    EmentaId BIGINT NOT NULL,
    CursoId BIGINT NOT NULL,
    CONSTRAINT PK_EmentaCurso PRIMARY KEY(EmentaId,CursoId),
    CONSTRAINT FK_EmentaCurso_Ementa FOREIGN KEY(EmentaId) REFERENCES academico.Ementa(EmentaId),
    CONSTRAINT FK_EmentaCurso_Curso FOREIGN KEY(CursoId) REFERENCES academico.Curso(CursoId)
 );
 INSERT INTO governanca.VersaoSchema(Versao,Descricao)
 VALUES('1.2.0',N'Vínculo explícito de ementa com curso sem exigir matriz curricular.');
 COMMIT;
 PRINT N'Migration 003 aplicada.';
END TRY
BEGIN CATCH
 IF @@TRANCOUNT>0 ROLLBACK;
 THROW;
END CATCH;
