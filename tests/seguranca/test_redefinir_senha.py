
import pytest

from equivalencia_ementas.seguranca.application.use_cases.redefinir_senha import (
    DadosRedefinicaoSenha,
    ErroRedefinicaoSenha,
    RedefinirSenha,
)

from equivalencia_ementas.seguranca.infrastructure.security.gerenciador_recuperacao_senha import (
    GerenciadorRecuperacaoSenha,
)


class RecuperacaoFake:
    def __init__(self, usuario_id=1):
        self.usuario_id = usuario_id
        self.tokens_consumidos = []
        self.usuarios_invalidados = []

    def consumir(self, token_hash):
        self.tokens_consumidos.append(token_hash)
        return self.usuario_id

    def invalidar_pendentes(self, usuario_id):
        self.usuarios_invalidados.append(usuario_id)


class UsuarioFake:
    def __init__(self, atualizado=True):
        self.atualizado = atualizado
        self.chamadas = []

    def atualizar_senha(self, usuario_id, senha_hash):
        self.chamadas.append((usuario_id, senha_hash))
        return self.atualizado


class SessaoFake:
    def __init__(self):
        self.revogados = []

    def revogar_todas_do_usuario(self, usuario_id):
        self.revogados.append(usuario_id)


class HashSenhaFake:
    def gerar(self, senha):
        return f"hash-de-teste:{senha}"


def preparar(usuario_id=1, atualizado=True):
    recuperacao = RecuperacaoFake(usuario_id)
    usuario = UsuarioFake(atualizado)
    sessao = SessaoFake()

    caso_de_uso = RedefinirSenha(
        recuperacao,
        usuario,
        sessao,
        HashSenhaFake(),
    )

    return caso_de_uso, recuperacao, usuario, sessao


def test_redefine_senha_com_token_valido():
    caso, recuperacao, usuario, sessao = preparar()
    token = GerenciadorRecuperacaoSenha.gerar().token

    caso.executar(
        DadosRedefinicaoSenha(
            token=token,
            nova_senha="NovaSenhaSegura@2026",
        )
    )

    assert len(usuario.chamadas) == 1
    assert usuario.chamadas[0][0] == 1
    assert recuperacao.usuarios_invalidados == [1]
    assert sessao.revogados == [1]


def test_rejeita_token_invalido():
    caso, recuperacao, usuario, sessao = preparar()

    with pytest.raises(ErroRedefinicaoSenha):
        caso.executar(
            DadosRedefinicaoSenha(
                token="token-invalido",
                nova_senha="NovaSenhaSegura@2026",
            )
        )

    assert usuario.chamadas == []
    assert sessao.revogados == []


def test_rejeita_senha_curta():
    caso, recuperacao, usuario, sessao = preparar()
    token = GerenciadorRecuperacaoSenha.gerar().token

    with pytest.raises(ErroRedefinicaoSenha):
        caso.executar(
            DadosRedefinicaoSenha(
                token=token,
                nova_senha="curta",
            )
        )

    assert recuperacao.tokens_consumidos == []


def test_rejeita_token_expirado_ou_consumido():
    caso, recuperacao, usuario, sessao = preparar(
        usuario_id=None
    )
    token = GerenciadorRecuperacaoSenha.gerar().token

    with pytest.raises(ErroRedefinicaoSenha):
        caso.executar(
            DadosRedefinicaoSenha(
                token=token,
                nova_senha="NovaSenhaSegura@2026",
            )
        )

    assert usuario.chamadas == []
    assert sessao.revogados == []


def test_nao_revoga_sessoes_se_usuario_nao_for_atualizado():
    caso, recuperacao, usuario, sessao = preparar(
        atualizado=False
    )
    token = GerenciadorRecuperacaoSenha.gerar().token

    with pytest.raises(ErroRedefinicaoSenha):
        caso.executar(
            DadosRedefinicaoSenha(
                token=token,
                nova_senha="NovaSenhaSegura@2026",
            )
        )

    assert sessao.revogados == []
