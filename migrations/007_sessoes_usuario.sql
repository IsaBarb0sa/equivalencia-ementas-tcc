
/*
    Migration 007
    Versão: 1.6.0
    Sessões de autenticação dos usuários.
*/

SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(N'governanca.VersaoSchema', N'U') IS NULL
        THROW 50000, 'Selecione o banco do projeto.', 1;

    IF NOT EXISTS (
        SELECT 1
        FROM governanca.VersaoSchema
        WHERE Versao = '1.5.0'
    )
        THROW 50001, 'Aplique a migration 006 primeiro.', 1;

    IF EXISTS (
        SELECT 1
        FROM governanca.VersaoSchema
        WHERE Versao = '1.6.0'
    )
    BEGIN
        COMMIT;
        PRINT N'Migration 007 já aplicada.';
        RETURN;
    END;

    CREATE TABLE seguranca.SessaoUsuario
    (
        SessaoUsuarioId BIGINT IDENTITY(1,1) NOT NULL,

        UsuarioId BIGINT NOT NULL,

        TokenHash CHAR(64) NOT NULL,

        CriadoEm DATETIME2(3) NOT NULL
            CONSTRAINT DF_SessaoUsuario_CriadoEm
            DEFAULT (SYSUTCDATETIME()),

        ExpiraEm DATETIME2(3) NOT NULL,

        RevogadoEm DATETIME2(3) NULL,

        UltimoAcessoEm DATETIME2(3) NULL,

        CONSTRAINT PK_SessaoUsuario
            PRIMARY KEY CLUSTERED (SessaoUsuarioId),

        CONSTRAINT FK_SessaoUsuario_Usuario
            FOREIGN KEY (UsuarioId)
            REFERENCES seguranca.Usuario (UsuarioId),

        CONSTRAINT UQ_SessaoUsuario_TokenHash
            UNIQUE (TokenHash),

        CONSTRAINT CK_SessaoUsuario_TokenHash CHECK (
            LEN(TokenHash) = 64
            AND TokenHash NOT LIKE '%[^0-9a-f]%'
        ),

        CONSTRAINT CK_SessaoUsuario_Expiracao CHECK (
            ExpiraEm > CriadoEm
        ),

        CONSTRAINT CK_SessaoUsuario_Revogacao CHECK (
            RevogadoEm IS NULL
            OR RevogadoEm >= CriadoEm
        )
    );

    CREATE INDEX IX_SessaoUsuario_Usuario_ExpiraEm
        ON seguranca.SessaoUsuario (
            UsuarioId,
            ExpiraEm DESC
        );

    CREATE INDEX IX_SessaoUsuario_SessoesAtivas
        ON seguranca.SessaoUsuario (
            ExpiraEm
        )
        WHERE RevogadoEm IS NULL;

    INSERT INTO governanca.VersaoSchema (
        Versao,
        Descricao
    )
    VALUES (
        '1.6.0',
        N'Sessões de autenticação com hash de token, expiração e revogação.'
    );

    COMMIT;

    PRINT N'Migration 007 aplicada com sucesso.';

END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK;

    THROW;
END CATCH;
