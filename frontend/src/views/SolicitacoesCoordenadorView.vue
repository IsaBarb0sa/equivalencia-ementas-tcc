<script setup>
import { ref, onMounted, computed } from 'vue'
import { listarSolicitacoesCoordenacao } from '../services/coordenacao'

const solicitacoes = ref([])
const carregando = ref(true)
const erro = ref('')

const total = computed(() => solicitacoes.value.length)

const recebidas = computed(() =>
    solicitacoes.value.filter(
        (item) => item.status === 'RECEBIDA'
    ).length
)

const emAnalise = computed(() =>
    solicitacoes.value.filter(
        (item) => item.status === 'EM_ANALISE'
    ).length
)

const concluidas = computed(() =>
    solicitacoes.value.filter(
        (item) => item.status === 'CONCLUIDA'
    ).length
)

function formatarData(valor) {
    if (!valor) return 'Não informada'

    const data = new Date(valor)

    if (Number.isNaN(data.getTime())) {
        return valor
    }

    return data.toLocaleDateString('pt-BR')
}

function formatarStatus(status) {
    const nomes = {
        RECEBIDA: 'Recebida',
        EM_ANALISE: 'Em análise',
        CONCLUIDA: 'Concluída',
    }

    return nomes[status] || status.replaceAll('_', ' ')
}

function classeStatus(status) {
    return {
        RECEBIDA: 'status-recebida',
        EM_ANALISE: 'status-analise',
        CONCLUIDA: 'status-concluida',
    }[status] || 'status-padrao'
}

async function carregarSolicitacoes() {
    carregando.value = true
    erro.value = ''

    try {
        solicitacoes.value = await listarSolicitacoesCoordenacao()
    } catch (excecao) {
        solicitacoes.value = []
        erro.value =
            excecao.message || 'Não foi possível carregar as solicitações.'
    } finally {
        carregando.value = false
    }
}

onMounted(carregarSolicitacoes)
</script>

<template>
    <main class="pagina">
        <RouterLink to="/coordenacao" class="voltar">
            ← Voltar ao painel
        </RouterLink>

        <div class="cabecalho">
            <div>
                <span class="subtitulo">ÁREA DA COORDENAÇÃO</span>
                <h1>Solicitações recebidas</h1>
                <p>
                    Consulte os processos de equivalência enviados
                    para os cursos sob sua responsabilidade.
                </p>
            </div>

            <button type="button" class="atualizar" :disabled="carregando" @click="carregarSolicitacoes">
                {{ carregando ? 'Carregando...' : 'Atualizar lista' }}
            </button>
        </div>

        <div v-if="!carregando && !erro" class="resumo">
            <div class="resumo-card">
                <span>Total de solicitações</span>
                <strong>{{ total }}</strong>
            </div>

            <div class="resumo-card">
                <span>Recebidas</span>
                <strong>{{ recebidas }}</strong>
            </div>

            <div class="resumo-card">
                <span>Em análise</span>
                <strong>{{ emAnalise }}</strong>
            </div>

            <div class="resumo-card">
                <span>Concluídas</span>
                <strong>{{ concluidas }}</strong>
            </div>
        </div>

        <div v-if="carregando" class="mensagem">
            Carregando solicitações...
        </div>

        <div v-else-if="erro" class="mensagem erro" role="alert">
            <strong>Não foi possível carregar os processos.</strong>
            <p>{{ erro }}</p>

            <button type="button" @click="carregarSolicitacoes">
                Tentar novamente
            </button>
        </div>

        <div v-else-if="solicitacoes.length === 0" class="mensagem">
            <h2>Nenhuma solicitação encontrada</h2>
            <p>
                Ainda não existem solicitações para os seus cursos.
            </p>
        </div>

        <section v-else class="lista">
            <div class="lista-topo">
                <h2>Processos cadastrados</h2>
                <span>{{ total }} resultado(s)</span>
            </div>

            <article v-for="solicitacao in solicitacoes" :key="solicitacao.solicitacao_id" class="solicitacao-card">
                <div class="card-topo">
                    <div>
                        <span class="rotulo">CURSO DE DESTINO</span>
                        <h3>{{ solicitacao.curso_destino }}</h3>
                    </div>

                    <span class="status" :class="classeStatus(solicitacao.status)">
                        {{ formatarStatus(solicitacao.status) }}
                    </span>
                </div>

                <div class="informacoes">
                    <div>
                        <span class="rotulo">PROTOCOLO</span>
                        <p class="protocolo">{{ solicitacao.protocolo }}</p>
                    </div>

                    <div>
                        <span class="rotulo">DATA DE ENVIO</span>
                        <p>{{ formatarData(solicitacao.criado_em) }}</p>
                    </div>

                    <div>
                        <span class="rotulo">DOCUMENTOS</span>
                        <p>
                            {{ solicitacao.quantidade_documentos }}
                            PDF(s)
                        </p>
                    </div>
                </div>

                <div class="card-rodape">
                    <span>
                        Solicitação #{{ solicitacao.solicitacao_id }}
                    </span>


                    <RouterLink :to="{
                        name: 'detalhe-solicitacao-coordenacao',
                        params: { protocolo: solicitacao.protocolo },
                    }" class="botao-detalhes">
                        Visualizar detalhes →
                    </RouterLink>

                </div>
            </article>
        </section>
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

.cabecalho {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 24px;
    margin-bottom: 30px;
}

.subtitulo,
.rotulo {
    color: #6380a3;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}

h1 {
    color: #16345b;
    font-size: 30px;
    margin: 12px 0;
}

.cabecalho p {
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
    white-space: nowrap;
}

.atualizar:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.resumo {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 30px;
}

.resumo-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 13px;
    padding: 22px;
}

.resumo-card span {
    display: block;
    color: #64748b;
    font-size: 12px;
    margin-bottom: 13px;
}

.resumo-card strong {
    font-size: 29px;
    color: #16345b;
}

.lista {
    display: flex;
    flex-direction: column;
    gap: 17px;
}

.lista-topo {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.lista-topo h2 {
    color: #16345b;
    font-size: 20px;
}

.lista-topo span {
    color: #64748b;
    font-size: 13px;
}

.solicitacao-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 15px;
    padding: 25px;
}

.card-topo {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: flex-start;
    margin-bottom: 23px;
}

h3 {
    color: #16345b;
    font-size: 19px;
    margin: 8px 0 0;
}

.status {
    border-radius: 30px;
    padding: 7px 12px;
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
}

.status-recebida {
    background: #eaf1fc;
    color: #24548d;
}

.status-analise {
    background: #fff5df;
    color: #91630a;
}

.status-concluida {
    background: #eaf7ef;
    color: #22633e;
}

.status-padrao {
    background: #edf0f4;
    color: #475569;
}

.informacoes {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr;
    gap: 18px;
}

.informacoes p {
    font-size: 14px;
    color: #34465e;
    margin: 9px 0;
}

.protocolo {
    overflow-wrap: anywhere;
}

.card-rodape {
    border-top: 1px solid #edf0f5;
    margin-top: 23px;
    padding-top: 17px;
    display: flex;
    justify-content: space-between;
    gap: 12px;
    font-size: 12px;
    color: #758297;
}

.detalhes-pendente {
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

.mensagem h2 {
    color: #16345b;
}

.mensagem.erro {
    background: #fff5f5;
    color: #922f2f;
}

.mensagem button {
    margin-top: 15px;
    padding: 10px 16px;
    border-radius: 8px;
    border: none;
    background: #1e477b;
    color: white;
    cursor: pointer;
}

@media (max-width: 850px) {
    .resumo {
        grid-template-columns: repeat(2, 1fr);
    }

    .informacoes {
        grid-template-columns: 1fr 1fr;
    }
}

@media (max-width: 600px) {

    .cabecalho,
    .card-topo,
    .card-rodape {
        flex-direction: column;
    }

    .resumo,
    .informacoes {
        grid-template-columns: 1fr;
    }

    h1 {
        font-size: 25px;
    }
}

.botao-detalhes {
    display: inline-block;
    padding: 10px 16px;
    background: #1e477b;
    color: white;
    text-decoration: none;
    font-size: 13px;
    font-weight: 600;
    border-radius: 9px;
    transition: background 0.2s;
}

.botao-detalhes:hover {
    background: #16345b;
}
</style>
