
const API_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function consultar(caminho) {
  let resposta

  try {
    resposta = await fetch(`${API_URL}${caminho}`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    })
  } catch {
    throw new Error('Não foi possível conectar ao servidor.')
  }

  const dados = await resposta.json().catch(() => null)

  if (!resposta.ok) {
    if (resposta.status === 401) {
      throw new Error('Sessão expirada. Faça login novamente.')
    }

    if (resposta.status === 403) {
      throw new Error('Você não possui permissão para esta consulta.')
    }

    if (resposta.status === 404) {
      throw new Error('Curso ou matriz não encontrado ou não autorizado.')
    }

    throw new Error(
      typeof dados?.detail === 'string'
        ? dados.detail
        : 'Não foi possível consultar os dados institucionais.'
    )
  }

  return dados
}

export function listarCursosCoordenador() {
  return consultar('/api/coordenacao/cursos')
}

export function listarMatrizesCoordenador(cursoId) {
  return consultar(
    `/api/coordenacao/cursos/${encodeURIComponent(cursoId)}/matrizes`
  )
}

export function listarDisciplinasMatriz(matrizId) {
  return consultar(
    `/api/coordenacao/matrizes/${encodeURIComponent(matrizId)}/disciplinas`
  )
}

export function buscarEmentaInstitucional(matrizDisciplinaId, ementaId) {
  return consultar(
    `/api/coordenacao/matriz-disciplinas/` +
      `${encodeURIComponent(matrizDisciplinaId)}/ementas/` +
      `${encodeURIComponent(ementaId)}`
  )
}

export async function atualizarEmentaInstitucional(
  matrizDisciplinaId,
  ementaId,
  dados
) {
  const resposta = await fetch(
    `${API_URL}/api/coordenacao/matriz-disciplinas/` +
      `${encodeURIComponent(matrizDisciplinaId)}/ementas/` +
      `${encodeURIComponent(ementaId)}`,
    {
      method: 'PATCH',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(dados),
    }
  )

  if (!resposta.ok) {
    let mensagem = `Erro HTTP ${resposta.status}`

    try {
      const erro = await resposta.json()

      if (typeof erro.detail === 'string') {
        mensagem = erro.detail
      } else if (Array.isArray(erro.detail)) {
        mensagem = erro.detail
          .map((item) => item.msg || 'Campo inválido')
          .join('; ')
      }
    } catch {
      // Mantém a mensagem HTTP caso a resposta não seja JSON.
    }

    const excecao = new Error(mensagem)
    excecao.status = resposta.status
    throw excecao
  }

  return resposta.json()
}

export async function atualizarObjetivoInstitucional(
  matrizDisciplinaId,
  ementaId,
  objetivoId,
  dados
) {
  const resposta = await fetch(
    `${API_URL}/api/coordenacao/matriz-disciplinas/` +
      `${encodeURIComponent(matrizDisciplinaId)}/ementas/` +
      `${encodeURIComponent(ementaId)}/objetivos/` +
      `${encodeURIComponent(objetivoId)}`,
    {
      method: 'PATCH',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(dados),
    }
  )

  if (!resposta.ok) {
    let mensagem = `Erro HTTP ${resposta.status}`

    try {
      const erro = await resposta.json()

      if (typeof erro.detail === 'string') {
        mensagem = erro.detail
      } else if (Array.isArray(erro.detail)) {
        mensagem = erro.detail
          .map((item) => item.msg || 'Campo inválido')
          .join('; ')
      }
    } catch {
      // Mantém o erro HTTP se a resposta não for JSON.
    }

    const excecao = new Error(mensagem)
    excecao.status = resposta.status
    throw excecao
  }

  return resposta.json()
}

export async function atualizarConteudoInstitucional(
  matrizDisciplinaId,
  ementaId,
  conteudoId,
  dados
) {
  const resposta = await fetch(
    `${API_URL}/api/coordenacao/matriz-disciplinas/` +
      `${encodeURIComponent(matrizDisciplinaId)}/ementas/` +
      `${encodeURIComponent(ementaId)}/conteudos/` +
      `${encodeURIComponent(conteudoId)}`,
    {
      method: 'PATCH',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(dados),
    }
  )

  if (!resposta.ok) {
    let mensagem = `Erro HTTP ${resposta.status}`

    try {
      const erro = await resposta.json()

      if (typeof erro.detail === 'string') {
        mensagem = erro.detail
      } else if (Array.isArray(erro.detail)) {
        mensagem = erro.detail
          .map((item) => item.msg || 'Campo inválido')
          .join('; ')
      }
    } catch {
      // Mantém a mensagem HTTP se não houver JSON válido.
    }

    const excecao = new Error(mensagem)
    excecao.status = resposta.status
    throw excecao
  }

  return resposta.json()
}

export async function atualizarBibliografiaInstitucional(
  matrizDisciplinaId,
  ementaId,
  bibliografiaId,
  dados
) {
  const resposta = await fetch(
    `${API_URL}/api/coordenacao/matriz-disciplinas/` +
      `${encodeURIComponent(matrizDisciplinaId)}/ementas/` +
      `${encodeURIComponent(ementaId)}/bibliografias/` +
      `${encodeURIComponent(bibliografiaId)}`,
    {
      method: 'PATCH',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(dados),
    }
  )

  if (!resposta.ok) {
    let mensagem = `Erro HTTP ${resposta.status}`

    try {
      const erro = await resposta.json()

      if (typeof erro.detail === 'string') {
        mensagem = erro.detail
      } else if (Array.isArray(erro.detail)) {
        mensagem = erro.detail
          .map((item) => item.msg || 'Campo inválido')
          .join('; ')
      }
    } catch {
      // Mantém a mensagem HTTP.
    }

    const excecao = new Error(mensagem)
    excecao.status = resposta.status
    throw excecao
  }

  return resposta.json()
}
