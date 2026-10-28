
const API_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function listarSolicitacoesCoordenacao(limite = 50) {
  let resposta

  try {
    resposta = await fetch(
      `${API_URL}/api/coordenacao/solicitacoes?limite=${limite}`,
      {
        method: 'GET',
        credentials: 'include',
        headers: {
          Accept: 'application/json',
        },
      }
    )
  } catch {
    throw new Error(
      'Não foi possível conectar ao servidor.'
    )
  }

  const dados = await resposta.json().catch(() => null)

  if (!resposta.ok) {
    throw new Error(
      typeof dados?.detail === 'string'
        ? dados.detail
        : 'Não foi possível consultar as solicitações.'
    )
  }

  return dados
}


export async function buscarSolicitacaoCoordenacao(protocolo) {
  if (!protocolo || !protocolo.trim()) {
    throw new Error('O protocolo deve ser informado.')
  }

  let resposta

  try {
    resposta = await fetch(
      `${API_URL}/api/coordenacao/solicitacoes/${encodeURIComponent(protocolo.trim())}`,
      {
        method: 'GET',
        credentials: 'include',
        headers: {
          Accept: 'application/json',
        },
      }
    )
  } catch {
    throw new Error('Não foi possível conectar ao servidor.')
  }

  const dados = await resposta.json().catch(() => null)

  if (!resposta.ok) {
    if (resposta.status === 401) {
      throw new Error('Sua sessão expirou. Faça login novamente.')
    }

    if (resposta.status === 403) {
      throw new Error('Você não tem permissão para consultar esta solicitação.')
    }

    if (resposta.status === 404) {
      throw new Error('Solicitação não encontrada ou não autorizada.')
    }

    throw new Error(
      typeof dados?.detail === 'string'
        ? dados.detail
        : 'Não foi possível consultar os detalhes da solicitação.'
    )
  }

  return dados
}
