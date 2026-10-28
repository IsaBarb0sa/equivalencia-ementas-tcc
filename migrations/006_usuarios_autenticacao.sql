
/*
    Migration 006
    Versão do schema: 1.5.0

    Autenticação e controle de acesso:
    - Cadastro de usuários
    - Perfis de acesso
    - Permissões de coordenadores por curso
    - Vínculo entre solicitações e candidatos
*/

SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    -- Verifica se estamos no banco correto.
    IF OBJECT_ID(N'governanca.VersaoSchema', N'U') IS NULL
        THROW 50000, 'Selecione o banco do projeto.', 1;

    -- A migration 005 precisa estar aplicada.
    IF NOT EXISTS (
        SELECT 1
        FROM governanca.VersaoSchema
        WHERE Versao = '1.4.0'
    )
        THROW 50001, 'Aplique a migration 005 primeiro.', 1;

    -- Evita executar a mesma migration duas vezes.
    IF EXISTS (
        SELECT 1
        FROM governanca.VersaoSchema
        WHERE Versao = '1.5.0'
    )
    BEGIN
        COMMIT;
        PRINT N'Migration 006 já aplicada.';
        RETURN;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.schemas
        WHERE name = N'seguranca'
    )
        EXEC(N'CREATE SCHEMA seguranca AUTHORIZATION dbo;');


    CREATE TABLE seguranca.Usuario
    (
        UsuarioId BIGINT IDENTITY(1,1) NOT NULL,

        NomeCompleto NVARCHAR(200) NOT NULL,

        -- CPF sem pontuação (11 dígitos).
        -- Coordenadores podem ter CPF nulo.
        Cpf CHAR(11) NULL,

        Email NVARCHAR(254) NOT NULL,

        -- Padronização para buscas e unicidade.
        EmailNormalizado AS
            LOWER(LTRIM(RTRIM(Email))) PERSISTED,

        -- Armazena apenas o hash Argon2id.
        SenhaHash NVARCHAR(255) NOT NULL,

        Perfil VARCHAR(20) NOT NULL
            CONSTRAINT DF_Usuario_Perfil
            DEFAULT ('CANDIDATO'),

        Ativo BIT NOT NULL
            CONSTRAINT DF_Usuario_Ativo
            DEFAULT (1),

        EmailVerificado BIT NOT NULL
            CONSTRAINT DF_Usuario_EmailVerificado
            DEFAULT (0),

        CriadoEm DATETIME2(3) NOT NULL
            CONSTRAINT DF_Usuario_CriadoEm
            DEFAULT (SYSUTCDATETIME()),

        AtualizadoEm DATETIME2(3) NOT NULL
            CONSTRAINT DF_Usuario_AtualizadoEm
            DEFAULT (SYSUTCDATETIME()),

        UltimoAcessoEm DATETIME2(3) NULL,

        VersaoLinha ROWVERSION NOT NULL,

        CONSTRAINT PK_Usuario
            PRIMARY KEY CLUSTERED (UsuarioId),

        CONSTRAINT CK_Usuario_Nome CHECK (
            LEN(LTRIM(RTRIM(NomeCompleto))) > 0
        ),

        CONSTRAINT CK_Usuario_Cpf CHECK (
            Cpf IS NULL OR (
                LEN(Cpf) = 11
                AND Cpf NOT LIKE '%[^0-9]%'
            )
        ),

        CONSTRAINT CK_Usuario_Email CHECK (
            LEN(LTRIM(RTRIM(Email))) > 3
            AND Email LIKE '%_@_%._%'
            AND Email NOT LIKE '% %'
        ),

        CONSTRAINT CK_Usuario_Perfil CHECK (
            Perfil IN (
                'CANDIDATO',
                'COORDENADOR',
                'ADMIN'
            )
        ),

        CONSTRAINT CK_Usuario_CpfCandidato CHECK (
            Perfil <> 'CANDIDATO'
            OR Cpf IS NOT NULL
        )
    );

    -- Um e-mail só pode pertencer a uma conta.
    CREATE UNIQUE INDEX UX_Usuario_Email
        ON seguranca.Usuario (EmailNormalizado);

    -- CPF único quando informado.
    CREATE UNIQUE INDEX UX_Usuario_Cpf
        ON seguranca.Usuario (Cpf)
        WHERE Cpf IS NOT NULL;

    CREATE INDEX IX_Usuario_Perfil_Ativo
        ON seguranca.Usuario (Perfil, Ativo);


    CREATE TABLE seguranca.CoordenadorCurso
    (
        CoordenadorCursoId BIGINT IDENTITY(1,1) NOT NULL,

        UsuarioId BIGINT NOT NULL,

        CursoId BIGINT NOT NULL,

        Ativo BIT NOT NULL
            CONSTRAINT DF_CoordenadorCurso_Ativo
            DEFAULT (1),

        VinculadoEm DATETIME2(3) NOT NULL
            CONSTRAINT DF_CoordenadorCurso_VinculadoEm
            DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_CoordenadorCurso
            PRIMARY KEY CLUSTERED (CoordenadorCursoId),

        CONSTRAINT FK_CoordenadorCurso_Usuario
            FOREIGN KEY (UsuarioId)
            REFERENCES seguranca.Usuario (UsuarioId),

        CONSTRAINT FK_CoordenadorCurso_Curso
            FOREIGN KEY (CursoId)
            REFERENCES academico.Curso (CursoId),

        CONSTRAINT UQ_CoordenadorCurso
            UNIQUE (UsuarioId, CursoId)
    );

    CREATE INDEX IX_CoordenadorCurso_Curso_Ativo
        ON seguranca.CoordenadorCurso (CursoId, Ativo);


    ALTER TABLE processamento.Solicitacao
    ADD CandidatoUsuarioId BIGINT NULL;

    ALTER TABLE processamento.Solicitacao
    ADD CONSTRAINT FK_Solicitacao_CandidatoUsuario
        FOREIGN KEY (CandidatoUsuarioId)
        REFERENCES seguranca.Usuario (UsuarioId);

    EXEC(N'
        CREATE INDEX IX_Solicitacao_Candidato_CriadoEm
        ON processamento.Solicitacao (
            CandidatoUsuarioId,
            CriadoEm DESC
        )
        WHERE CandidatoUsuarioId IS NOT NULL;
    ');


    INSERT INTO governanca.VersaoSchema (
        Versao,
        Descricao
    )
    VALUES (
        '1.5.0',
        N'Cadastro de usuários, perfis de acesso, permissões de coordenadores e vínculo de candidatos às solicitações.'
    );

    COMMIT;

    PRINT N'Migration 006 aplicada com sucesso.';

END TRY
BEGIN CATCH

    IF @@TRANCOUNT > 0
        ROLLBACK;

    THROW;

END CATCH;
