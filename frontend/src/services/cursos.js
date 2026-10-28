const API_URL = (
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
).replace(/\/+$/, '')

export async function listarCursos() {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 15000)

  try {
    const resposta = await fetch(`${API_URL}/api/cursos`, {
      headers: {
        Accept: 'application/json',
      },
      signal: controller.signal,
    })

    if (!resposta.ok) {
      throw new Error('Não foi possível carregar os cursos. Tente novamente.')
    }

    const dados = await resposta.json()

    if (
      !Array.isArray(dados) ||
      !dados.every(
        (curso) => Number.isInteger(curso.id) && typeof curso.nome === 'string',
      )
    ) {
      throw new Error('A API retornou uma lista de cursos inválida.')
    }

    return dados
  } catch (erro) {
    if (erro.name === 'AbortError') {
      throw new Error('A consulta demorou demais. Tente novamente.')
    }

    if (erro instanceof TypeError) {
      throw new Error('Não foi possível conectar à API. Confira se o backend está rodando.')
    }

    throw erro
  } finally {
    clearTimeout(timeout)
  }
}