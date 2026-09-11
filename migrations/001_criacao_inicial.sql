
USE master;
GO

IF DB_ID(N'EquivalenciaEmentas') IS NULL
BEGIN
    CREATE DATABASE TCC_Ementas;
END;
GO

ALTER DATABASE TCC_Ementas SET COMPATIBILITY_LEVEL = 160;
GO

USE TCC_Ementas;
GO

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET XACT_ABORT ON;
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'academico')
    EXEC(N'CREATE SCHEMA academico AUTHORIZATION dbo;');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'processamento')
    EXEC(N'CREATE SCHEMA processamento AUTHORIZATION dbo;');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'governanca')
    EXEC(N'CREATE SCHEMA governanca AUTHORIZATION dbo;');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'equivalencia')
    EXEC(N'CREATE SCHEMA equivalencia AUTHORIZATION dbo;');
GO

/* ACADEMICO */

CREATE TABLE academico.Instituicao
(
    InstituicaoId       BIGINT IDENTITY(1,1) NOT NULL,
    Codigo              NVARCHAR(30) NULL,
    Nome                NVARCHAR(200) NOT NULL,
    Sigla               NVARCHAR(30) NULL,
    Cnpj                CHAR(14) NULL,
    Cidade              NVARCHAR(100) NULL,
    Uf                  CHAR(2) NULL,
    Ativa               BIT NOT NULL CONSTRAINT DF_Instituicao_Ativa DEFAULT (1),
    CriadoEm            DATETIME2(3) NOT NULL CONSTRAINT DF_Instituicao_CriadoEm DEFAULT (SYSUTCDATETIME()),
    AtualizadoEm        DATETIME2(3) NOT NULL CONSTRAINT DF_Instituicao_AtualizadoEm DEFAULT (SYSUTCDATETIME()),
    VersaoLinha         ROWVERSION NOT NULL,

    CONSTRAINT PK_Instituicao PRIMARY KEY CLUSTERED (InstituicaoId),
    CONSTRAINT CK_Instituicao_Cnpj CHECK (Cnpj IS NULL OR Cnpj NOT LIKE '%[^0-9]%'),
    CONSTRAINT CK_Instituicao_Uf CHECK (Uf IS NULL OR LEN(Uf) = 2)
);
GO

CREATE UNIQUE INDEX UX_Instituicao_Codigo
    ON academico.Instituicao (Codigo)
    WHERE Codigo IS NOT NULL;
GO

CREATE UNIQUE INDEX UX_Instituicao_Cnpj
    ON academico.Instituicao (Cnpj)
    WHERE Cnpj IS NOT NULL;
GO

CREATE TABLE academico.Curso
(
    CursoId             BIGINT IDENTITY(1,1) NOT NULL,
    InstituicaoId       BIGINT NOT NULL,
    Codigo              NVARCHAR(30) NOT NULL,
    Nome                NVARCHAR(200) NOT NULL,
    Nivel               VARCHAR(20) NOT NULL CONSTRAINT DF_Curso_Nivel DEFAULT ('GRADUACAO'),
    Modalidade          VARCHAR(20) NOT NULL CONSTRAINT DF_Curso_Modalidade DEFAULT ('PRESENCIAL'),
    Ativo               BIT NOT NULL CONSTRAINT DF_Curso_Ativo DEFAULT (1),
    CriadoEm            DATETIME2(3) NOT NULL CONSTRAINT DF_Curso_CriadoEm DEFAULT (SYSUTCDATETIME()),
    AtualizadoEm        DATETIME2(3) NOT NULL CONSTRAINT DF_Curso_AtualizadoEm DEFAULT (SYSUTCDATETIME()),
    VersaoLinha         ROWVERSION NOT NULL,

    CONSTRAINT PK_Curso PRIMARY KEY CLUSTERED (CursoId),
    CONSTRAINT FK_Curso_Instituicao FOREIGN KEY (InstituicaoId)
        REFERENCES academico.Instituicao (InstituicaoId),
    CONSTRAINT UQ_Curso_Instituicao_Codigo UNIQUE (InstituicaoId, Codigo),
    CONSTRAINT CK_Curso_Nivel CHECK (Nivel IN ('GRADUACAO', 'POS_GRADUACAO', 'TECNICO', 'OUTRO')),
    CONSTRAINT CK_Curso_Modalidade CHECK (Modalidade IN ('PRESENCIAL', 'EAD', 'HIBRIDO', 'OUTRO'))
);
GO

CREATE INDEX IX_Curso_Instituicao_Nome
    ON academico.Curso (InstituicaoId, Nome);
GO

CREATE TABLE academico.MatrizCurricular
(
    MatrizCurricularId  BIGINT IDENTITY(1,1) NOT NULL,
    CursoId             BIGINT NOT NULL,
    Codigo              NVARCHAR(50) NOT NULL,
    Nome                NVARCHAR(200) NULL,
    AnoInicioVigencia   SMALLINT NULL,
    SemestreInicio      TINYINT NULL,
    AnoFimVigencia      SMALLINT NULL,
    SemestreFim         TINYINT NULL,
    Status              VARCHAR(20) NOT NULL CONSTRAINT DF_MatrizCurricular_Status DEFAULT ('RASCUNHO'),
    CriadoEm            DATETIME2(3) NOT NULL CONSTRAINT DF_MatrizCurricular_CriadoEm DEFAULT (SYSUTCDATETIME()),
    AtualizadoEm        DATETIME2(3) NOT NULL CONSTRAINT DF_MatrizCurricular_AtualizadoEm DEFAULT (SYSUTCDATETIME()),
    VersaoLinha         ROWVERSION NOT NULL,

    CONSTRAINT PK_MatrizCurricular PRIMARY KEY CLUSTERED (MatrizCurricularId),
    CONSTRAINT FK_MatrizCurricular_Curso FOREIGN KEY (CursoId)
        REFERENCES academico.Curso (CursoId),
    CONSTRAINT UQ_MatrizCurricular_Curso_Codigo UNIQUE (CursoId, Codigo),
    CONSTRAINT CK_MatrizCurricular_SemestreInicio CHECK (SemestreInicio IS NULL OR SemestreInicio IN (1, 2)),
    CONSTRAINT CK_MatrizCurricular_SemestreFim CHECK (SemestreFim IS NULL OR SemestreFim IN (1, 2)),
    CONSTRAINT CK_MatrizCurricular_Status CHECK (Status IN ('RASCUNHO', 'ATIVA', 'INATIVA', 'ARQUIVADA'))
);
GO

CREATE TABLE academico.Disciplina
(
    DisciplinaId        BIGINT IDENTITY(1,1) NOT NULL,
    InstituicaoId       BIGINT NOT NULL,
    Codigo              NVARCHAR(50) NOT NULL,
    Nome                NVARCHAR(200) NOT NULL,
    NomeNormalizado     NVARCHAR(200) NULL,
    AreaConhecimento    NVARCHAR(150) NULL,
    Ativa               BIT NOT NULL CONSTRAINT DF_Disciplina_Ativa DEFAULT (1),
    CriadoEm            DATETIME2(3) NOT NULL CONSTRAINT DF_Disciplina_CriadoEm DEFAULT (SYSUTCDATETIME()),
    AtualizadoEm        DATETIME2(3) NOT NULL CONSTRAINT DF_Disciplina_AtualizadoEm DEFAULT (SYSUTCDATETIME()),
    VersaoLinha         ROWVERSION NOT NULL,

    CONSTRAINT PK_Disciplina PRIMARY KEY CLUSTERED (DisciplinaId),
    CONSTRAINT FK_Disciplina_Instituicao FOREIGN KEY (InstituicaoId)
        REFERENCES academico.Instituicao (InstituicaoId),
    CONSTRAINT UQ_Disciplina_Instituicao_Codigo UNIQUE (InstituicaoId, Codigo)
);
GO

CREATE INDEX IX_Disciplina_Instituicao_Nome
    ON academico.Disciplina (InstituicaoId, Nome);
GO

CREATE TABLE academico.MatrizDisciplina
(
    MatrizDisciplinaId  BIGINT IDENTITY(1,1) NOT NULL,
    MatrizCurricularId  BIGINT NOT NULL,
    DisciplinaId        BIGINT NOT NULL,
    PeriodoSugerido     TINYINT NULL,
    Natureza            VARCHAR(20) NOT NULL CONSTRAINT DF_MatrizDisciplina_Natureza DEFAULT ('OBRIGATORIA'),
    Creditos            DECIMAL(6,2) NULL,
    Ativa               BIT NOT NULL CONSTRAINT DF_MatrizDisciplina_Ativa DEFAULT (1),
    CriadoEm            DATETIME2(3) NOT NULL CONSTRAINT DF_MatrizDisciplina_CriadoEm DEFAULT (SYSUTCDATETIME()),
    VersaoLinha         ROWVERSION NOT NULL,

    CONSTRAINT PK_MatrizDisciplina PRIMARY KEY CLUSTERED (MatrizDisciplinaId),
    CONSTRAINT FK_MatrizDisciplina_Matriz FOREIGN KEY (MatrizCurricularId)
        REFERENCES academico.MatrizCurricular (MatrizCurricularId),
    CONSTRAINT FK_MatrizDisciplina_Disciplina FOREIGN KEY (DisciplinaId)
        REFERENCES academico.Disciplina (DisciplinaId),
    CONSTRAINT UQ_MatrizDisciplina_Matriz_Disciplina UNIQUE (MatrizCurricularId, DisciplinaId),
    CONSTRAINT UQ_MatrizDisciplina_Id_Disciplina UNIQUE (MatrizDisciplinaId, DisciplinaId),
    CONSTRAINT CK_MatrizDisciplina_Periodo CHECK (PeriodoSugerido IS NULL OR PeriodoSugerido BETWEEN 1 AND 20),
    CONSTRAINT CK_MatrizDisciplina_Natureza CHECK (Natureza IN ('OBRIGATORIA', 'OPTATIVA', 'ELETIVA', 'OUTRA')),
    CONSTRAINT CK_MatrizDisciplina_Creditos CHECK (Creditos IS NULL OR Creditos >= 0)
);
GO

/* PROCESSAMENTO: DOCUMENTO ANTES DA EMENTA PARA PERMITIR UPLOAD */

CREATE TABLE processamento.DocumentoFonte
(
    DocumentoFonteId    BIGINT IDENTITY(1,1) NOT NULL,
    NomeArquivo         NVARCHAR(260) NOT NULL,
    UriArmazenamento    NVARCHAR(1000) NOT NULL,
    MimeType            NVARCHAR(100) NOT NULL CONSTRAINT DF_DocumentoFonte_MimeType DEFAULT (N'application/pdf'),
    HashSha256          CHAR(64) NOT NULL,
    TamanhoBytes        BIGINT NOT NULL,
    QuantidadePaginas   INT NULL,
    PossuiTextoNativo   BIT NULL,
    Status              VARCHAR(20) NOT NULL CONSTRAINT DF_DocumentoFonte_Status DEFAULT ('RECEBIDO'),
    RecebidoEm          DATETIME2(3) NOT NULL CONSTRAINT DF_DocumentoFonte_RecebidoEm DEFAULT (SYSUTCDATETIME()),
    VersaoLinha         ROWVERSION NOT NULL,

    CONSTRAINT PK_DocumentoFonte PRIMARY KEY CLUSTERED (DocumentoFonteId),
    CONSTRAINT UQ_DocumentoFonte_Hash UNIQUE (HashSha256),
    CONSTRAINT CK_DocumentoFonte_Hash CHECK
        (LEN(HashSha256) = 64 AND HashSha256 NOT LIKE '%[^0-9A-Fa-f]%'),
    CONSTRAINT CK_DocumentoFonte_Tamanho CHECK (TamanhoBytes > 0),
    CONSTRAINT CK_DocumentoFonte_Paginas CHECK (QuantidadePaginas IS NULL OR QuantidadePaginas > 0),
    CONSTRAINT CK_DocumentoFonte_Status CHECK
        (Status IN ('RECEBIDO', 'PROCESSANDO', 'PROCESSADO', 'FALHA', 'ARQUIVADO'))
);
GO

CREATE TABLE academico.Ementa
(
    EmentaId                    BIGINT IDENTITY(1,1) NOT NULL,
    DisciplinaId                BIGINT NOT NULL,
    MatrizDisciplinaId          BIGINT NULL,
    DocumentoFonteId            BIGINT NULL,
    Versao                      NVARCHAR(30) NOT NULL,
    Idioma                      VARCHAR(10) NOT NULL CONSTRAINT DF_Ementa_Idioma DEFAULT ('pt-BR'),
    AnoVigencia                 SMALLINT NULL,
    SemestreVigencia            TINYINT NULL,
    Resumo                      NVARCHAR(MAX) NULL,
    CargaHorariaDeclarada       DECIMAL(8,2) NOT NULL,
    UnidadeCargaHoraria         VARCHAR(10) NOT NULL CONSTRAINT DF_Ementa_UnidadeCarga DEFAULT ('HORA'),
    DuracaoHoraAulaMinutos      SMALLINT NULL,
    CargaHorariaNormalizadaMin  INT NULL,
    Status                      VARCHAR(20) NOT NULL CONSTRAINT DF_Ementa_Status DEFAULT ('RASCUNHO'),
    ConfiancaParsing            DECIMAL(6,5) NULL,
    PublicadaEm                 DATETIME2(3) NULL,
    CriadoEm                    DATETIME2(3) NOT NULL CONSTRAINT DF_Ementa_CriadoEm DEFAULT (SYSUTCDATETIME()),
    AtualizadoEm                DATETIME2(3) NOT NULL CONSTRAINT DF_Ementa_AtualizadoEm DEFAULT (SYSUTCDATETIME()),
    VersaoLinha                 ROWVERSION NOT NULL,

    CONSTRAINT PK_Ementa PRIMARY KEY CLUSTERED (EmentaId),
    CONSTRAINT FK_Ementa_Disciplina FOREIGN KEY (DisciplinaId)
        REFERENCES academico.Disciplina (DisciplinaId),
    CONSTRAINT FK_Ementa_MatrizDisciplina_Disciplina
        FOREIGN KEY (MatrizDisciplinaId, DisciplinaId)
        REFERENCES academico.MatrizDisciplina (MatrizDisciplinaId, DisciplinaId),
    CONSTRAINT FK_Ementa_DocumentoFonte FOREIGN KEY (DocumentoFonteId)
        REFERENCES processamento.DocumentoFonte (DocumentoFonteId),
    CONSTRAINT UQ_Ementa_Disciplina_Matriz_Versao UNIQUE (DisciplinaId, MatrizDisciplinaId, Versao),
    CONSTRAINT UQ_Ementa_Ementa_Disciplina UNIQUE (EmentaId, DisciplinaId),
    CONSTRAINT CK_Ementa_Semestre CHECK (SemestreVigencia IS NULL OR SemestreVigencia IN (1, 2)),
    CONSTRAINT CK_Ementa_CargaDeclarada CHECK (CargaHorariaDeclarada > 0),
    CONSTRAINT CK_Ementa_UnidadeCarga CHECK (UnidadeCargaHoraria IN ('HORA', 'HORA_AULA', 'CREDITO')),
    CONSTRAINT CK_Ementa_DuracaoHoraAula CHECK
        (DuracaoHoraAulaMinutos IS NULL OR DuracaoHoraAulaMinutos BETWEEN 30 AND 120),
    CONSTRAINT CK_Ementa_CargaNormalizada CHECK
        (CargaHorariaNormalizadaMin IS NULL OR CargaHorariaNormalizadaMin > 0),
    CONSTRAINT CK_Ementa_Status CHECK (Status IN ('RASCUNHO', 'EM_REVISAO', 'PUBLICADA', 'ARQUIVADA')),
    CONSTRAINT CK_Ementa_ConfiancaParsing CHECK
        (ConfiancaParsing IS NULL OR ConfiancaParsing BETWEEN 0 AND 1),
    CONSTRAINT CK_Ementa_Publicacao CHECK
        ((Status = 'PUBLICADA' AND PublicadaEm IS NOT NULL) OR Status <> 'PUBLICADA')
);
GO

CREATE INDEX IX_Ementa_DocumentoFonte
    ON academico.Ementa (DocumentoFonteId)
    WHERE DocumentoFonteId IS NOT NULL;
GO

CREATE INDEX IX_Ementa_Disciplina_Status
    ON academico.Ementa (DisciplinaId, Status, AnoVigencia DESC);
GO

CREATE TABLE academico.ConteudoProgramatico
(
    ConteudoProgramaticoId BIGINT IDENTITY(1,1) NOT NULL,
    EmentaId               BIGINT NOT NULL,
    Ordem                  INT NOT NULL,
    Titulo                 NVARCHAR(300) NULL,
    TextoOriginal          NVARCHAR(MAX) NOT NULL,
    TextoNormalizado       NVARCHAR(MAX) NULL,
    Peso                   DECIMAL(8,5) NOT NULL CONSTRAINT DF_ConteudoProgramatico_Peso DEFAULT (1),
    PaginaInicial          INT NULL,
    PaginaFinal            INT NULL,
    CoordenadasJson        NVARCHAR(MAX) NULL,
    ConfiancaExtracao      DECIMAL(6,5) NULL,
    CriadoEm               DATETIME2(3) NOT NULL CONSTRAINT DF_ConteudoProgramatico_CriadoEm DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT PK_ConteudoProgramatico PRIMARY KEY CLUSTERED (ConteudoProgramaticoId),
    CONSTRAINT FK_ConteudoProgramatico_Ementa FOREIGN KEY (EmentaId)
        REFERENCES academico.Ementa (EmentaId),
    CONSTRAINT UQ_ConteudoProgramatico_Ementa_Ordem UNIQUE (EmentaId, Ordem),
    CONSTRAINT UQ_ConteudoProgramatico_Id_Ementa UNIQUE (ConteudoProgramaticoId, EmentaId),
    CONSTRAINT CK_ConteudoProgramatico_Ordem CHECK (Ordem > 0),
    CONSTRAINT CK_ConteudoProgramatico_Peso CHECK (Peso > 0),
    CONSTRAINT CK_ConteudoProgramatico_Paginas CHECK
        ((PaginaInicial IS NULL AND PaginaFinal IS NULL) OR
         (PaginaInicial IS NOT NULL AND PaginaFinal IS NOT NULL AND
          PaginaInicial > 0 AND PaginaFinal >= PaginaInicial)),
    CONSTRAINT CK_ConteudoProgramatico_CoordenadasJson CHECK
        (CoordenadasJson IS NULL OR ISJSON(CoordenadasJson) = 1),
    CONSTRAINT CK_ConteudoProgramatico_Confianca CHECK
        (ConfiancaExtracao IS NULL OR ConfiancaExtracao BETWEEN 0 AND 1)
);
GO

CREATE TABLE academico.ObjetivoEmenta
(
    ObjetivoEmentaId    BIGINT IDENTITY(1,1) NOT NULL,
    EmentaId            BIGINT NOT NULL,
    Ordem               INT NOT NULL,
    Tipo                VARCHAR(15) NOT NULL CONSTRAINT DF_ObjetivoEmenta_Tipo DEFAULT ('GERAL'),
    Texto               NVARCHAR(MAX) NOT NULL,

    CONSTRAINT PK_ObjetivoEmenta PRIMARY KEY CLUSTERED (ObjetivoEmentaId),
    CONSTRAINT FK_ObjetivoEmenta_Ementa FOREIGN KEY (EmentaId)
        REFERENCES academico.Ementa (EmentaId),
    CONSTRAINT UQ_ObjetivoEmenta_Ementa_Ordem UNIQUE (EmentaId, Ordem),
    CONSTRAINT CK_ObjetivoEmenta_Ordem CHECK (Ordem > 0),
    CONSTRAINT CK_ObjetivoEmenta_Tipo CHECK (Tipo IN ('GERAL', 'ESPECIFICO'))
);
GO

CREATE TABLE academico.Bibliografia
(
    BibliografiaId      BIGINT IDENTITY(1,1) NOT NULL,
    EmentaId            BIGINT NOT NULL,
    Ordem               INT NOT NULL,
    Tipo                VARCHAR(15) NOT NULL,
    ReferenciaTexto     NVARCHAR(MAX) NOT NULL,
    Isbn                NVARCHAR(20) NULL,

    CONSTRAINT PK_Bibliografia PRIMARY KEY CLUSTERED (BibliografiaId),
    CONSTRAINT FK_Bibliografia_Ementa FOREIGN KEY (EmentaId)
        REFERENCES academico.Ementa (EmentaId),
    CONSTRAINT UQ_Bibliografia_Ementa_Ordem UNIQUE (EmentaId, Ordem),
    CONSTRAINT CK_Bibliografia_Ordem CHECK (Ordem > 0),
    CONSTRAINT CK_Bibliografia_Tipo CHECK (Tipo IN ('BASICA', 'COMPLEMENTAR', 'OUTRA'))
);
GO

/* GOVERNANCA E PROCESSAMENTO NLP */

CREATE TABLE governanca.ModeloProcessamento
(
    ModeloProcessamentoId BIGINT IDENTITY(1,1) NOT NULL,
    TipoModelo            VARCHAR(20) NOT NULL,
    Provedor              NVARCHAR(100) NOT NULL,
    NomeModelo            NVARCHAR(200) NOT NULL,
    RevisaoModelo         NVARCHAR(100) NOT NULL,
    Dimensoes             INT NULL,
    ParametrosJson        NVARCHAR(MAX) NULL,
    Ativo                 BIT NOT NULL CONSTRAINT DF_ModeloProcessamento_Ativo DEFAULT (1),
    CriadoEm              DATETIME2(3) NOT NULL CONSTRAINT DF_ModeloProcessamento_CriadoEm DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT PK_ModeloProcessamento PRIMARY KEY CLUSTERED (ModeloProcessamentoId),
    CONSTRAINT UQ_ModeloProcessamento_Identidade
        UNIQUE (TipoModelo, Provedor, NomeModelo, RevisaoModelo),
    CONSTRAINT CK_ModeloProcessamento_Tipo CHECK
        (TipoModelo IN ('EMBEDDING', 'PARSER', 'OCR', 'RERANKER', 'CLASSIFICADOR')),
    CONSTRAINT CK_ModeloProcessamento_Dimensoes CHECK (Dimensoes IS NULL OR Dimensoes > 0),
    CONSTRAINT CK_ModeloProcessamento_ParametrosJson CHECK
        (ParametrosJson IS NULL OR ISJSON(ParametrosJson) = 1)
);
GO

CREATE TABLE processamento.ExecucaoProcessamento
(
    ExecucaoProcessamentoId BIGINT IDENTITY(1,1) NOT NULL,
    DocumentoFonteId        BIGINT NOT NULL,
    ModeloProcessamentoId   BIGINT NULL,
    PipelineVersao          NVARCHAR(50) NOT NULL,
    TipoExecucao            VARCHAR(20) NOT NULL,
    Status                  VARCHAR(20) NOT NULL CONSTRAINT DF_ExecucaoProcessamento_Status DEFAULT ('PENDENTE'),
    Tentativa               INT NOT NULL CONSTRAINT DF_ExecucaoProcessamento_Tentativa DEFAULT (1),
    IniciadoEm              DATETIME2(3) NULL,
    FinalizadoEm            DATETIME2(3) NULL,
    DuracaoMs               BIGINT NULL,
    MetricasJson            NVARCHAR(MAX) NULL,
    MensagemErro            NVARCHAR(MAX) NULL,
    CriadoEm                DATETIME2(3) NOT NULL CONSTRAINT DF_ExecucaoProcessamento_CriadoEm DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT PK_ExecucaoProcessamento PRIMARY KEY CLUSTERED (ExecucaoProcessamentoId),
    CONSTRAINT FK_ExecucaoProcessamento_Documento FOREIGN KEY (DocumentoFonteId)
        REFERENCES processamento.DocumentoFonte (DocumentoFonteId),
    CONSTRAINT FK_ExecucaoProcessamento_Modelo FOREIGN KEY (ModeloProcessamentoId)
        REFERENCES governanca.ModeloProcessamento (ModeloProcessamentoId),
    CONSTRAINT UQ_ExecucaoProcessamento_Idempotencia
        UNIQUE (DocumentoFonteId, PipelineVersao, TipoExecucao, Tentativa),
    CONSTRAINT CK_ExecucaoProcessamento_Tipo CHECK
        (TipoExecucao IN ('EXTRACAO', 'OCR', 'PARSING', 'EMBEDDING', 'PIPELINE_COMPLETO')),
    CONSTRAINT CK_ExecucaoProcessamento_Status CHECK
        (Status IN ('PENDENTE', 'EXECUTANDO', 'CONCLUIDA', 'FALHA', 'CANCELADA')),
    CONSTRAINT CK_ExecucaoProcessamento_Tentativa CHECK (Tentativa > 0),
    CONSTRAINT CK_ExecucaoProcessamento_Duracao CHECK (DuracaoMs IS NULL OR DuracaoMs >= 0),
    CONSTRAINT CK_ExecucaoProcessamento_MetricasJson CHECK
        (MetricasJson IS NULL OR ISJSON(MetricasJson) = 1),
    CONSTRAINT CK_ExecucaoProcessamento_Datas CHECK
        (FinalizadoEm IS NULL OR (IniciadoEm IS NOT NULL AND FinalizadoEm >= IniciadoEm))
);
GO

CREATE INDEX IX_ExecucaoProcessamento_Documento_Status
    ON processamento.ExecucaoProcessamento (DocumentoFonteId, Status, CriadoEm DESC);
GO

CREATE TABLE processamento.RepresentacaoVetorial
(
    RepresentacaoVetorialId BIGINT IDENTITY(1,1) NOT NULL,
    EmentaId                BIGINT NOT NULL,
    ConteudoProgramaticoId  BIGINT NULL,
    ModeloProcessamentoId   BIGINT NOT NULL,
    TipoRepresentacao       VARCHAR(20) NOT NULL,
    Dimensoes               INT NOT NULL,
    Formato                 VARCHAR(20) NOT NULL CONSTRAINT DF_RepresentacaoVetorial_Formato DEFAULT ('FLOAT32_LE'),
    Normalizado             BIT NOT NULL CONSTRAINT DF_RepresentacaoVetorial_Normalizado DEFAULT (1),
    Vetor                   VARBINARY(MAX) NOT NULL,
    HashTextoSha256         CHAR(64) NOT NULL,
    CriadoEm                DATETIME2(3) NOT NULL CONSTRAINT DF_RepresentacaoVetorial_CriadoEm DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT PK_RepresentacaoVetorial PRIMARY KEY CLUSTERED (RepresentacaoVetorialId),
    CONSTRAINT FK_RepresentacaoVetorial_Ementa FOREIGN KEY (EmentaId)
        REFERENCES academico.Ementa (EmentaId),
    CONSTRAINT FK_RepresentacaoVetorial_Conteudo_Ementa
        FOREIGN KEY (ConteudoProgramaticoId, EmentaId)
        REFERENCES academico.ConteudoProgramatico (ConteudoProgramaticoId, EmentaId),
    CONSTRAINT FK_RepresentacaoVetorial_Modelo FOREIGN KEY (ModeloProcessamentoId)
        REFERENCES governanca.ModeloProcessamento (ModeloProcessamentoId),
    CONSTRAINT UQ_RepresentacaoVetorial_Identidade
        UNIQUE (EmentaId, ConteudoProgramaticoId, ModeloProcessamentoId, TipoRepresentacao),
    CONSTRAINT CK_RepresentacaoVetorial_Tipo CHECK
        (TipoRepresentacao IN ('EMENTA_GLOBAL', 'RESUMO', 'CONTEUDO')),
    CONSTRAINT CK_RepresentacaoVetorial_Conteudo CHECK
        ((TipoRepresentacao = 'CONTEUDO' AND ConteudoProgramaticoId IS NOT NULL) OR
         (TipoRepresentacao <> 'CONTEUDO' AND ConteudoProgramaticoId IS NULL)),
    CONSTRAINT CK_RepresentacaoVetorial_Dimensoes CHECK (Dimensoes > 0),
    CONSTRAINT CK_RepresentacaoVetorial_Formato CHECK (Formato = 'FLOAT32_LE'),
    CONSTRAINT CK_RepresentacaoVetorial_Tamanho CHECK (DATALENGTH(Vetor) = Dimensoes * 4),
    CONSTRAINT CK_RepresentacaoVetorial_Hash CHECK
        (LEN(HashTextoSha256) = 64 AND HashTextoSha256 NOT LIKE '%[^0-9A-Fa-f]%')
);
GO

CREATE INDEX IX_RepresentacaoVetorial_Ementa_Modelo
    ON processamento.RepresentacaoVetorial (EmentaId, ModeloProcessamentoId, TipoRepresentacao);
GO

/* EQUIVALENCIA */

CREATE TABLE equivalencia.AvaliacaoEquivalencia
(
    AvaliacaoEquivalenciaId BIGINT IDENTITY(1,1) NOT NULL,
    EmentaMatrizId          BIGINT NOT NULL,
    EmentaCandidataId       BIGINT NOT NULL,
    ModeloEmbeddingId       BIGINT NOT NULL,
    PipelineVersao          NVARCHAR(50) NOT NULL,
    PoliticaVersao          NVARCHAR(50) NOT NULL,
    Status                  VARCHAR(20) NOT NULL CONSTRAINT DF_AvaliacaoEquivalencia_Status DEFAULT ('PENDENTE'),
    CoberturaMatriz         DECIMAL(6,5) NULL,
    CoberturaCandidata      DECIMAL(6,5) NULL,
    SimilaridadeGlobal      DECIMAL(6,5) NULL,
    SimilaridadeTfidf       DECIMAL(6,5) NULL,
    RazaoCargaHoraria       DECIMAL(9,6) NULL,
    CargaCompativel         BIT NULL,
    ScoreFinal              DECIMAL(6,5) NULL,
    Confianca               DECIMAL(6,5) NULL,
    Recomendacao            VARCHAR(30) NULL,
    JustificativaAutomatica NVARCHAR(MAX) NULL,
    ParametrosJson          NVARCHAR(MAX) NULL,
    IniciadaEm              DATETIME2(3) NULL,
    FinalizadaEm            DATETIME2(3) NULL,
    CriadoEm                DATETIME2(3) NOT NULL CONSTRAINT DF_AvaliacaoEquivalencia_CriadoEm DEFAULT (SYSUTCDATETIME()),
    VersaoLinha             ROWVERSION NOT NULL,

    CONSTRAINT PK_AvaliacaoEquivalencia PRIMARY KEY CLUSTERED (AvaliacaoEquivalenciaId),
    CONSTRAINT FK_AvaliacaoEquivalencia_EmentaMatriz FOREIGN KEY (EmentaMatrizId)
        REFERENCES academico.Ementa (EmentaId),
    CONSTRAINT FK_AvaliacaoEquivalencia_EmentaCandidata FOREIGN KEY (EmentaCandidataId)
        REFERENCES academico.Ementa (EmentaId),
    CONSTRAINT FK_AvaliacaoEquivalencia_Modelo FOREIGN KEY (ModeloEmbeddingId)
        REFERENCES governanca.ModeloProcessamento (ModeloProcessamentoId),
    CONSTRAINT UQ_AvaliacaoEquivalencia_Id_Ementas
        UNIQUE (AvaliacaoEquivalenciaId, EmentaMatrizId, EmentaCandidataId),
    CONSTRAINT CK_AvaliacaoEquivalencia_EmentasDiferentes CHECK (EmentaMatrizId <> EmentaCandidataId),
    CONSTRAINT CK_AvaliacaoEquivalencia_Status CHECK
        (Status IN ('PENDENTE', 'PROCESSANDO', 'CONCLUIDA', 'FALHA', 'CANCELADA')),
    CONSTRAINT CK_AvaliacaoEquivalencia_CoberturaMatriz CHECK
        (CoberturaMatriz IS NULL OR CoberturaMatriz BETWEEN 0 AND 1),
    CONSTRAINT CK_AvaliacaoEquivalencia_CoberturaCandidata CHECK
        (CoberturaCandidata IS NULL OR CoberturaCandidata BETWEEN 0 AND 1),
    CONSTRAINT CK_AvaliacaoEquivalencia_SimilaridadeGlobal CHECK
        (SimilaridadeGlobal IS NULL OR SimilaridadeGlobal BETWEEN 0 AND 1),
    CONSTRAINT CK_AvaliacaoEquivalencia_Tfidf CHECK
        (SimilaridadeTfidf IS NULL OR SimilaridadeTfidf BETWEEN 0 AND 1),
    CONSTRAINT CK_AvaliacaoEquivalencia_RazaoCarga CHECK
        (RazaoCargaHoraria IS NULL OR RazaoCargaHoraria >= 0),
    CONSTRAINT CK_AvaliacaoEquivalencia_Score CHECK
        (ScoreFinal IS NULL OR ScoreFinal BETWEEN 0 AND 1),
    CONSTRAINT CK_AvaliacaoEquivalencia_Confianca CHECK
        (Confianca IS NULL OR Confianca BETWEEN 0 AND 1),
    CONSTRAINT CK_AvaliacaoEquivalencia_Recomendacao CHECK
        (Recomendacao IS NULL OR Recomendacao IN
            ('EQUIVALENTE', 'PARCIALMENTE_EQUIVALENTE', 'NAO_EQUIVALENTE', 'REVISAO_MANUAL')),
    CONSTRAINT CK_AvaliacaoEquivalencia_ParametrosJson CHECK
        (ParametrosJson IS NULL OR ISJSON(ParametrosJson) = 1),
    CONSTRAINT CK_AvaliacaoEquivalencia_Datas CHECK
        (FinalizadaEm IS NULL OR (IniciadaEm IS NOT NULL AND FinalizadaEm >= IniciadaEm))
);
GO

CREATE INDEX IX_AvaliacaoEquivalencia_Par_Status
    ON equivalencia.AvaliacaoEquivalencia
       (EmentaMatrizId, EmentaCandidataId, Status, CriadoEm DESC);
GO

CREATE TABLE equivalencia.CorrespondenciaConteudo
(
    CorrespondenciaConteudoId BIGINT IDENTITY(1,1) NOT NULL,
    AvaliacaoEquivalenciaId   BIGINT NOT NULL,
    EmentaMatrizId            BIGINT NOT NULL,
    EmentaCandidataId         BIGINT NOT NULL,
    ConteudoMatrizId          BIGINT NOT NULL,
    ConteudoCandidatoId       BIGINT NOT NULL,
    SimilaridadeSemantica     DECIMAL(6,5) NOT NULL,
    SimilaridadeLexical       DECIMAL(6,5) NULL,
    ScoreCombinado            DECIMAL(6,5) NOT NULL,
    MetodoCorrespondencia     VARCHAR(30) NOT NULL,
    PosicaoRanking            INT NULL,
    CriadoEm                  DATETIME2(3) NOT NULL CONSTRAINT DF_CorrespondenciaConteudo_CriadoEm DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT PK_CorrespondenciaConteudo PRIMARY KEY CLUSTERED (CorrespondenciaConteudoId),
    CONSTRAINT FK_CorrespondenciaConteudo_Avaliacao
        FOREIGN KEY (AvaliacaoEquivalenciaId, EmentaMatrizId, EmentaCandidataId)
        REFERENCES equivalencia.AvaliacaoEquivalencia
            (AvaliacaoEquivalenciaId, EmentaMatrizId, EmentaCandidataId),
    CONSTRAINT FK_CorrespondenciaConteudo_Matriz
        FOREIGN KEY (ConteudoMatrizId, EmentaMatrizId)
        REFERENCES academico.ConteudoProgramatico (ConteudoProgramaticoId, EmentaId),
    CONSTRAINT FK_CorrespondenciaConteudo_Candidato
        FOREIGN KEY (ConteudoCandidatoId, EmentaCandidataId)
        REFERENCES academico.ConteudoProgramatico (ConteudoProgramaticoId, EmentaId),
    CONSTRAINT UQ_CorrespondenciaConteudo_Par
        UNIQUE (AvaliacaoEquivalenciaId, ConteudoMatrizId, ConteudoCandidatoId),
    CONSTRAINT CK_CorrespondenciaConteudo_Semantica CHECK (SimilaridadeSemantica BETWEEN 0 AND 1),
    CONSTRAINT CK_CorrespondenciaConteudo_Lexical CHECK
        (SimilaridadeLexical IS NULL OR SimilaridadeLexical BETWEEN 0 AND 1),
    CONSTRAINT CK_CorrespondenciaConteudo_Combinado CHECK (ScoreCombinado BETWEEN 0 AND 1),
    CONSTRAINT CK_CorrespondenciaConteudo_Metodo CHECK
        (MetodoCorrespondencia IN ('MAX_SIMILARIDADE', 'MATCHING_BIPARTIDO', 'RERANKER', 'MANUAL')),
    CONSTRAINT CK_CorrespondenciaConteudo_Ranking CHECK
        (PosicaoRanking IS NULL OR PosicaoRanking > 0)
);
GO

CREATE INDEX IX_CorrespondenciaConteudo_Avaliacao_Matriz
    ON equivalencia.CorrespondenciaConteudo
       (AvaliacaoEquivalenciaId, ConteudoMatrizId, ScoreCombinado DESC);
GO

CREATE TABLE equivalencia.ParecerEquivalencia
(
    ParecerEquivalenciaId   BIGINT IDENTITY(1,1) NOT NULL,
    AvaliacaoEquivalenciaId BIGINT NOT NULL,
    RevisorIdentificador    NVARCHAR(100) NOT NULL,
    Decisao                 VARCHAR(30) NOT NULL,
    Justificativa           NVARCHAR(MAX) NOT NULL,
    ParecerEmitidoEm        DATETIME2(3) NOT NULL CONSTRAINT DF_ParecerEquivalencia_EmitidoEm DEFAULT (SYSUTCDATETIME()),
    SubstituidoPorParecerId BIGINT NULL,
    VersaoLinha             ROWVERSION NOT NULL,

    CONSTRAINT PK_ParecerEquivalencia PRIMARY KEY CLUSTERED (ParecerEquivalenciaId),
    CONSTRAINT FK_ParecerEquivalencia_Avaliacao FOREIGN KEY (AvaliacaoEquivalenciaId)
        REFERENCES equivalencia.AvaliacaoEquivalencia (AvaliacaoEquivalenciaId),
    CONSTRAINT FK_ParecerEquivalencia_Substituto FOREIGN KEY (SubstituidoPorParecerId)
        REFERENCES equivalencia.ParecerEquivalencia (ParecerEquivalenciaId),
    CONSTRAINT CK_ParecerEquivalencia_Decisao CHECK
        (Decisao IN ('EQUIVALENTE', 'PARCIALMENTE_EQUIVALENTE', 'NAO_EQUIVALENTE', 'INCONCLUSIVO')),
    CONSTRAINT CK_ParecerEquivalencia_AutoReferencia CHECK
        (SubstituidoPorParecerId IS NULL OR SubstituidoPorParecerId <> ParecerEquivalenciaId)
);
GO

CREATE INDEX IX_ParecerEquivalencia_Avaliacao
    ON equivalencia.ParecerEquivalencia (AvaliacaoEquivalenciaId, ParecerEmitidoEm DESC);
GO

/* VIEWS PARA CONSULTA */

CREATE VIEW academico.vw_EmentaCatalogo
AS
    SELECT
        e.EmentaId,
        i.InstituicaoId,
        i.Nome AS Instituicao,
        i.Sigla AS InstituicaoSigla,
        d.DisciplinaId,
        d.Codigo AS CodigoDisciplina,
        d.Nome AS Disciplina,
        c.CursoId,
        c.Nome AS Curso,
        mc.MatrizCurricularId,
        mc.Codigo AS CodigoMatriz,
        e.Versao AS VersaoEmenta,
        e.AnoVigencia,
        e.SemestreVigencia,
        e.CargaHorariaDeclarada,
        e.UnidadeCargaHoraria,
        e.CargaHorariaNormalizadaMin,
        e.Status,
        e.ConfiancaParsing
    FROM academico.Ementa AS e
    INNER JOIN academico.Disciplina AS d
        ON d.DisciplinaId = e.DisciplinaId
    INNER JOIN academico.Instituicao AS i
        ON i.InstituicaoId = d.InstituicaoId
    LEFT JOIN academico.MatrizDisciplina AS md
        ON md.MatrizDisciplinaId = e.MatrizDisciplinaId
    LEFT JOIN academico.MatrizCurricular AS mc
        ON mc.MatrizCurricularId = md.MatrizCurricularId
    LEFT JOIN academico.Curso AS c
        ON c.CursoId = mc.CursoId;
GO

CREATE VIEW equivalencia.vw_ResultadoAvaliacao
AS
    SELECT
        ae.AvaliacaoEquivalenciaId,
        ae.EmentaMatrizId,
        dm.Nome AS DisciplinaMatriz,
        im.Sigla AS InstituicaoMatriz,
        ae.EmentaCandidataId,
        dc.Nome AS DisciplinaCandidata,
        ic.Sigla AS InstituicaoCandidata,
        ae.CoberturaMatriz,
        ae.CoberturaCandidata,
        ae.SimilaridadeGlobal,
        ae.SimilaridadeTfidf,
        ae.RazaoCargaHoraria,
        ae.CargaCompativel,
        ae.ScoreFinal,
        ae.Confianca,
        ae.Recomendacao,
        ae.Status,
        ae.CriadoEm
    FROM equivalencia.AvaliacaoEquivalencia AS ae
    INNER JOIN academico.Ementa AS em
        ON em.EmentaId = ae.EmentaMatrizId
    INNER JOIN academico.Disciplina AS dm
        ON dm.DisciplinaId = em.DisciplinaId
    INNER JOIN academico.Instituicao AS im
        ON im.InstituicaoId = dm.InstituicaoId
    INNER JOIN academico.Ementa AS ec
        ON ec.EmentaId = ae.EmentaCandidataId
    INNER JOIN academico.Disciplina AS dc
        ON dc.DisciplinaId = ec.DisciplinaId
    INNER JOIN academico.Instituicao AS ic
        ON ic.InstituicaoId = dc.InstituicaoId;
GO

/* METADADOS DA VERSAO DO SCHEMA */

CREATE TABLE governanca.VersaoSchema
(
    VersaoSchemaId      INT IDENTITY(1,1) NOT NULL,
    Versao              VARCHAR(20) NOT NULL,
    Descricao           NVARCHAR(500) NOT NULL,
    AplicadaEm          DATETIME2(3) NOT NULL CONSTRAINT DF_VersaoSchema_AplicadaEm DEFAULT (SYSUTCDATETIME()),

    CONSTRAINT PK_VersaoSchema PRIMARY KEY CLUSTERED (VersaoSchemaId),
    CONSTRAINT UQ_VersaoSchema_Versao UNIQUE (Versao)
);
GO

INSERT INTO governanca.VersaoSchema (Versao, Descricao)
VALUES ('1.0.0', N'Criação inicial do modelo acadêmico, processamento NLP, embeddings e equivalência.');
GO

PRINT N'Banco EquivalenciaEmentas criado com sucesso. Schema: 1.0.0';
GO
