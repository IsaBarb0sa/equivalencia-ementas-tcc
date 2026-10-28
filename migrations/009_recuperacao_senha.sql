
-- Migration 009
-- Recuperação de senha
-- Usuário já possui Perfil (CANDIDATO, COORDENADOR, ADMIN).

IF OBJECT_ID(N'seguranca.Usuario', N'U') IS NULL
BEGIN
    THROW 50001,
        'A tabela seguranca.Usuario não existe.',
        1;
END;
GO

IF OBJECT_ID(N'seguranca.RecuperacaoSenha', N'U') IS NULL
BEGIN
    CREATE TABLE seguranca.RecuperacaoSenha
    (
        RecuperacaoSenhaId BIGINT
            IDENTITY(1,1) NOT NULL,

        UsuarioId BIGINT NOT NULL,

        TokenHash CHAR(64) NOT NULL,

        CriadoEm DATETIME2(3) NOT NULL
            CONSTRAINT DF_RecuperacaoSenha_CriadoEm
            DEFAULT (SYSUTCDATETIME()),

        ExpiraEm DATETIME2(3) NOT NULL,

        UtilizadoEm DATETIME2(3) NULL,

        CONSTRAINT PK_RecuperacaoSenha
            PRIMARY KEY (RecuperacaoSenhaId),

        CONSTRAINT FK_RecuperacaoSenha_Usuario
            FOREIGN KEY (UsuarioId)
            REFERENCES seguranca.Usuario(UsuarioId),

        CONSTRAINT UQ_RecuperacaoSenha_Token
            UNIQUE (TokenHash),

        CONSTRAINT CK_RecuperacaoSenha_Expiracao
            CHECK (ExpiraEm > CriadoEm)
    );
END;
GO

IF OBJECT_ID(N'seguranca.RecuperacaoSenha', N'U') IS NOT NULL
   AND NOT EXISTS (
       SELECT 1
       FROM sys.indexes
       WHERE name = N'IX_RecuperacaoSenha_Usuario'
         AND object_id =
             OBJECT_ID(N'seguranca.RecuperacaoSenha')
   )
BEGIN
    CREATE INDEX IX_RecuperacaoSenha_Usuario
    ON seguranca.RecuperacaoSenha (
        UsuarioId,
        ExpiraEm
    );
END;
GO
