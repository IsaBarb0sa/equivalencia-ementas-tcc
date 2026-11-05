<script setup>
import { computed, onMounted, ref, watch } from 'vue'

const API = `${window.location.protocol}//${window.location.hostname}:8000`

const documentos = ref([])
const documentoSelecionado = ref('')
const indiceSelecionado = ref('')
const resultado = ref(null)
const carregandoDocumentos = ref(false)
const comparando = ref(false)
const erro = ref('')

const disciplinas = computed(() =>
    documentos.value.find((doc) => doc.arquivo === documentoSelecionado.value)?.disciplinas ?? [],
)

watch(documentoSelecionado, () => {
    indiceSelecionado.value = ''
    resultado.value = null
})

watch(indiceSelecionado, () => {
    resultado.value = null
})

async function requisitar(caminho, opcoes = {}) {
    const resposta = await fetch(`${API}${caminho}`, {
        ...opcoes,
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', ...opcoes.headers },
    })

    if (!resposta.ok) {
        let detalhe = ''
        try {
            const corpo = await resposta.json()
            detalhe = typeof corpo.detail === 'string' ? corpo.detail : ''
        } catch {
            // Resposta sem corpo JSON.
        }
        throw new Error(detalhe || `Erro HTTP ${resposta.status}`)
    }
    return resposta.json()
}

async function carregarDocumentos() {
    carregandoDocumentos.value = true
    erro.value = ''
    try {
        const dados = await requisitar('/api/coordenacao/equivalencia/documentos')
        documentos.value = dados.documentos ?? []
    } catch (exc) {
        erro.value = `Não foi possível carregar os documentos: ${exc.message}`
    } finally {
        carregandoDocumentos.value = false
    }
}

async function comparar() {
    if (!documentoSelecionado.value || indiceSelecionado.value === '') return
    comparando.value = true
    resultado.value = null
    erro.value = ''

    try {
        resultado.value = await requisitar('/api/coordenacao/equivalencia/comparar', {
            method: 'POST',
            body: JSON.stringify({
                documento_origem: documentoSelecionado.value,
                indice_disciplina_origem: Number(indiceSelecionado.value),
                quantidade_melhores: 3,
            }),
        })
    } catch (exc) {
        erro.value = `Não foi possível comparar: ${exc.message}`
    } finally {
        comparando.value = false
    }
}

function percentual(valor) {
    return typeof valor === 'number' ? `${(valor * 100).toFixed(1)}%` : 'Não calculada'
}

onMounted(carregarDocumentos)
</script>

<template>
    <main class="pagina-equivalencia">
        <RouterLink class="voltar" to="/coordenacao">← Voltar à coordenação</RouterLink>
        <h1>Análise de equivalência</h1>
        <p class="descricao">
            Selecione uma disciplina extraída. O sistema a compara automaticamente com
            as disciplinas disponíveis na matriz de demonstração da UNIPAC.
        </p>

        <section class="painel">
            <div class="campo">
                <label for="documento">Documento de origem</label>
                <select id="documento" v-model="documentoSelecionado" :disabled="carregandoDocumentos || comparando">
                    <option value="">Selecione um documento</option>
                    <option v-for="doc in documentos" :key="doc.arquivo" :value="doc.arquivo">
                        {{ doc.arquivo }} ({{ doc.disciplinas.length }} disciplinas)
                    </option>
                </select>
            </div>

            <div class="campo">
                <label for="disciplina">Disciplina de origem</label>
                <select id="disciplina" v-model="indiceSelecionado" :disabled="!documentoSelecionado || comparando">
                    <option value="">Selecione uma disciplina</option>
                    <option v-for="disciplina in disciplinas" :key="disciplina.indice" :value="disciplina.indice">
                        {{ disciplina.nome }}
                    </option>
                </select>
            </div>

            <button type="button" :disabled="!documentoSelecionado || indiceSelecionado === '' || comparando"
                @click="comparar">
                {{ comparando ? 'Comparando disciplinas…' : 'Comparar com a matriz' }}
            </button>
        </section>

        <p v-if="carregandoDocumentos">Carregando documentos…</p>
        <p v-if="erro" class="erro" role="alert">{{ erro }}</p>

        <section v-if="resultado" class="resultado">
            <h2>Resultados para {{ resultado.disciplina_origem }}</h2>
            <p>{{ resultado.total_disciplinas_matriz }} disciplinas analisadas.</p>
            <p class="aviso">{{ resultado.aviso }}</p>

            <div class="lista-resultados">
                <details v-for="item in resultado.comparacoes" :key="item.indice_matriz" class="disciplina">
                    <summary>
                        <strong>{{ item.disciplina_destino }}</strong>
                        <span>{{ item.status === 'comparado' ? `${item.evidencias.length} evidências` :
                            item.status.replaceAll('_', ' ') }}</span>
                    </summary>

                    <div v-if="item.evidencias.length" class="evidencias">
                        <article v-for="(evidencia, indice) in item.evidencias" :key="indice" class="evidencia">
                            <div class="pontuacoes">
                                <span>Semântica: {{ percentual(evidencia.similaridade_semantica) }}</span>
                                <span>Lexical: {{ percentual(evidencia.similaridade_lexical) }}</span>
                            </div>
                            <p><b>Origem ({{ evidencia.secao_origem }}):</b> {{ evidencia.origem }}</p>
                            <p><b>Destino ({{ evidencia.secao_destino }}):</b> {{ evidencia.destino }}</p>
                        </article>
                    </div>
                    <p v-else>Não há evidências textuais disponíveis para esta comparação.</p>
                </details>
            </div>
        </section>
    </main>
</template>

<style scoped>
.pagina-equivalencia {
    max-width: 1100px;
    margin: 0 auto;
    padding: 40px 24px 70px;
    color: #17365d;
}

.voltar {
    color: #235996;
    text-decoration: none;
}

h1 {
    font-size: 2rem;
    margin: 20px 0 8px;
}

.descricao {
    color: #586c84;
    margin-bottom: 28px;
}

.painel,
.disciplina {
    background: #fff;
    border: 1px solid #dce5f1;
    border-radius: 14px;
}

.painel {
    display: grid;
    gap: 16px;
    padding: 24px;
    margin-bottom: 28px;
}

.campo {
    display: grid;
    gap: 8px;
}

label {
    font-weight: 600;
}

select {
    width: 100%;
    padding: 12px;
    border: 1px solid #bac9dc;
    border-radius: 8px;
    background: white;
    color: #17365d;
}

button {
    justify-self: start;
    border: 0;
    border-radius: 8px;
    background: #174f91;
    color: white;
    font-weight: 600;
    padding: 13px 20px;
    cursor: pointer;
}

button:disabled {
    opacity: .55;
    cursor: wait;
}

.erro {
    color: #a22c2c;
}

.resultado h2 {
    margin-bottom: 6px;
}

.aviso {
    background: #fff8e5;
    border: 1px solid #f3dfab;
    border-radius: 8px;
    padding: 12px;
    color: #6b501a;
}

.lista-resultados {
    display: grid;
    gap: 12px;
    margin-top: 20px;
}

.disciplina {
    padding: 16px 20px;
}

summary {
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    gap: 20px;
}

summary span {
    font-size: .9rem;
    color: #5d7188;
    white-space: nowrap;
}

.evidencias {
    display: grid;
    gap: 12px;
    margin-top: 16px;
}

.evidencia {
    border-top: 1px solid #e5e9f0;
    padding-top: 12px;
    color: #344c6a;
}

.evidencia p {
    line-height: 1.55;
    overflow-wrap: anywhere;
}

.pontuacoes {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    color: #174f91;
    font-weight: 600;
    font-size: .9rem;
}

@media (max-width: 640px) {
    summary {
        flex-direction: column;
        gap: 4px;
    }
}
</style>
