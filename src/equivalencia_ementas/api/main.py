import logging
import os
from pathlib import Path
from typing import Annotated
from datetime import datetime
from decimal import Decimal

from equivalencia_ementas.shared.database.session import SessionFactory

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from equivalencia_ementas.academico.application.use_cases.listar_cursos import (
    ListarCursos,
)
from equivalencia_ementas.academico.application.use_cases.receber_solicitacao import (
    ArquivoRecebido,
    ErroRecebimento,
    ReceberSolicitacao,
)
from equivalencia_ementas.academico.infrastructure.repositories.curso_repository import (
    SqlAlchemyCursoRepository,
)
from equivalencia_ementas.academico.infrastructure.repositories.solicitacao_repository import (
    SqlAlchemySolicitacaoRepository,
)

from equivalencia_ementas.academico.application.use_cases.consultar_solicitacoes import (
    ConsultarSolicitacoes,
)

from equivalencia_ementas.shared.database.session import get_session

from sqlalchemy.exc import IntegrityError

from equivalencia_ementas.seguranca.application.use_cases.cadastrar_candidato import (
    CadastrarCandidato,
    DadosCadastroCandidato,
    ErroCadastro,
)

from equivalencia_ementas.seguranca.infrastructure.repositories.usuario_repository import (
    SqlAlchemyUsuarioRepository,
)

from equivalencia_ementas.seguranca.infrastructure.security.hash_senha import (
    HashSenha,
)

from fastapi import Cookie, Response

from equivalencia_ementas.seguranca.application.use_cases.autenticar_usuario import (
    AutenticarUsuario,
    CredenciaisInvalidas,
    DadosLogin,
)

from equivalencia_ementas.seguranca.infrastructure.repositories.sessao_repository import (
    SqlAlchemySessaoRepository,
)

from equivalencia_ementas.seguranca.infrastructure.security.gerenciador_sessao import (
    GerenciadorSessao,
)

from fastapi import Request


from equivalencia_ementas.seguranca.domain.entities.usuario import (
    PerfilUsuario,
    Usuario,
)


from equivalencia_ementas.seguranca.infrastructure.repositories.controle_tentativas_repository import (
    SqlAlchemyControleTentativasRepository,
)

from equivalencia_ementas.seguranca.infrastructure.security.chaves_controle_login import (
    gerar_chave_login,
)

from equivalencia_ementas.academico.application.use_cases.consultar_solicitacoes_coordenador import (
    ConsultarSolicitacoesCoordenador,
)

import re

from fastapi.responses import FileResponse

from equivalencia_ementas.academico.infrastructure.repositories.catalogo_institucional_repository import (
    SqlAlchemyCatalogoInstitucionalRepository,
)

from equivalencia_ementas.academico.application.use_cases.atualizar_ementa_institucional import (
    AtualizarEmentaInstitucional,
    ConflitoAtualizacaoEmenta,
    DadosAtualizacaoEmenta,
    EmentaNaoEncontrada,
    ErroAtualizacaoEmenta,
)


logger = logging.getLogger(__name__)

NOME_COOKIE_SESSAO = "tcc_sessao"

# Em produção HTTPS, configurar COOKIE_SECURE=true.
COOKIE_SECURE = os.environ.get(
    "COOKIE_SECURE", "false"
).lower() == "true"

GERENCIADOR_SESSAO = GerenciadorSessao()

def get_auth_session():
    """
    Sessão independente para verificar a autenticação.

    Evita interferir na transação utilizada pelos
    endpoints que alteram dados.
    """
    with SessionFactory() as session:
        yield session

def obter_usuario_autenticado(
    request: Request,
    session: Annotated[Session, Depends(get_auth_session)],
) -> Usuario:

    token = request.cookies.get(NOME_COOKIE_SESSAO)

    if not GERENCIADOR_SESSAO.token_valido(token):
        raise HTTPException(
            status_code=401,
            detail="Autenticação necessária.",
        )

    token_hash = GERENCIADOR_SESSAO.calcular_hash(token)
    repository = SqlAlchemySessaoRepository(session)

    try:
        usuario = repository.buscar_usuario_por_token(token_hash)

    except SQLAlchemyError:
        logger.exception("Falha ao validar sessão.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível validar a sessão.",
        ) from None

    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail="Sessão inválida ou expirada.",
        )

    return usuario

def obter_instituicao_destino() -> int:
    valor = os.environ.get("INSTITUICAO_DESTINO_ID", "")

    try:
        instituicao_id = int(valor)
    except ValueError as exc:
        raise RuntimeError(
            "Configure INSTITUICAO_DESTINO_ID com o ID da instituição de destino."
        ) from exc

    if instituicao_id <= 0:
        raise RuntimeError("INSTITUICAO_DESTINO_ID deve ser positivo.")

    return instituicao_id


INSTITUICAO_DESTINO_ID = obter_instituicao_destino()

app = FastAPI(
    title="API de Equivalência de Ementas",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5173",
        "http://localhost:5174",

    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Accept", "Content-Type"],
)


class CursoResponse(BaseModel):
    id: int
    nome: str


@app.get("/api/saude", tags=["Saúde"])
def verificar_saude() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/api/cursos",
    response_model=list[CursoResponse],
    tags=["Cursos"],
)
def listar_cursos(
    session: Annotated[Session, Depends(get_session)],
) -> list[CursoResponse]:
    repository = SqlAlchemyCursoRepository(session)
    caso_de_uso = ListarCursos(repository)

    try:
        cursos = caso_de_uso.executar(INSTITUICAO_DESTINO_ID)
    except SQLAlchemyError:
        logger.exception("Falha ao consultar os cursos no banco.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível consultar os cursos no momento.",
        ) from None

    return [
        CursoResponse(id=curso.id, nome=curso.nome)
        for curso in cursos
    ]

RAIZ_PROJETO = Path(__file__).resolve().parents[3]

DIRETORIO_UPLOADS = Path(
    os.environ.get(
        "UPLOAD_DIR",
        str(RAIZ_PROJETO / "var" / "uploads"),
    )
).resolve()


class SolicitacaoResponse(BaseModel):
    protocolo: str
    status: str
    quantidade_documentos: int


class DocumentoConsultaResponse(BaseModel):
    documento_id: int
    nome_arquivo: str
    quantidade_paginas: int
    tamanho_bytes: int
    status_documento: str


class SolicitacaoResumoResponse(BaseModel):
    solicitacao_id: int
    protocolo: str
    curso_id: int
    curso_destino: str
    status: str
    criado_em: datetime
    quantidade_documentos: int


class SolicitacaoDetalhadaResponse(SolicitacaoResumoResponse):
    documentos: list[DocumentoConsultaResponse]


class CadastroCandidatoRequest(BaseModel):
    nome_completo: str = Field(min_length=3, max_length=200)
    cpf: str = Field(min_length=11, max_length=14)
    email: str = Field(min_length=5, max_length=254)
    senha: str = Field(min_length=12, max_length=128)


class CadastroCandidatoResponse(BaseModel):
    usuario_id: int
    nome_completo: str
    email: str
    mensagem: str


class LoginRequest(BaseModel):
    identificador: str
    senha: str


class UsuarioLogadoResponse(BaseModel):
    usuario_id: int
    nome_completo: str
    email: str
    perfil: str
    email_verificado: bool


class CursoCoordenacaoResponse(BaseModel):
    curso_id: int
    codigo: str
    nome: str
    nivel: str
    modalidade: str


class MatrizCoordenacaoResponse(BaseModel):
    matriz_curricular_id: int
    curso_id: int
    codigo: str
    nome: str | None
    ano_inicio_vigencia: int | None
    semestre_inicio: int | None
    ano_fim_vigencia: int | None
    semestre_fim: int | None
    status: str

    class DisciplinaMatrizCoordenacaoResponse(BaseModel):
        matriz_disciplina_id: int
        disciplina_id: int
        codigo: str
        nome: str
        periodo_sugerido: int | None
        natureza: str

        quantidade_ementas: int

        ementa_id: int | None
        versao: str | None
        status_ementa: str | None
        carga_horaria: float | None


class DisciplinaMatrizCoordenacaoResponse(BaseModel):
    matriz_disciplina_id: int
    disciplina_id: int
    codigo: str
    nome: str
    periodo_sugerido: int | None
    natureza: str

    quantidade_ementas: int

    ementa_id: int | None
    versao: str | None
    status_ementa: str | None
    carga_horaria: float | None

class ObjetivoEmentaResponse(BaseModel):
    objetivo_id: int
    ordem: int
    tipo: str
    texto: str


class ConteudoProgramaticoResponse(BaseModel):
    conteudo_id: int
    ordem: int
    titulo: str | None
    texto: str


class BibliografiaEmentaResponse(BaseModel):
    bibliografia_id: int
    ordem: int
    tipo: str
    referencia: str
    isbn: str | None


class EmentaInstitucionalDetalheResponse(BaseModel):
    ementa_id: int
    matriz_disciplina_id: int
    disciplina_id: int
    codigo_disciplina: str
    nome_disciplina: str

    matriz_curricular_id: int
    codigo_matriz: str
    nome_matriz: str | None

    curso_id: int
    nome_curso: str

    versao: str
    status: str
    idioma: str
    ano_vigencia: int | None
    semestre_vigencia: int | None

    resumo: str | None
    competencias_habilidades: str | None

    carga_horaria_total: float | None
    carga_horaria_teorica: float | None
    carga_horaria_pratica: float | None
    unidade_carga_horaria: str

    criado_em: datetime
    atualizado_em: datetime

    objetivos: list[ObjetivoEmentaResponse]
    conteudos_programaticos: list[ConteudoProgramaticoResponse]
    bibliografias: list[BibliografiaEmentaResponse]

    versao_linha: str


class AtualizarEmentaInstitucionalRequest(BaseModel):
    versao_linha: str = Field(
        ...,
        pattern=r"^0x[0-9a-fA-F]{16}$",
    )

    resumo: str | None
    competencias_habilidades: str | None

    carga_horaria_total: Decimal | None
    carga_horaria_teorica: Decimal | None
    carga_horaria_pratica: Decimal | None


class AtualizarTextoObjetivoRequest(BaseModel):
    versao_linha: str = Field(
        ...,
        pattern=r"^0x[0-9a-fA-F]{16}$",
    )
    texto: str = Field(
        ...,
        min_length=1,
        max_length=30000,
    )


@app.post(
    "/api/solicitacoes",
    response_model=SolicitacaoResponse,
    status_code=201,
    tags=["Solicitações"],
)
def receber_solicitacao(
    curso_id: Annotated[int, Form(gt=0)],
    arquivos: Annotated[list[UploadFile], File()],
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(obter_usuario_autenticado)],
) -> SolicitacaoResponse:

    if usuario.perfil != PerfilUsuario.CANDIDATO:
        raise HTTPException(
            status_code=403,
            detail="Somente candidatos podem enviar solicitações.",
        )

    if usuario.id is None:
        raise HTTPException(
            status_code=401,
            detail="Usuário inválido.",
        )

    try:
        repository = SqlAlchemySolicitacaoRepository(session)
        caso_de_uso = ReceberSolicitacao(
            repository,
            DIRETORIO_UPLOADS,
        )

        # Transação única para a solicitação e seus documentos.
        with session.begin():
            resultado = caso_de_uso.executar(
                curso_id=curso_id,
                instituicao_id=INSTITUICAO_DESTINO_ID,
                candidato_usuario_id=usuario.id,
                arquivos=[
                    ArquivoRecebido(
                        nome=arquivo.filename or "",
                        stream=arquivo.file,
                    )
                    for arquivo in arquivos
                ],
            )

        return SolicitacaoResponse(
            protocolo=resultado.protocolo,
            status=resultado.status,
            quantidade_documentos=resultado.quantidade_documentos,
        )

    except ErroRecebimento as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except SQLAlchemyError:
        logger.exception("Falha ao registrar solicitação.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível registrar a solicitação.",
        ) from None

    except OSError:
        logger.exception("Falha ao armazenar documentos.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível armazenar os documentos.",
        ) from None

    finally:
        for arquivo in arquivos:
            awaitable = getattr(arquivo, "file", None)
            if awaitable is not None:
                awaitable.close()


class AtualizarTextoConteudoRequest(BaseModel):
    versao_linha: str = Field(
        ...,
        pattern=r"^0x[0-9a-fA-F]{16}$",
    )

    texto: str = Field(
        ...,
        min_length=1,
        max_length=30000,
    )


class AtualizarTextoBibliografiaRequest(BaseModel):
    versao_linha: str = Field(
        ...,
        pattern=r"^0x[0-9a-fA-F]{16}$",
    )

    texto: str = Field(
        ...,
        min_length=1,
        max_length=30000,
    )


@app.get(
    "/api/solicitacoes",
    response_model=list[SolicitacaoResumoResponse],
    tags=["Solicitações"],
)
def listar_solicitacoes(
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(obter_usuario_autenticado)],
    limite: int = 50,
) -> list[SolicitacaoResumoResponse]:

    if usuario.perfil != PerfilUsuario.CANDIDATO:
        raise HTTPException(
            status_code=403,
            detail="Acesso permitido apenas para candidatos.",
        )

    if usuario.id is None:
        raise HTTPException(
            status_code=401,
            detail="Usuário inválido.",
        )

    if not 1 <= limite <= 100:
        raise HTTPException(
            status_code=422,
            detail="O limite deve estar entre 1 e 100.",
        )

    repository = SqlAlchemySolicitacaoRepository(session)
    caso_de_uso = ConsultarSolicitacoes(repository)

    try:
        registros = caso_de_uso.listar(
            instituicao_id=INSTITUICAO_DESTINO_ID,
            candidato_usuario_id=usuario.id,
            limite=limite,
        )
    except SQLAlchemyError:
        logger.exception("Falha ao listar solicitações.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível consultar as solicitações.",
        ) from None

    return [
        SolicitacaoResumoResponse(**vars(registro))
        for registro in registros
    ]



@app.get(
    "/api/solicitacoes/{protocolo}",
    response_model=SolicitacaoDetalhadaResponse,
    tags=["Solicitações"],
)
def consultar_solicitacao(
    protocolo: str,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(obter_usuario_autenticado)],
) -> SolicitacaoDetalhadaResponse:

    if usuario.perfil != PerfilUsuario.CANDIDATO:
        raise HTTPException(
            status_code=403,
            detail="Acesso permitido apenas para candidatos.",
        )

    if usuario.id is None:
        raise HTTPException(
            status_code=401,
            detail="Usuário inválido.",
        )

    repository = SqlAlchemySolicitacaoRepository(session)
    caso_de_uso = ConsultarSolicitacoes(repository)

    try:
        registro = caso_de_uso.buscar(
            protocolo=protocolo,
            instituicao_id=INSTITUICAO_DESTINO_ID,
            candidato_usuario_id=usuario.id,
        )
    except SQLAlchemyError:
        logger.exception("Falha ao consultar solicitação.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível consultar a solicitação.",
        ) from None

    if registro is None:
        raise HTTPException(
            status_code=404,
            detail="Solicitação não encontrada.",
        )

    return SolicitacaoDetalhadaResponse(
        solicitacao_id=registro.solicitacao_id,
        protocolo=registro.protocolo,
        curso_id=registro.curso_id,
        curso_destino=registro.curso_destino,
        status=registro.status,
        criado_em=registro.criado_em,
        quantidade_documentos=registro.quantidade_documentos,
        documentos=[
            DocumentoConsultaResponse(**vars(documento))
            for documento in registro.documentos
        ],
    )


@app.post(
    "/api/auth/cadastro",
    response_model=CadastroCandidatoResponse,
    status_code=201,
    tags=["Autenticação"],
)
def cadastrar_candidato(
    dados: CadastroCandidatoRequest,
    session: Annotated[Session, Depends(get_session)],
) -> CadastroCandidatoResponse:

    repository = SqlAlchemyUsuarioRepository(session)
    hash_senha = HashSenha()
    caso_de_uso = CadastrarCandidato(repository, hash_senha)

    try:
        with session.begin():
            resultado = caso_de_uso.executar(
                DadosCadastroCandidato(
                    nome_completo=dados.nome_completo,
                    cpf=dados.cpf,
                    email=dados.email,
                    senha=dados.senha,
                )
            )

    except ErroCadastro as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except IntegrityError:
        logger.warning(
            "Tentativa de cadastro com dados únicos já existentes."
        )
        raise HTTPException(
            status_code=409,
            detail="CPF ou e-mail já cadastrado.",
        ) from None

    except SQLAlchemyError:
        logger.exception("Falha ao cadastrar candidato.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível realizar o cadastro.",
        ) from None

    return CadastroCandidatoResponse(
        usuario_id=resultado.usuario_id,
        nome_completo=resultado.nome_completo,
        email=resultado.email,
        mensagem="Cadastro realizado com sucesso.",
    )



@app.post(
    "/api/auth/login",
    response_model=UsuarioLogadoResponse,
    tags=["Autenticação"],
)
def login(
    dados: LoginRequest,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
) -> UsuarioLogadoResponse:

    usuario_repository = SqlAlchemyUsuarioRepository(session)
    sessao_repository = SqlAlchemySessaoRepository(session)

    controle_repository = SqlAlchemyControleTentativasRepository(
        session
    )

    caso_de_uso = AutenticarUsuario(
        usuario_repository,
        HashSenha(),
    )

    # O identificador é protegido por HMAC.
    chave_login = gerar_chave_login(dados.identificador)

    usuario = None
    dados_sessao = None
    credenciais_invalidas = False
    bloqueado = False

    try:
        with session.begin():

            # Verifica bloqueio antes da senha.
            bloqueado = controle_repository.esta_bloqueado(
                chave_login
            )

            if not bloqueado:
                try:
                    usuario = caso_de_uso.executar(
                        DadosLogin(
                            identificador=dados.identificador,
                            senha=dados.senha,
                        )
                    )

                except CredenciaisInvalidas:
                    credenciais_invalidas = True

                    # A falha será confirmada no COMMIT.
                    controle_repository.registrar_falha(
                        chave_login
                    )

                    # A quinta falha já ativa o bloqueio.
                    bloqueado = controle_repository.esta_bloqueado(
                        chave_login
                    )

                else:
                    # Login válido: zera tentativas anteriores.
                    controle_repository.limpar(chave_login)

                    dados_sessao = GERENCIADOR_SESSAO.gerar()

                    sessao_repository.criar(
                        usuario_id=usuario.usuario_id,
                        token_hash=dados_sessao.token_hash,
                        expira_em=dados_sessao.expira_em,
                    )

        # A transação já terminou neste ponto.
        # Por isso a falha não será desfeita por rollback.

    except SQLAlchemyError:
        logger.exception("Falha ao autenticar usuário.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível realizar o login.",
        ) from None

    if bloqueado:
        raise HTTPException(
            status_code=429,
            detail=(
                "Muitas tentativas de login. "
                "Aguarde 15 minutos antes de tentar novamente."
            ),
        )

    if credenciais_invalidas:
        raise HTTPException(
            status_code=401,
            detail="CPF/e-mail ou senha inválidos.",
        )

    if usuario is None or dados_sessao is None:
        raise HTTPException(
            status_code=401,
            detail="CPF/e-mail ou senha inválidos.",
        )

    response.set_cookie(
        key=NOME_COOKIE_SESSAO,
        value=dados_sessao.token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        max_age=8 * 60 * 60,
        path="/",
    )

    return UsuarioLogadoResponse(
        usuario_id=usuario.usuario_id,
        nome_completo=usuario.nome_completo,
        email=usuario.email,
        perfil=usuario.perfil,
        email_verificado=usuario.email_verificado,
    )


@app.get(
    "/api/auth/me",
    response_model=UsuarioLogadoResponse,
    tags=["Autenticação"],
)
def usuario_atual(
    usuario: Annotated[
        Usuario,
        Depends(obter_usuario_autenticado),
    ],
) -> UsuarioLogadoResponse:

    return UsuarioLogadoResponse(
        usuario_id=usuario.id,
        nome_completo=usuario.nome_completo,
        email=usuario.email,
        perfil=usuario.perfil.value,
        email_verificado=usuario.email_verificado,
    )

@app.post(
    "/api/auth/logout",
    status_code=204,
    tags=["Autenticação"],
)
def logout(
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
) -> None:

    token = request.cookies.get(NOME_COOKIE_SESSAO)

    if token and GERENCIADOR_SESSAO.token_valido(token):
        token_hash = GERENCIADOR_SESSAO.calcular_hash(token)

        try:
            with session.begin():
                repository = SqlAlchemySessaoRepository(session)
                repository.revogar(token_hash)

        except SQLAlchemyError:
            logger.exception("Falha ao encerrar sessão.")

            raise HTTPException(
                status_code=503,
                detail="Não foi possível encerrar a sessão.",
            ) from None

    response.delete_cookie(
        key=NOME_COOKIE_SESSAO,
        path="/",
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="strict",
    )


@app.get(
    "/api/coordenacao/solicitacoes",
    response_model=list[SolicitacaoResumoResponse],
    tags=["Coordenação"],
)
def listar_solicitacoes_coordenacao(
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(obter_usuario_autenticado)],
    limite: int = 50,
) -> list[SolicitacaoResumoResponse]:

    if usuario.perfil != PerfilUsuario.COORDENADOR:
        raise HTTPException(
            status_code=403,
            detail="Acesso permitido apenas para coordenadores.",
        )

    if usuario.id is None:
        raise HTTPException(
            status_code=401,
            detail="Usuário inválido.",
        )

    if not 1 <= limite <= 100:
        raise HTTPException(
            status_code=422,
            detail="O limite deve estar entre 1 e 100.",
        )

    repository = SqlAlchemySolicitacaoRepository(session)

    caso_de_uso = ConsultarSolicitacoesCoordenador(
        repository
    )

    try:
        registros = caso_de_uso.listar(
            instituicao_id=INSTITUICAO_DESTINO_ID,
            coordenador_usuario_id=usuario.id,
            limite=limite,
        )

    except SQLAlchemyError:
        logger.exception(
            "Falha ao listar solicitações da coordenação."
        )
        raise HTTPException(
            status_code=503,
            detail="Não foi possível consultar as solicitações.",
        ) from None

    return [
        SolicitacaoResumoResponse(
            **vars(registro)
        )
        for registro in registros
    ]

@app.get(
    "/api/coordenacao/solicitacoes/{protocolo}",
    response_model=SolicitacaoDetalhadaResponse,
    tags=["Coordenação"],
)
def consultar_solicitacao_coordenacao(
    protocolo: str,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[
        Usuario,
        Depends(obter_usuario_autenticado),
    ],
) -> SolicitacaoDetalhadaResponse:

    if usuario.perfil != PerfilUsuario.COORDENADOR:
        raise HTTPException(
            status_code=403,
            detail="Acesso permitido apenas para coordenadores.",
        )

    if usuario.id is None:
        raise HTTPException(
            status_code=401,
            detail="Usuário inválido.",
        )

    repository = SqlAlchemySolicitacaoRepository(session)
    caso_de_uso = ConsultarSolicitacoesCoordenador(repository)

    try:
        registro = caso_de_uso.buscar(
            protocolo=protocolo,
            instituicao_id=INSTITUICAO_DESTINO_ID,
            coordenador_usuario_id=usuario.id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except SQLAlchemyError:
        logger.exception(
            "Falha ao consultar detalhes da solicitação."
        )
        raise HTTPException(
            status_code=503,
            detail="Não foi possível consultar a solicitação.",
        ) from None

    if registro is None:
        raise HTTPException(
            status_code=404,
            detail="Solicitação não encontrada.",
        )

    return SolicitacaoDetalhadaResponse(
        solicitacao_id=registro.solicitacao_id,
        protocolo=registro.protocolo,
        curso_id=registro.curso_id,
        curso_destino=registro.curso_destino,
        status=registro.status,
        criado_em=registro.criado_em,
        quantidade_documentos=registro.quantidade_documentos,
        documentos=[
            DocumentoConsultaResponse(**vars(documento))
            for documento in registro.documentos
        ],
    )

@app.get(
    "/api/coordenacao/solicitacoes/{protocolo}/documentos/{documento_id}/arquivo",
    tags=["Coordenação"],
)
def visualizar_documento_coordenacao(
    protocolo: str,
    documento_id: int,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[
        Usuario,
        Depends(obter_usuario_autenticado),
    ],
) -> FileResponse:

    # 1. Verifica o perfil do usuário autenticado.
    if usuario.perfil != PerfilUsuario.COORDENADOR:
        raise HTTPException(
            status_code=403,
            detail="Acesso permitido apenas para coordenadores.",
        )

    if usuario.id is None:
        raise HTTPException(
            status_code=401,
            detail="Usuário inválido.",
        )

    if documento_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="Documento inválido.",
        )

    # 2. Consulta somente documentos autorizados.
    repository = SqlAlchemySolicitacaoRepository(session)

    try:
        documento = repository.buscar_arquivo_documento_coordenador(
            protocolo=protocolo,
            documento_id=documento_id,
            instituicao_id=INSTITUICAO_DESTINO_ID,
            coordenador_usuario_id=usuario.id,
        )

    except SQLAlchemyError:
        logger.exception(
            "Falha ao verificar autorização do documento."
        )
        raise HTTPException(
            status_code=503,
            detail="Não foi possível consultar o documento.",
        ) from None

    if documento is None:
        raise HTTPException(
            status_code=404,
            detail="Documento não encontrado.",
        )

    # 3. Valida o hash que identifica o arquivo.
    hash_sha256 = documento["hash_sha256"]

    if not isinstance(hash_sha256, str):
        logger.error("Documento com hash inválido: %s", documento_id)
        raise HTTPException(
            status_code=503,
            detail="Arquivo indisponível.",
        )

    hash_sha256 = hash_sha256.lower()

    if re.fullmatch(r"[0-9a-f]{64}", hash_sha256) is None:
        logger.error("Hash inválido no documento: %s", documento_id)
        raise HTTPException(
            status_code=503,
            detail="Arquivo indisponível.",
        )

    # 4. Reconstrói o caminho dentro da pasta autorizada.
    diretorio = DIRETORIO_UPLOADS.resolve()
    caminho_pdf = (diretorio / f"{hash_sha256}.pdf").resolve()

    if not caminho_pdf.is_relative_to(diretorio):
        raise HTTPException(
            status_code=503,
            detail="Caminho do arquivo inválido.",
        )

    if not caminho_pdf.is_file():
        logger.error(
            "PDF não localizado para documento %s.",
            documento_id,
        )
        raise HTTPException(
            status_code=404,
            detail="O arquivo PDF não está disponível.",
        )

    # 5. Devolve o PDF para exibição no navegador.
    return FileResponse(
        path=caminho_pdf,
        media_type="application/pdf",
        content_disposition_type="inline",
        filename=f"documento-{documento_id}.pdf",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get(
    "/api/coordenacao/cursos",
    response_model=list[CursoCoordenacaoResponse],
    tags=["Coordenação - Ementas institucionais"],
)
def listar_cursos_coordenacao(
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(obter_usuario_autenticado)],
) -> list[CursoCoordenacaoResponse]:

    if usuario.perfil != PerfilUsuario.COORDENADOR:
        raise HTTPException(
            status_code=403,
            detail="Acesso permitido apenas para coordenadores.",
        )

    if usuario.id is None:
        raise HTTPException(
            status_code=401,
            detail="Usuário inválido.",
        )

    repository = SqlAlchemyCatalogoInstitucionalRepository(session)

    try:
        cursos = repository.listar_cursos_coordenador(
            instituicao_id=INSTITUICAO_DESTINO_ID,
            coordenador_usuario_id=usuario.id,
        )
    except SQLAlchemyError:
        logger.exception("Falha ao listar cursos do coordenador.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível consultar os cursos.",
        ) from None

    return [
        CursoCoordenacaoResponse(**curso)
        for curso in cursos
    ]


@app.get(
    "/api/coordenacao/cursos/{curso_id}/matrizes",
    response_model=list[MatrizCoordenacaoResponse],
    tags=["Coordenação - Ementas institucionais"],
)
def listar_matrizes_coordenacao(
    curso_id: int,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(obter_usuario_autenticado)],
) -> list[MatrizCoordenacaoResponse]:

    if usuario.perfil != PerfilUsuario.COORDENADOR:
        raise HTTPException(
            status_code=403,
            detail="Acesso permitido apenas para coordenadores.",
        )

    if usuario.id is None:
        raise HTTPException(
            status_code=401,
            detail="Usuário inválido.",
        )

    if curso_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="O curso deve ser válido.",
        )

    repository = SqlAlchemyCatalogoInstitucionalRepository(session)

    try:
        matrizes = repository.listar_matrizes_coordenador(
            curso_id=curso_id,
            instituicao_id=INSTITUICAO_DESTINO_ID,
            coordenador_usuario_id=usuario.id,
        )
    except SQLAlchemyError:
        logger.exception("Falha ao listar matrizes curriculares.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível consultar as matrizes.",
        ) from None

    if matrizes is None:
        raise HTTPException(
            status_code=404,
            detail="Curso não encontrado ou não autorizado.",
        )

    return [
        MatrizCoordenacaoResponse(**matriz)
        for matriz in matrizes
    ]

@app.get(
    "/api/coordenacao/matrizes/{matriz_id}/disciplinas",
    response_model=list[DisciplinaMatrizCoordenacaoResponse],
    tags=["Coordenação - Ementas institucionais"],
)
def listar_disciplinas_matriz_coordenacao(
    matriz_id: int,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(obter_usuario_autenticado)],
) -> list[DisciplinaMatrizCoordenacaoResponse]:

    # A rota é exclusiva para coordenadores.
    if usuario.perfil != PerfilUsuario.COORDENADOR:
        raise HTTPException(
            status_code=403,
            detail="Acesso permitido apenas para coordenadores.",
        )

    if usuario.id is None:
        raise HTTPException(
            status_code=401,
            detail="Usuário inválido.",
        )

    if matriz_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="A matriz curricular deve ser válida.",
        )

    repository = SqlAlchemyCatalogoInstitucionalRepository(session)

    try:
        disciplinas = repository.listar_disciplinas_matriz_coordenador(
            matriz_curricular_id=matriz_id,
            instituicao_id=INSTITUICAO_DESTINO_ID,
            coordenador_usuario_id=usuario.id,
        )

    except SQLAlchemyError:
        logger.exception(
            "Falha ao listar disciplinas da matriz curricular."
        )
        raise HTTPException(
            status_code=503,
            detail="Não foi possível consultar as disciplinas.",
        ) from None

    if disciplinas is None:
        raise HTTPException(
            status_code=404,
            detail="Matriz curricular não encontrada ou não autorizada.",
        )

    return [
        DisciplinaMatrizCoordenacaoResponse(**disciplina)
        for disciplina in disciplinas
    ]


@app.get(
    "/api/coordenacao/matriz-disciplinas/{matriz_disciplina_id}/ementas/{ementa_id}",
    response_model=EmentaInstitucionalDetalheResponse,
    tags=["Coordenação - Ementas institucionais"],
)
def consultar_ementa_institucional(
    matriz_disciplina_id: int,
    ementa_id: int,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(obter_usuario_autenticado)],
) -> EmentaInstitucionalDetalheResponse:

    if usuario.perfil != PerfilUsuario.COORDENADOR:
        raise HTTPException(
            status_code=403,
            detail="Acesso permitido apenas para coordenadores.",
        )

    if usuario.id is None:
        raise HTTPException(
            status_code=401,
            detail="Usuário inválido.",
        )

    if matriz_disciplina_id <= 0 or ementa_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="Os identificadores devem ser positivos.",
        )

    repository = SqlAlchemyCatalogoInstitucionalRepository(session)

    try:
        ementa = repository.buscar_ementa_coordenador(
            matriz_disciplina_id=matriz_disciplina_id,
            ementa_id=ementa_id,
            instituicao_id=INSTITUICAO_DESTINO_ID,
            coordenador_usuario_id=usuario.id,
        )

    except SQLAlchemyError:
        logger.exception("Falha ao consultar ementa institucional.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível consultar a ementa.",
        ) from None

    if ementa is None:
        raise HTTPException(
            status_code=404,
            detail="Ementa não encontrada ou não autorizada.",
        )

    return EmentaInstitucionalDetalheResponse(**ementa)


@app.patch(
    "/api/coordenacao/matriz-disciplinas/{matriz_disciplina_id}/ementas/{ementa_id}",
    response_model=EmentaInstitucionalDetalheResponse,
    tags=["Coordenação - Ementas institucionais"],
)
def atualizar_ementa_institucional(
    matriz_disciplina_id: int,
    ementa_id: int,
    dados: AtualizarEmentaInstitucionalRequest,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(obter_usuario_autenticado)],
) -> EmentaInstitucionalDetalheResponse:

    if usuario.perfil != PerfilUsuario.COORDENADOR:
        raise HTTPException(
            status_code=403,
            detail="Acesso permitido apenas para coordenadores.",
        )

    if usuario.id is None:
        raise HTTPException(
            status_code=401,
            detail="Usuário inválido.",
        )

    repository = SqlAlchemyCatalogoInstitucionalRepository(session)
    caso_de_uso = AtualizarEmentaInstitucional(repository)

    try:
        caso_de_uso.executar(
            DadosAtualizacaoEmenta(
                matriz_disciplina_id=matriz_disciplina_id,
                ementa_id=ementa_id,
                instituicao_id=INSTITUICAO_DESTINO_ID,
                coordenador_usuario_id=usuario.id,
                versao_linha=dados.versao_linha,
                resumo=dados.resumo,
                competencias_habilidades=dados.competencias_habilidades,
                carga_horaria_total=dados.carga_horaria_total,
                carga_horaria_teorica=dados.carga_horaria_teorica,
                carga_horaria_pratica=dados.carga_horaria_pratica,
            )
        )

        # Consulta o resultado dentro da mesma transação.
        ementa_atualizada = repository.buscar_ementa_coordenador(
            matriz_disciplina_id=matriz_disciplina_id,
            ementa_id=ementa_id,
            instituicao_id=INSTITUICAO_DESTINO_ID,
            coordenador_usuario_id=usuario.id,
        )

        if ementa_atualizada is None:
            raise RuntimeError(
                "Ementa não encontrada após a atualização."
            )

        # Valida a resposta antes de confirmar a transação.
        resposta = EmentaInstitucionalDetalheResponse(
            **ementa_atualizada
        )

        session.commit()
        return resposta

    except ErroAtualizacaoEmenta as exc:
        session.rollback()
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except EmentaNaoEncontrada as exc:
        session.rollback()
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ConflitoAtualizacaoEmenta as exc:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except SQLAlchemyError as exc:
        session.rollback()
        logger.exception("Erro ao atualizar ementa institucional.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível salvar a ementa.",
        ) from exc

    except Exception:
        session.rollback()
        logger.exception("Falha inesperada ao atualizar ementa.")
        raise

@app.patch(
    "/api/coordenacao/matriz-disciplinas/"
    "{matriz_disciplina_id}/ementas/{ementa_id}/"
    "objetivos/{objetivo_id}",
    response_model=EmentaInstitucionalDetalheResponse,
    tags=["Coordenação - Ementas institucionais"],
)
def atualizar_texto_objetivo_institucional(
    matriz_disciplina_id: int,
    ementa_id: int,
    objetivo_id: int,
    dados: AtualizarTextoObjetivoRequest,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(obter_usuario_autenticado)],
) -> EmentaInstitucionalDetalheResponse:

    if usuario.perfil != PerfilUsuario.COORDENADOR:
        raise HTTPException(
            status_code=403,
            detail="Acesso permitido apenas para coordenadores.",
        )

    if usuario.id is None:
        raise HTTPException(
            status_code=401,
            detail="Usuário inválido.",
        )

    if min(
        matriz_disciplina_id,
        ementa_id,
        objetivo_id,
    ) <= 0:
        raise HTTPException(
            status_code=422,
            detail="Os identificadores devem ser positivos.",
        )

    texto_objetivo = dados.texto.strip()

    if not texto_objetivo:
        raise HTTPException(
            status_code=422,
            detail="O texto do objetivo não pode estar vazio.",
        )

    repository = SqlAlchemyCatalogoInstitucionalRepository(session)

    try:
        resultado = repository.atualizar_texto_objetivo_coordenador(
            matriz_disciplina_id=matriz_disciplina_id,
            ementa_id=ementa_id,
            objetivo_id=objetivo_id,
            instituicao_id=INSTITUICAO_DESTINO_ID,
            coordenador_usuario_id=usuario.id,
            versao_linha=dados.versao_linha,
            texto_objetivo=texto_objetivo,
        )

        if resultado == "nao_encontrado":
            raise HTTPException(
                status_code=404,
                detail="Objetivo não encontrado ou não autorizado.",
            )

        if resultado == "conflito":
            raise HTTPException(
                status_code=409,
                detail=(
                    "A ementa foi modificada ou não está disponível "
                    "para edição. Atualize a página antes de salvar."
                ),
            )

        if resultado != "atualizado":
            raise RuntimeError(
                "Resultado inesperado ao atualizar objetivo."
            )

        ementa_atualizada = repository.buscar_ementa_coordenador(
            matriz_disciplina_id=matriz_disciplina_id,
            ementa_id=ementa_id,
            instituicao_id=INSTITUICAO_DESTINO_ID,
            coordenador_usuario_id=usuario.id,
        )

        if ementa_atualizada is None:
            raise RuntimeError(
                "Ementa não encontrada após atualizar o objetivo."
            )

        resposta = EmentaInstitucionalDetalheResponse(
            **ementa_atualizada
        )

        session.commit()
        return resposta

    except HTTPException:
        session.rollback()
        raise

    except SQLAlchemyError as exc:
        session.rollback()
        logger.exception("Falha ao atualizar objetivo da ementa.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível atualizar o objetivo.",
        ) from exc

    except Exception:
        session.rollback()
        logger.exception("Erro inesperado ao atualizar objetivo.")
        raise

@app.patch(
    "/api/coordenacao/matriz-disciplinas/"
    "{matriz_disciplina_id}/ementas/{ementa_id}/"
    "conteudos/{conteudo_id}",
    response_model=EmentaInstitucionalDetalheResponse,
    tags=["Coordenação - Ementas institucionais"],
)
def atualizar_texto_conteudo_institucional(
    matriz_disciplina_id: int,
    ementa_id: int,
    conteudo_id: int,
    dados: AtualizarTextoConteudoRequest,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(obter_usuario_autenticado)],
) -> EmentaInstitucionalDetalheResponse:

    if usuario.perfil != PerfilUsuario.COORDENADOR:
        raise HTTPException(
            status_code=403,
            detail="Acesso permitido apenas para coordenadores.",
        )

    if usuario.id is None:
        raise HTTPException(
            status_code=401,
            detail="Usuário inválido.",
        )

    if min(matriz_disciplina_id, ementa_id, conteudo_id) <= 0:
        raise HTTPException(
            status_code=422,
            detail="Os identificadores devem ser positivos.",
        )

    texto_conteudo = dados.texto.strip()

    if not texto_conteudo:
        raise HTTPException(
            status_code=422,
            detail="O texto do conteúdo não pode estar vazio.",
        )

    repository = SqlAlchemyCatalogoInstitucionalRepository(session)

    try:
        resultado = repository.atualizar_texto_conteudo_coordenador(
            matriz_disciplina_id=matriz_disciplina_id,
            ementa_id=ementa_id,
            conteudo_id=conteudo_id,
            instituicao_id=INSTITUICAO_DESTINO_ID,
            coordenador_usuario_id=usuario.id,
            versao_linha=dados.versao_linha,
            texto_conteudo=texto_conteudo,
        )

        if resultado == "nao_encontrado":
            raise HTTPException(
                status_code=404,
                detail="Conteúdo não encontrado ou não autorizado.",
            )

        if resultado == "conflito":
            raise HTTPException(
                status_code=409,
                detail=(
                    "A ementa foi modificada ou não está disponível "
                    "para edição. Atualize a página."
                ),
            )

        if resultado != "atualizado":
            raise RuntimeError(
                "Resultado inesperado ao atualizar conteúdo."
            )

        ementa_atualizada = repository.buscar_ementa_coordenador(
            matriz_disciplina_id=matriz_disciplina_id,
            ementa_id=ementa_id,
            instituicao_id=INSTITUICAO_DESTINO_ID,
            coordenador_usuario_id=usuario.id,
        )

        if ementa_atualizada is None:
            raise RuntimeError(
                "Ementa não encontrada após a atualização."
            )

        resposta = EmentaInstitucionalDetalheResponse(
            **ementa_atualizada
        )

        session.commit()
        return resposta

    except HTTPException:
        session.rollback()
        raise

    except SQLAlchemyError as exc:
        session.rollback()
        logger.exception(
            "Falha ao atualizar conteúdo programático."
        )
        raise HTTPException(
            status_code=503,
            detail="Não foi possível atualizar o conteúdo.",
        ) from exc

    except Exception:
        session.rollback()
        logger.exception(
            "Erro inesperado ao atualizar conteúdo programático."
        )
        raise

@app.patch(
    "/api/coordenacao/matriz-disciplinas/"
    "{matriz_disciplina_id}/ementas/{ementa_id}/"
    "bibliografias/{bibliografia_id}",
    response_model=EmentaInstitucionalDetalheResponse,
    tags=["Coordenação - Ementas institucionais"],
)
def atualizar_texto_bibliografia_institucional(
    matriz_disciplina_id: int,
    ementa_id: int,
    bibliografia_id: int,
    dados: AtualizarTextoBibliografiaRequest,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(obter_usuario_autenticado)],
) -> EmentaInstitucionalDetalheResponse:

    if usuario.perfil != PerfilUsuario.COORDENADOR:
        raise HTTPException(
            status_code=403,
            detail="Acesso permitido apenas para coordenadores.",
        )

    if usuario.id is None:
        raise HTTPException(
            status_code=401,
            detail="Usuário inválido.",
        )

    if min(matriz_disciplina_id, ementa_id, bibliografia_id) <= 0:
        raise HTTPException(
            status_code=422,
            detail="Os identificadores devem ser positivos.",
        )

    texto_bibliografia = dados.texto.strip()

    if not texto_bibliografia:
        raise HTTPException(
            status_code=422,
            detail="O texto da bibliografia não pode estar vazio.",
        )

    repository = SqlAlchemyCatalogoInstitucionalRepository(session)

    try:
        resultado = repository.atualizar_texto_bibliografia_coordenador(
            matriz_disciplina_id=matriz_disciplina_id,
            ementa_id=ementa_id,
            bibliografia_id=bibliografia_id,
            instituicao_id=INSTITUICAO_DESTINO_ID,
            coordenador_usuario_id=usuario.id,
            versao_linha=dados.versao_linha,
            texto_bibliografia=texto_bibliografia,
        )

        if resultado == "nao_encontrado":
            raise HTTPException(
                status_code=404,
                detail="Bibliografia não encontrada ou não autorizada.",
            )

        if resultado == "conflito":
            raise HTTPException(
                status_code=409,
                detail=(
                    "A ementa foi modificada ou não está disponível "
                    "para edição. Atualize a página."
                ),
            )

        if resultado != "atualizado":
            raise RuntimeError(
                "Resultado inesperado ao atualizar bibliografia."
            )

        ementa_atualizada = repository.buscar_ementa_coordenador(
            matriz_disciplina_id=matriz_disciplina_id,
            ementa_id=ementa_id,
            instituicao_id=INSTITUICAO_DESTINO_ID,
            coordenador_usuario_id=usuario.id,
        )

        if ementa_atualizada is None:
            raise RuntimeError(
                "Ementa não encontrada após atualizar a bibliografia."
            )

        resposta = EmentaInstitucionalDetalheResponse(
            **ementa_atualizada
        )

        session.commit()
        return resposta

    except HTTPException:
        session.rollback()
        raise

    except SQLAlchemyError as exc:
        session.rollback()
        logger.exception("Falha ao atualizar bibliografia.")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível atualizar a bibliografia.",
        ) from exc

    except Exception:
        session.rollback()
        logger.exception("Erro inesperado ao atualizar bibliografia.")
        raise
