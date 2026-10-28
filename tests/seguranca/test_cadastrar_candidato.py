
import pytest

from equivalencia_ementas.seguranca.application.use_cases.cadastrar_candidato import (
    CadastrarCandidato,
    DadosCadastroCandidato,
    ErroCadastro,
)
from equivalencia_ementas.seguranca.domain.entities.usuario import (
    PerfilUsuario,
)


class RepositorioFake:
    def __init__(self):
        self.usuarios = []

    def buscar_por_email(self, email):
        return next(
            (u for u in self.usuarios if u.email == email),
            None,
        )

    def buscar_por_cpf(self, cpf):
        return next(
            (u for u in self.usuarios if u.cpf == cpf),
            None,
        )

    def criar(self, usuario):
        self.usuarios.append(usuario)
        return len(self.usuarios)


class HashFake:
    def gerar(self, senha):
        return f"hash_teste_{len(senha)}"


def dados_validos(**alteracoes):
    dados = {
        "nome_completo": "Candidata Exemplo",
        "cpf": "529.982.247-25",
        "email": "CANDIDATA@EXEMPLO.COM",
        "senha": "SenhaSegura@2026",
    }
    dados.update(alteracoes)
    return DadosCadastroCandidato(**dados)


@pytest.fixture
def ambiente():
    repository = RepositorioFake()
    caso_de_uso = CadastrarCandidato(repository, HashFake())
    return repository, caso_de_uso


def test_cadastrar_candidato(ambiente):
    repository, caso_de_uso = ambiente

    resultado = caso_de_uso.executar(dados_validos())

    assert resultado.usuario_id == 1
    assert resultado.email == "candidata@exemplo.com"
    assert len(repository.usuarios) == 1

    usuario = repository.usuarios[0]
    assert usuario.cpf == "52998224725"
    assert usuario.perfil == PerfilUsuario.CANDIDATO
    assert usuario.senha_hash != "SenhaSegura@2026"
    assert usuario.email_verificado is False


def test_rejeitar_cpf_invalido(ambiente):
    repository, caso_de_uso = ambiente

    with pytest.raises(ErroCadastro, match="CPF"):
        caso_de_uso.executar(
            dados_validos(cpf="123.456.789-00")
        )

    assert repository.usuarios == []


def test_rejeitar_email_invalido(ambiente):
    _, caso_de_uso = ambiente

    with pytest.raises(ErroCadastro, match="e-mail"):
        caso_de_uso.executar(
            dados_validos(email="email-invalido")
        )


def test_rejeitar_senha_curta(ambiente):
    _, caso_de_uso = ambiente

    with pytest.raises(ErroCadastro, match="senha"):
        caso_de_uso.executar(
            dados_validos(senha="123456")
        )


def test_rejeitar_email_duplicado(ambiente):
    _, caso_de_uso = ambiente

    caso_de_uso.executar(dados_validos())

    with pytest.raises(ErroCadastro, match="e-mail"):
        caso_de_uso.executar(dados_validos())


def test_rejeitar_cpf_duplicado(ambiente):
    _, caso_de_uso = ambiente

    caso_de_uso.executar(dados_validos())

    with pytest.raises(ErroCadastro, match="CPF"):
        caso_de_uso.executar(
            dados_validos(email="outro@exemplo.com")
        )


def test_normalizar_nome_e_email(ambiente):
    repository, caso_de_uso = ambiente

    caso_de_uso.executar(
        dados_validos(
            nome_completo="  Candidata   Exemplo  ",
            email="  TESTE@EXEMPLO.COM  ",
        )
    )

    usuario = repository.usuarios[0]
    assert usuario.nome_completo == "Candidata Exemplo"
    assert usuario.email == "teste@exemplo.com"


def test_rejeitar_nome_invalido(ambiente):
    _, caso_de_uso = ambiente

    with pytest.raises(ErroCadastro, match="nome"):
        caso_de_uso.executar(
            dados_validos(nome_completo="A")
        )


def test_rejeitar_senha_com_controle(ambiente):
    _, caso_de_uso = ambiente

    with pytest.raises(ErroCadastro, match="controle"):
        caso_de_uso.executar(
            dados_validos(senha="SenhaSegura\n2026")
        )
