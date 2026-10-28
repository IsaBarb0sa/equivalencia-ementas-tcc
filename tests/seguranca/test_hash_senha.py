
from equivalencia_ementas.seguranca.infrastructure.security.hash_senha import (
    HashSenha,
)


def test_gerar_hash():
    servico = HashSenha()

    resultado = servico.gerar("SenhaSegura@2026")

    assert resultado.startswith("$argon2id$")
    assert resultado != "SenhaSegura@2026"


def test_verificar_senha_correta():
    servico = HashSenha()

    senha_hash = servico.gerar("SenhaSegura@2026")

    assert servico.verificar("SenhaSegura@2026", senha_hash)


def test_rejeitar_senha_incorreta():
    servico = HashSenha()

    senha_hash = servico.gerar("SenhaSegura@2026")

    assert not servico.verificar("SenhaErrada", senha_hash)


def test_hashes_diferentes_para_mesma_senha():
    servico = HashSenha()

    primeiro = servico.gerar("SenhaSegura@2026")
    segundo = servico.gerar("SenhaSegura@2026")

    assert primeiro != segundo


def test_rejeitar_hash_invalido():
    servico = HashSenha()

    assert not servico.verificar("SenhaSegura@2026", "hash_invalido")


def test_hash_nao_precisa_atualizar():
    servico = HashSenha()

    senha_hash = servico.gerar("SenhaSegura@2026")

    assert not servico.precisa_atualizar(senha_hash)
