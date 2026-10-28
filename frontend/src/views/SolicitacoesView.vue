<script setup>
import { onMounted, ref } from 'vue'
import {
    listarSolicitacoes,
    buscarSolicitacao,
} from '../services/solicitacoesConsulta'

const solicitacoes = ref([])
const carregando = ref(true)
const erro = ref('')

const selecionada = ref(null)
const carregandoDetalhes = ref(false)
const erroDetalhes = ref('')

async function carregarSolicitacoes() {
    carregando.value = true
    erro.value = ''

    try {
        solicitacoes.value = await listarSolicitacoes()
    } catch (excecao) {
        erro.value = excecao.message || 'Erro ao carregar solicitações.'
    } finally {
        carregando.value = false
    }
}

async function verDetalhes(protocolo) {
    selecionada.value = null
    erroDetalhes.value = ''
    carregandoDetalhes.value = true

    try {
        selecionada.value = await buscarSolicitacao(protocolo)
    } catch (excecao) {
        erroDetalhes.value =
            excecao.message || 'Erro ao consultar a solicitação.'
    } finally {
        carregandoDetalhes.value = false
    }
}

function fecharDetalhes() {
    selecionada.value = null
    erroDetalhes.value = ''
}

function formatarData(valor) {
    if (!valor) return 'Data não informada'

    // A API retorna datetime do SQL Server sem fuso horário.
    // Não presumimos UTC nem convertemos o horário.
    const [data, horario = ''] = valor.split('T')
    const partes = data.split('-')

    if (partes.length !== 3) return valor

    const [ano, mes, dia] = partes

    return `${dia}/${mes}/${ano} ${horario.slice(0, 5)}`.trim()
}

function formatarTamanho(bytes) {
    if (bytes == null) return 'Tamanho não informado'

    if (bytes < 1024 * 1024) {
        return `${(bytes / 1024).toFixed(1)} KB`
    }

    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function nomeStatus(status) {
    return (status || 'DESCONHECIDO')
        .replaceAll('_', ' ')
}

function classeStatus(status) {
    switch (status) {
        case 'RECEBIDA':
            return 'status-recebida'
        case 'EM_PROCESSAMENTO':
        case 'PROCESSANDO':
            return 'status-processamento'
        case 'CONCLUIDA':
        case 'CONCLUÍDA':
            return 'status-concluida'
        case 'ERRO':
        case 'FALHA':
            return 'status-erro'
        default:
            return 'status-neutro'
    }
}

onMounted(carregarSolicitacoes)
</script>

<template>
    <section class="pagina">
        <div class="cabecalho">
            <div class="intro">
                <span class="eyebrow">APROVEITAMENTO DE ESTUDOS</span>
                <h1>Acompanhamento de solicitações</h1>
                <p>
                    Consulte as solicitações registradas, seus protocolos
                    e os documentos recebidos.
                </p>
            </div>

            <button type="button" class="secondary-button" :disabled="carregando" @click="carregarSolicitacoes">
                {{ carregando ? 'Atualizando...' : 'Atualizar lista' }}
            </button>
        </div>

        <div class="card painel">
            <div class="painel-cabecalho">
                <div>
                    <h2>Solicitações registradas</h2>
                    <p>Exibindo até 50 solicitações recentes.</p>
                </div>

                <span v-if="!carregando && !erro" class="contador">
                    {{ solicitacoes.length }} registro(s)
                </span>
            </div>

            <div v-if="carregando" class="estado">
                <span class="spinner"></span>
                <p>Carregando solicitações...</p>
            </div>

            <div v-else-if="erro" class="error-box" role="alert">
                <strong>Não foi possível carregar as solicitações.</strong>
                <p>{{ erro }}</p>
                <button type="button" class="secondary-button" @click="carregarSolicitacoes">
                    Tentar novamente
                </button>
            </div>

            <div v-else-if="solicitacoes.length === 0" class="estado">
                <div class="icone-vazio">📄</div>
                <h3>Nenhuma solicitação encontrada</h3>
                <p>As solicitações enviadas aparecerão aqui.</p>
            </div>

            <div v-else class="lista">
                <article v-for="solicitacao in solicitacoes" :key="solicitacao.solicitacao_id" class="solicitacao-card">
                    <div class="solicitacao-topo">
                        <div class="solicitacao-identificacao">
                            <h3>{{ solicitacao.curso_destino }}</h3>
                            <span class="protocolo">
                                {{ solicitacao.protocolo }}
                            </span>
                        </div>

                        <span class="status" :class="classeStatus(solicitacao.status)">
                            {{ nomeStatus(solicitacao.status) }}
                        </span>
                    </div>

                    <div class="metadados">
                        <div>
                            <span class="meta-label">Registrada em</span>
                            <strong>
                                {{ formatarData(solicitacao.criado_em) }}
                            </strong>
                        </div>

                        <div>
                            <span class="meta-label">Documentos</span>
                            <strong>
                                {{ solicitacao.quantidade_documentos }}
                                PDF(s)
                            </strong>
                        </div>

                        <div>
                            <span class="meta-label">Solicitação</span>
                            <strong>
                                #{{ solicitacao.solicitacao_id }}
                            </strong>
                        </div>
                    </div>

                    <div class="solicitacao-rodape">
                        <button type="button" class="primary-button" :disabled="carregandoDetalhes"
                            @click="verDetalhes(solicitacao.protocolo)">
                            Ver detalhes
                        </button>
                    </div>
                </article>
            </div>
        </div>

        <!-- CONSULTA DOS DETALHES -->
        <div v-if="carregandoDetalhes || erroDetalhes || selecionada" class="card painel detalhes">
            <div class="detalhes-cabecalho">
                <h2>Detalhes da solicitação</h2>
                <button type="button" class="fechar-button" :disabled="carregandoDetalhes" @click="fecharDetalhes">
                    Fechar
                </button>
            </div>

            <div v-if="carregandoDetalhes" class="estado">
                <span class="spinner"></span>
                <p>Consultando documentos...</p>
            </div>

            <div v-else-if="erroDetalhes" class="error-box" role="alert">
                {{ erroDetalhes }}
            </div>

            <template v-else-if="selecionada">
                <div class="resumo-detalhes">
                    <div>
                        <span class="meta-label">Protocolo</span>
                        <strong class="quebra-texto">
                            {{ selecionada.protocolo }}
                        </strong>
                    </div>

                    <div>
                        <span class="meta-label">Curso de destino</span>
                        <strong>{{ selecionada.curso_destino }}</strong>
                    </div>

                    <div>
                        <span class="meta-label">Data de registro</span>
                        <strong>
                            {{ formatarData(selecionada.criado_em) }}
                        </strong>
                    </div>

                    <div>
                        <span class="meta-label">Status da solicitação</span>
                        <span class="status" :class="classeStatus(selecionada.status)">
                            {{ nomeStatus(selecionada.status) }}
                        </span>
                    </div>
                </div>

                <div class="documentos">
                    <h3>
                        Documentos enviados
                        ({{ selecionada.documentos.length }})
                    </h3>

                    <div v-for="documento in selecionada.documentos" :key="documento.documento_id"
                        class="documento-item">
                        <div class="pdf-icon">PDF</div>

                        <div class="documento-info">
                            <strong>{{ documento.nome_arquivo }}</strong>
                            <span>
                                {{ documento.quantidade_paginas }} página(s)
                                · {{ formatarTamanho(documento.tamanho_bytes) }}
                            </span>
                            <span class="documento-status">
                                Estado do documento:
                                {{ nomeStatus(documento.status_documento) }}
                            </span>
                        </div>
                    </div>
                </div>

                <p class="observacao">
                    O status de cada documento representa seu registro
                    de processamento e não significa que a análise de
                    equivalência desta solicitação foi concluída.
                </p>
            </template>
        </div>
    </section>
</template>

<style scoped>
.pagina {
    width: 100%;
}

.cabecalho {
    display: flex;
    justify-content: space-between;
    align-items: end;
    gap: 20px;
    margin-bottom: 30px;
}

.intro {
    max-width: 680px;
}

.eyebrow {
    color: #527197;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.6px;
}

h1 {
    margin: 12px 0;
    color: #16345b;
    font-size: clamp(28px, 4vw, 38px);
    letter-spacing: -1px;
}

.intro p {
    color: #68778a;
    line-height: 1.7;
}

.card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
}

.painel {
    padding: 28px;
}

.painel-cabecalho,
.detalhes-cabecalho {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 25px;
}

h2 {
    color: #203d61;
    font-size: 19px;
    margin: 0;
}

.painel-cabecalho p {
    color: #758297;
    font-size: 13px;
    margin: 7px 0 0;
}

.contador {
    padding: 8px 12px;
    background: #edf3fc;
    border-radius: 8px;
    color: #315c92;
    font-size: 12px;
    font-weight: 600;
}

.lista {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.solicitacao-card {
    border: 1px solid #e2e8f0;
    border-radius: 13px;
    padding: 22px;
    background: #fcfdff;
}

.solicitacao-topo {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 15px;
}

.solicitacao-identificacao {
    min-width: 0;
}

.solicitacao-identificacao h3 {
    color: #203d61;
    font-size: 17px;
    margin: 0 0 8px;
}

.protocolo {
    font-size: 12px;
    color: #758297;
    overflow-wrap: anywhere;
}

.status {
    display: inline-flex;
    align-items: center;
    width: fit-content;
    padding: 6px 11px;
    border-radius: 30px;
    font-size: 11px;
    font-weight: 700;
    white-space: nowrap;
}

.status-recebida {
    background: #eaf1ff;
    color: #315c92;
}

.status-processamento {
    background: #fff3da;
    color: #92640d;
}

.status-concluida {
    background: #e4f6eb;
    color: #237348;
}

.status-erro {
    background: #fff0f0;
    color: #a53636;
}

.status-neutro {
    background: #edf0f5;
    color: #68778a;
}

.metadados {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 20px;
    padding: 20px 0;
    margin-top: 18px;
    border-top: 1px solid #edf0f5;
    border-bottom: 1px solid #edf0f5;
}

.meta-label {
    display: block;
    color: #758297;
    font-size: 12px;
    margin-bottom: 7px;
}

.metadados strong,
.resumo-detalhes strong {
    display: block;
    color: #34465e;
    font-size: 13px;
    overflow-wrap: anywhere;
}

.solicitacao-rodape {
    display: flex;
    justify-content: flex-end;
    padding-top: 18px;
}

.primary-button {
    border: none;
    border-radius: 9px;
    padding: 12px 18px;
    background: #1e477b;
    color: white;
    cursor: pointer;
    font-weight: 600;
}

.primary-button:hover:not(:disabled) {
    background: #15365e;
}

.primary-button:disabled,
.secondary-button:disabled,
.fechar-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.secondary-button {
    padding: 12px 18px;
    border: 1px solid #b9cce6;
    border-radius: 9px;
    background: white;
    color: #244f85;
    cursor: pointer;
    font-weight: 600;
}

.secondary-button:hover:not(:disabled) {
    background: #f1f6fd;
}

.detalhes {
    margin-top: 25px;
}

.fechar-button {
    background: none;
    border: none;
    color: #527197;
    cursor: pointer;
    font-weight: 600;
}

.resumo-detalhes {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 22px;
    padding: 22px;
    background: #f8faff;
    border-radius: 12px;
}

.quebra-texto {
    overflow-wrap: anywhere;
}

.documentos {
    margin-top: 28px;
}

.documentos h3 {
    color: #203d61;
    font-size: 16px;
    margin-bottom: 18px;
}

.documento-item {
    display: flex;
    align-items: center;
    gap: 14px;
    border-bottom: 1px solid #edf0f5;
    padding: 15px 0;
}

.pdf-icon {
    display: grid;
    place-items: center;
    flex-shrink: 0;
    height: 48px;
    width: 42px;
    border-radius: 8px;
    background: #e6eefb;
    color: #315c92;
    font-size: 11px;
    font-weight: 800;
}

.documento-info {
    display: flex;
    flex-direction: column;
    min-width: 0;
    gap: 5px;
}

.documento-info strong {
    font-size: 13px;
    color: #34465e;
    overflow-wrap: anywhere;
}

.documento-info span {
    font-size: 12px;
    color: #758297;
}

.documento-info .documento-status {
    color: #527197;
}

.observacao {
    margin-top: 24px;
    color: #758297;
    font-size: 12px;
    line-height: 1.7;
}

.estado {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 45px 15px;
    text-align: center;
    color: #68778a;
}

.estado h3 {
    margin-bottom: 5px;
    color: #203d61;
}

.icone-vazio {
    font-size: 32px;
}

.spinner {
    height: 25px;
    width: 25px;
    border-radius: 50%;
    border: 3px solid #dce7f6;
    border-top-color: #315c92;
    animation: girar 0.8s linear infinite;
}

@keyframes girar {
    to {
        transform: rotate(360deg);
    }
}

.error-box {
    background: #fff1f1;
    color: #922f2f;
    border-radius: 9px;
    padding: 16px;
    font-size: 13px;
    line-height: 1.6;
}

@media (max-width: 700px) {
    .cabecalho {
        align-items: stretch;
        flex-direction: column;
    }

    .painel {
        padding: 18px;
    }

    .solicitacao-topo {
        flex-direction: column;
    }

    .metadados {
        grid-template-columns: 1fr;
        gap: 14px;
    }

    .resumo-detalhes {
        grid-template-columns: 1fr;
    }
}
</style>
