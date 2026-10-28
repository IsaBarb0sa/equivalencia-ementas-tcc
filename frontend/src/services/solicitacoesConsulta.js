
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function consultarApi(caminho) {
    let resposta

    try {
        resposta = await fetch(`${API_URL}${caminho}`, {
            credentials: 'include',
            headers: {
                Accept: 'application/json',
            },
        })
    } catch {
        throw new Error(
            'Não foi possível conectar à API. Verifique se o servidor está ligado.'
        )
    }

    const dados = await resposta.json().catch(() => null)

    if (!resposta.ok) {
        const detalhe = dados?.detail

        throw new Error(
            typeof detalhe === 'string'
                ? detalhe
                : `Erro ao consultar a API (${resposta.status}).`
        )
    }

    return dados
}

export function listarSolicitacoes(limite = 50) {
    return consultarApi(`/api/solicitacoes?limite=${limite}`)
}

export function buscarSolicitacao(protocolo) {
    return consultarApi(
        `/api/solicitacoes/${encodeURIComponent(protocolo)}`
    )
}
