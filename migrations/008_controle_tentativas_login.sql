
-- Controle persistente de tentativas de autenticação.
-- As chaves representam identificadores ou IPs
-- transformados em hash SHA-256.

IF OBJECT_ID(
    N'seguranca.ControleTentativaLogin',
    N'U'
) IS NULL
BEGIN
    CREATE TABLE seguranca.ControleTentativaLogin
    (
        ChaveHash CHAR(64) NOT NULL,

        QuantidadeFalhas INT NOT NULL
            CONSTRAINT DF_ControleTentativaLogin_Falhas
            DEFAULT (0),

        JanelaInicio DATETIME2(3) NOT NULL
            CONSTRAINT DF_ControleTentativaLogin_Janela
            DEFAULT (SYSUTCDATETIME()),

        BloqueadoAte DATETIME2(3) NULL,

        AtualizadoEm DATETIME2(3) NOT NULL
            CONSTRAINT DF_ControleTentativaLogin_Atualizado
            DEFAULT (SYSUTCDATETIME()),

        CONSTRAINT PK_ControleTentativaLogin
            PRIMARY KEY (ChaveHash),

        CONSTRAINT CK_ControleTentativaLogin_Falhas
            CHECK (QuantidadeFalhas >= 0)
    );
END;
GO
