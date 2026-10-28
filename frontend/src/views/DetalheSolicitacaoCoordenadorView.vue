<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { buscarSolicitacaoCoordenacao } from '../services/coordenacao'

const route = useRoute()

const solicitacao = ref(null)
const carregando = ref(true)
const erro = ref('')

function formatarData(valor) {
    if (!valor) return 'Não informada'

    // Exibe a data registrada sem deslocamentos de fuso horário.
    const partes = valor.slice(0, 10).split('-')

    if (partes.length !== 3) return valor

    const [ano, mes, dia] = partes
    return `${dia}/${mes}/${ano}`
}

function formatarTamanho(bytes) {
    if (bytes === null || bytes === undefined) {
        return 'Não informado'
    }

    if (bytes < 1024) return `${bytes} bytes`

    if (bytes < 1024 * 1024) {
        return `${(bytes / 1024).toLocaleString('pt-BR', {
            maximumFractionDigits: 1,
        })} KB`
    }

    return `${(bytes / (1024 * 1024)).toLocaleString('pt-BR', {
        maximumFractionDigits: 2,
    })} MB`
}

function formatarStatus(status) {
    if (!status) return 'Não informado'

    const nomes = {
        RECEBIDA: 'Recebida',
        EM_ANALISE: 'Em análise',
        CONCLUIDA: 'Concluída',
        PROCESSADO: 'Processado',
        RECEBIDO: 'Recebido',
        FALHA: 'Falha',
    }

    return nomes[status] || status.replaceAll('_', ' ')
}

async function carregarDetalhes() {
    carregando.value = true
    erro.value = ''
    solicitacao.value = null

    try {
        solicitacao.value = await buscarSolicitacaoCoordenacao(
            String(route.params.protocolo || '')
        )
    } catch (excecao) {
        erro.value =
            excecao.message || 'Não foi possível carregar os detalhes.'
    } finally {
        carregando.value = false
    }
}

onMounted(carregarDetalhes)

watch(
    () => route.params.protocolo,
    () => carregarDetalhes()
)


function visualizarPDF(documentoId) {
    const protocolo = String(route.params.protocolo || '')

    if (!protocolo || !documentoId) return

    const apiUrl =
        import.meta.env.VITE_API_URL || 'http://localhost:8000'

    const url =
        `${apiUrl}/api/coordenacao/solicitacoes/` +
        `${encodeURIComponent(protocolo)}/documentos/` +
        `${documentoId}/arquivo`

    window.open(url, '_blank', 'noopener,noreferrer')
}
</script>

<template>
    <main class="pagina">
        <RouterLink to="/coordenacao/solicitacoes" class="voltar">
            ← Voltar às solicitações
        </RouterLink>

        <div class="cabecalho">
            <div>
                <span class="subtitulo">ÁREA DA COORDENAÇÃO</span>
                <h1>Detalhes da solicitação</h1>
                <p>
                    Consulte as informações e os documentos enviados
                    pelo candidato.
                </p>
            </div>

            <button class="atualizar" type="button" :disabled="carregando" @click="carregarDetalhes">
                {{ carregando ? 'Carregando...' : 'Atualizar' }}
            </button>
        </div>

        <section v-if="carregando" class="mensagem">
            Carregando informações da solicitação...
        </section>

        <section v-else-if="erro" class="mensagem erro" role="alert">
            <h2>Não foi possível consultar a solicitação</h2>
            <p>{{ erro }}</p>
            <button type="button" @click="carregarDetalhes">
                Tentar novamente
            </button>
        </section>

        <template v-else-if="solicitacao">
            <section class="cartao">
                <div class="secao-topo">
                    <div>
                        <span class="rotulo">SOLICITAÇÃO</span>
                        <h2>Processo #{{ solicitacao.solicitacao_id }}</h2>
                    </div>

                    <span class="status">
                        {{ formatarStatus(solicitacao.status) }}
                    </span>
                </div>

                <div class="informacoes">
                    <div class="campo campo-largo">
                        <span class="rotulo">PROTOCOLO</span>
                        <p class="protocolo">{{ solicitacao.protocolo }}</p>
                    </div>

                    <div class="campo">
                        <span class="rotulo">CURSO DE DESTINO</span>
                        <p>{{ solicitacao.curso_destino }}</p>
                    </div>

                    <div class="campo">
                        <span class="rotulo">DATA DE ENVIO</span>
                        <p>{{ formatarData(solicitacao.criado_em) }}</p>
                    </div>

                    <div class="campo">
                        <span class="rotulo">QUANTIDADE DE DOCUMENTOS</span>
                        <p>{{ solicitacao.quantidade_documentos }}</p>
                    </div>
                </div>
            </section>

            <section class="cartao">
                <div class="secao-topo">
                    <div>
                        <span class="rotulo">ARQUIVOS ENVIADOS</span>
                        <h2>Documentos da solicitação</h2>
                    </div>

                    <span class="contador">
                        {{ solicitacao.documentos.length }}
                        arquivo(s)
                    </span>
                </div>

                <div v-if="solicitacao.documentos.length === 0" class="vazio">
                    Nenhum documento vinculado a esta solicitação.
                </div>

                <div v-else class="documentos">
                    <article v-for="documento in solicitacao.documentos" :key="documento.documento_id"
                        class="documento">
                        <div class="documento-topo">
                            <div class="icone-pdf">PDF</div>

                            <div class="documento-identificacao">
                                <h3>{{ documento.nome_arquivo }}</h3>
                                <span>
                                    Documento #{{ documento.documento_id }}
                                </span>
                            </div>

                            <span class="status-documento">
                                {{ formatarStatus(documento.status_documento) }}
                            </span>
                        </div>

                        <div class="documento-info">
                            <div>
                                <span class="rotulo">PÁGINAS</span>
                                <p>
                                    {{ documento.quantidade_paginas ?? 'Não informado' }}
                                </p>
                            </div>

                            <div class="documento-acoes">
                                <button type="button" class="botao-pdf" @click="visualizarPDF(documento.documento_id)">
                                    Visualizar PDF ↗
                                </button>
                            </div>

                            <div>
                                <span class="rotulo">TAMANHO</span>
                                <p>{{ formatarTamanho(documento.tamanho_bytes) }}</p>
                            </div>
                        </div>
                    </article>
                </div>

            </section>

            <section class="cartao proxima-etapa">
                <span class="rotulo">PRÓXIMA FUNCIONALIDADE</span>
                <h2>Análise de equivalência</h2>
                <p>
                    Aqui serão exibidas as disciplinas identificadas
                    nos documentos e as sugestões de equivalência
                    com a matriz curricular institucional.
                </p>

                <span class="em-desenvolvimento">
                    Em desenvolvimento
                </span>
            </section>
        </template>
    </main>
</template>

<style scoped>
.pagina {
    max-width: 1100px;
    margin: 40px auto;
    padding: 20px;
}

.voltar {
    display: inline-block;
    margin-bottom: 28px;
    color: #24548d;
    text-decoration: none;
    font-size: 14px;
    font-weight: 600;
}

.voltar:hover {
    text-decoration: underline;
}

.cabecalho,
.secao-topo,
.documento-topo {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;
}

.cabecalho {
    margin-bottom: 28px;
}

.subtitulo,
.rotulo {
    color: #6380a3;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}

h1 {
    font-size: 30px;
    margin: 12px 0;
    color: #16345b;
}

.cabecalho p,
.proxima-etapa p {
    color: #64748b;
    line-height: 1.7;
}

.atualizar {
    padding: 12px 18px;
    background: #1e477b;
    color: white;
    border: none;
    border-radius: 9px;
    cursor: pointer;
}

.atualizar:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.cartao {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 28px;
    margin-bottom: 22px;
}

h2 {
    color: #16345b;
    font-size: 21px;
    margin: 9px 0 0;
}

.status {
    padding: 8px 14px;
    border-radius: 30px;
    background: #eaf1fc;
    color: #24548d;
    font-size: 12px;
    font-weight: 600;
}

.informacoes {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-top: 28px;
}

.campo-largo {
    grid-column: 1 / -1;
}

.campo p,
.documento-info p {
    margin: 8px 0 0;
    color: #34465e;
    font-size: 14px;
}

.protocolo {
    overflow-wrap: anywhere;
}

.contador {
    font-size: 13px;
    color: #64748b;
}

.documentos {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-top: 26px;
}

.documento {
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 22px;
}

.documento-topo {
    justify-content: flex-start;
    align-items: center;
}

.icone-pdf {
    background: #feecec;
    color: #a33e3e;
    border-radius: 10px;
    padding: 12px 10px;
    font-size: 13px;
    font-weight: 800;
}

.documento-identificacao {
    flex: 1;
    min-width: 0;
}

.documento-identificacao h3 {
    margin: 0 0 7px;
    font-size: 16px;
    color: #16345b;
    overflow-wrap: anywhere;
}

.documento-identificacao span {
    color: #64748b;
    font-size: 12px;
}

.status-documento {
    background: #eaf7ef;
    color: #22633e;
    font-size: 12px;
    font-weight: 600;
    padding: 7px 12px;
    border-radius: 25px;
}

.documento-info {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
    margin-top: 20px;
    padding-top: 18px;
    border-top: 1px solid #edf0f5;
}

.aviso,
.vazio {
    color: #64748b;
    font-size: 13px;
    line-height: 1.6;
}

.aviso {
    margin: 22px 0 0;
}

.vazio {
    margin-top: 22px;
}

.proxima-etapa {
    background: #f7faff;
}

.em-desenvolvimento {
    display: inline-block;
    margin-top: 12px;
    font-size: 12px;
    font-weight: 600;
    color: #527197;
}

.mensagem {
    text-align: center;
    padding: 48px 24px;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 15px;
    color: #64748b;
}

.mensagem.erro {
    color: #922f2f;
    background: #fff5f5;
}

.mensagem button {
    margin-top: 14px;
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    background: #1e477b;
    color: white;
    cursor: pointer;
}

@media (max-width: 600px) {

    .cabecalho,
    .secao-topo,
    .documento-topo {
        flex-direction: column;
    }

    .informacoes,
    .documento-info {
        grid-template-columns: 1fr;
    }

    h1 {
        font-size: 25px;
    }
}

.documento-acoes {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
}

.botao-pdf {
    border: none;
    border-radius: 9px;
    padding: 11px 18px;
    background: #1e477b;
    color: white;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
}

.botao-pdf:hover {
    background: #16345b;
}
</style>
