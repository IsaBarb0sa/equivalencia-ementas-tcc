
const API_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function requisicao(caminho, opcoes = {}) {
  let resposta

  try {
    resposta = await fetch(`${API_URL}${caminho}`, {
      ...opcoes,
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        ...opcoes.headers,
      },
    })
  } catch {
    throw new Error(
      'Não foi possível conectar ao servidor. Verifique se a API está ligada.'
    )
  }

  const dados = await resposta.json().catch(() => null)

  if (!resposta.ok) {
    const mensagem =
      typeof dados?.detail === 'string'
        ? dados.detail
        : 'Não foi possível realizar a operação.'

    const erro = new Error(mensagem)
    erro.status = resposta.status
    throw erro
  }

  return dados
}

export function entrar(identificador, senha) {
  return requisicao('/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ identificador, senha }),
  })
}

export function obterUsuarioAtual() {
  return requisicao('/api/auth/me')
}

export function sair() {
  return requisicao('/api/auth/logout', {
    method: 'POST',
  })
}


export function cadastrarCandidato(dados) {
  return requisicao('/api/auth/cadastro', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      nome_completo: dados.nome_completo,
      cpf: dados.cpf,
      email: dados.email,
      senha: dados.senha,
    }),
  })
}
