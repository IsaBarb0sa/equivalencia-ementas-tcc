
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function criarSolicitacao(cursoId, arquivos) {
    const dados = new FormData()
    dados.append('curso_id', String(cursoId))

    for (const arquivo of arquivos) {
        dados.append('arquivos', arquivo)
    }

    let resposta

    try {
        resposta = await fetch(`${API_URL}/api/solicitacoes`, {
            method: 'POST',
            credentials: 'include',
            body: dados,
        })
    } catch {
        throw new Error(
            'Não foi possível conectar à API. Verifique se o servidor está ligado.'
        )
    }

    const dadosResposta = await resposta.json().catch(() => null)

    if (!resposta.ok) {
        const detalhe = dadosResposta?.detail
        let mensagem = 'Falha ao enviar a solicitação.'

        if (typeof detalhe === 'string') {
            mensagem = detalhe
        } else if (Array.isArray(detalhe)) {
            mensagem = detalhe
                .map((item) => item.msg || 'Erro de validação')
                .join('; ')
        }

        throw new Error(mensagem)
    }

    return dadosResposta
}
