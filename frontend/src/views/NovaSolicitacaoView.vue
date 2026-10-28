<script setup>
import { computed, onMounted, ref } from 'vue'
import { listarCursos } from '../services/cursos'
import { criarSolicitacao } from '../services/solicitacoes'

const curso = ref('')
const arquivos = ref([])
const erros = ref([])
const enviando = ref(false)
const resultadoEnvio = ref(null)
const erroEnvio = ref('')
const arrastando = ref(false)

const cursos = ref([])
const carregandoCursos = ref(true)
const erroCursos = ref('')

const tamanhoMaximo = 20 * 1024 * 1024

const podeEnviar = computed(() =>
    !enviando.value &&
    !resultadoEnvio.value &&
    !carregandoCursos.value &&
    !erroCursos.value &&
    cursos.value.some(item => String(item.id) === String(curso.value)) &&
    arquivos.value.length > 0
)

async function carregarCursos() {
    carregandoCursos.value = true
    erroCursos.value = ''
    curso.value = ''
    cursos.value = []
    limparResultado()

    try {
        cursos.value = await listarCursos()
    } catch (erro) {
        erroCursos.value = erro.message || 'Não foi possível carregar os cursos.'
    } finally {
        carregandoCursos.value = false
    }
}

onMounted(carregarCursos)

function formatarTamanho(bytes) {
    if (bytes < 1024 * 1024) {
        return `${(bytes / 1024).toFixed(1)} KB`
    }

    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function chaveArquivo(arquivo) {
    return `${arquivo.name}-${arquivo.size}-${arquivo.lastModified}`
}

function limparResultado() {
    resultadoEnvio.value = null
    erroEnvio.value = ''
}

function adicionarArquivos(lista) {
    if (enviando.value || resultadoEnvio.value) return

    erros.value = []
    limparResultado()

    for (const arquivo of Array.from(lista ?? [])) {
        if (!arquivo.name.toLowerCase().endsWith('.pdf')) {
            erros.value.push(`${arquivo.name}: selecione um arquivo PDF.`)
            continue
        }

        if (arquivo.size === 0) {
            erros.value.push(`${arquivo.name}: o arquivo está vazio.`)
            continue
        }

        if (arquivo.size > tamanhoMaximo) {
            erros.value.push(`${arquivo.name}: o limite é de 20 MB por arquivo.`)
            continue
        }

        const duplicado = arquivos.value.some(
            item => chaveArquivo(item) === chaveArquivo(arquivo)
        )

        if (duplicado) {
            erros.value.push(`${arquivo.name}: este arquivo já foi selecionado.`)
            continue
        }

        arquivos.value.push(arquivo)
    }
}

function selecionarArquivos(evento) {
    if (enviando.value || resultadoEnvio.value) return

    adicionarArquivos(evento.target.files)
    evento.target.value = ''
}

function receberArquivos(evento) {
    arrastando.value = false
    if (enviando.value || resultadoEnvio.value) return

    adicionarArquivos(evento.dataTransfer.files)
}

function removerArquivo(indice) {
    if (enviando.value || resultadoEnvio.value) return

    arquivos.value.splice(indice, 1)
    limparResultado()
    erros.value = []
}

function novaSolicitacao() {
    if (enviando.value) return

    curso.value = ''
    arquivos.value = []
    erros.value = []
    limparResultado()
}

async function enviarSolicitacao() {
    if (!podeEnviar.value) return

    erroEnvio.value = ''
    resultadoEnvio.value = null
    enviando.value = true

    try {
        resultadoEnvio.value = await criarSolicitacao(
            curso.value,
            arquivos.value
        )
    } catch (erro) {
        erroEnvio.value =
            erro.message || 'Não foi possível enviar a solicitação.'
    } finally {
        enviando.value = false
    }
}
</script>

<template>
    <section>
        <div class="intro">
            <span class="eyebrow">APROVEITAMENTO DE ESTUDOS</span>
            <h1>Nova solicitação</h1>
            <p>
                Reúna suas ementas e escolha o curso em que deseja aproveitar
                as disciplinas já cursadas.
            </p>
        </div>

        <div class="layout">
            <form class="card form-card" @submit.prevent="enviarSolicitacao">

                <!-- ETAPA 1: CURSO -->
                <section class="form-section">
                    <div class="section-heading">
                        <span class="step" aria-hidden="true">1</span>
                        <h2>Curso de destino</h2>
                    </div>

                    <label for="curso">
                        Em qual curso você deseja ingressar?
                    </label>

                    <select id="curso" v-model="curso" required :disabled="enviando ||
                        Boolean(resultadoEnvio) ||
                        carregandoCursos ||
                        Boolean(erroCursos) ||
                        cursos.length === 0
                        " @change="limparResultado">
                        <option disabled value="">
                            {{
                                carregandoCursos
                                    ? 'Carregando cursos...'
                                    : 'Selecione o curso'
                            }}
                        </option>

                        <option v-for="item in cursos" :key="item.id" :value="item.id">
                            {{ item.nome }}
                        </option>
                    </select>

                    <div v-if="erroCursos" class="error-box" role="alert">
                        <p>{{ erroCursos }}</p>
                        <button type="button" class="primary-button" @click="carregarCursos">
                            Tentar novamente
                        </button>
                    </div>

                    <p v-else-if="!carregandoCursos && cursos.length === 0" class="help" role="status">
                        Nenhum curso está disponível para esta instituição
                        no momento.
                    </p>
                </section>

                <!-- ETAPA 2: DOCUMENTOS -->
                <section class="form-section">
                    <div class="section-heading">
                        <span class="step" aria-hidden="true">2</span>
                        <h2>Ementas das disciplinas</h2>
                    </div>

                    <p id="orientacao-arquivos" class="help">
                        Você pode selecionar vários PDFs ou um documento
                        que contenha as ementas de várias disciplinas.
                    </p>

                    <div class="dropzone" :class="{ 'is-dragging': arrastando }" @dragover.prevent="
                        !enviando && !resultadoEnvio && (arrastando = true)
                        " @dragleave.prevent="arrastando = false" @drop.prevent="receberArquivos">
                        <span class="file-symbol" aria-hidden="true">PDF</span>

                        <strong>Arraste seus documentos para cá</strong>
                        <span>ou selecione os arquivos no seu computador</span>

                        <label class="file-picker">
                            <span>Selecionar PDFs</span>
                            <input type="file" accept=".pdf,application/pdf" multiple
                                :disabled="enviando || Boolean(resultadoEnvio)"
                                aria-label="Selecionar arquivos PDF de ementas"
                                aria-describedby="orientacao-arquivos limite-arquivos" @change="selecionarArquivos" />
                        </label>

                        <small id="limite-arquivos">
                            Até 20 MB por arquivo
                        </small>
                    </div>

                    <!-- ERROS DOS ARQUIVOS -->
                    <div v-if="erros.length" class="error-box" role="alert">
                        <ul>
                            <li v-for="erro in erros" :key="erro">
                                {{ erro }}
                            </li>
                        </ul>
                    </div>

                    <!-- ARQUIVOS SELECIONADOS -->
                    <div v-if="arquivos.length" class="selected-files">
                        <h3>
                            Arquivos selecionados ({{ arquivos.length }})
                        </h3>

                        <ul class="file-list">
                            <li v-for="(arquivo, indice) in arquivos" :key="chaveArquivo(arquivo)" class="file-item">
                                <div class="file-info">
                                    <strong>{{ arquivo.name }}</strong>
                                    <span>
                                        {{ formatarTamanho(arquivo.size) }}
                                    </span>
                                </div>

                                <button type="button" class="remove-button"
                                    :disabled="enviando || Boolean(resultadoEnvio)"
                                    :aria-label="`Remover ${arquivo.name}`" @click="removerArquivo(indice)">
                                    Remover
                                </button>
                            </li>
                        </ul>
                    </div>
                </section>

                <!-- ENVIO -->
                <div class="form-actions">
                    <p>
                        Confira o curso e os documentos antes de enviar.
                    </p>

                    <button type="submit" class="primary-button" :disabled="!podeEnviar">
                        {{ enviando ? 'Enviando...' : 'Enviar solicitação' }}
                    </button>
                </div>

                <!-- ERRO DA API -->
                <div v-if="erroEnvio" class="error-box" role="alert">
                    <strong>
                        Não foi possível registrar a solicitação.
                    </strong>
                    <p>{{ erroEnvio }}</p>
                </div>

                <!-- CONFIRMAÇÃO DO ENVIO -->
                <div v-if="resultadoEnvio" class="notice" role="status">
                    <strong>
                        Solicitação registrada com sucesso!
                    </strong>

                    <p>
                        <strong>Protocolo:</strong>
                        {{ resultadoEnvio.protocolo }}
                    </p>

                    <p>
                        <strong>Status:</strong>
                        {{ resultadoEnvio.status }}
                    </p>

                    <p>
                        <strong>Documentos recebidos:</strong>
                        {{ resultadoEnvio.quantidade_documentos }}
                    </p>

                    <p>
                        Os documentos foram recebidos.
                        A análise de equivalência ainda não foi iniciada.
                    </p>

                    <button type="button" class="secondary-button" @click="novaSolicitacao">
                        Fazer nova solicitação
                    </button>
                </div>
            </form>

            <!-- BARRA LATERAL -->
            <aside class="sidebar">
                <div class="card guidance">
                    <span class="eyebrow">PASSO A PASSO</span>
                    <h2>Como funciona?</h2>

                    <ol class="steps-list">
                        <li>
                            <strong>Envie suas ementas</strong>
                            <p>
                                Escolha o curso de destino e anexe os
                                documentos da instituição de origem.
                            </p>
                        </li>

                        <li>
                            <strong>Acompanhe a análise</strong>
                            <p>
                                O sistema reunirá as informações e sugerirá
                                possíveis equivalências.
                            </p>
                        </li>

                        <li>
                            <strong>Receba o parecer</strong>
                            <p>
                                A coordenação revisará as sugestões e
                                confirmará o resultado.
                            </p>
                        </li>
                    </ol>
                </div>

                <div class="tip">
                    <h3>O que incluir nos documentos?</h3>
                    <p>
                        Sempre que possível, envie ementas com nome
                        da disciplina, carga horária e conteúdo
                        programático. Informações completas
                        ajudam na avaliação.
                    </p>
                </div>

                <p class="prototype-note">
                    O recebimento dos PDFs já está integrado.
                    A análise automática e o acompanhamento serão
                    disponibilizados nas próximas etapas.
                </p>
            </aside>
        </div>
    </section>
</template>

<style scoped>
.intro {
    max-width: 670px;
    margin-bottom: 32px;
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

.intro p,
.help {
    color: #68778a;
    line-height: 1.7;
}

.layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 300px;
    gap: 26px;
    align-items: start;
}

.card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
}

.form-card {
    padding: 30px;
}

.form-section+.form-section {
    border-top: 1px solid #edf0f5;
    margin-top: 28px;
    padding-top: 28px;
}

.section-heading {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 22px;
}

.step {
    width: 30px;
    height: 30px;
    flex-shrink: 0;
    display: grid;
    place-items: center;
    border-radius: 50%;
    background: #eaf1fb;
    color: #315c92;
    font-size: 14px;
    font-weight: 700;
}

h2 {
    margin: 0;
    font-size: 18px;
    color: #203d61;
}

label {
    display: block;
    margin-bottom: 9px;
    font-size: 14px;
    font-weight: 600;
}

select {
    width: 100%;
    padding: 13px;
    border: 1px solid #cbd5e1;
    border-radius: 9px;
    color: #203047;
    background: white;
}

.help {
    margin-top: -5px;
    font-size: 14px;
}

.dropzone {
    display: flex;
    align-items: center;
    flex-direction: column;
    gap: 12px;
    padding: 30px 18px;
    border: 2px dashed #c4d2e5;
    border-radius: 13px;
    background: #f8faff;
    text-align: center;
}

.dropzone.is-dragging {
    background: #eaf2ff;
    border-color: #326ac0;
}

.file-symbol {
    display: grid;
    place-items: center;
    width: 46px;
    height: 54px;
    border-radius: 9px;
    background: #e6eefb;
    color: #315c92;
    font-size: 12px;
    font-weight: 800;
}

.dropzone>span:not(.file-symbol),
.dropzone small {
    color: #6b7b91;
    font-size: 13px;
}

.file-picker {
    position: relative;
    overflow: hidden;
    margin: 4px 0;
    padding: 11px 18px;
    border: 1px solid #b9cce6;
    border-radius: 8px;
    background: white;
    color: #244f85;
    cursor: pointer;
}

.file-picker:focus-within {
    outline: 3px solid #4385e0;
    outline-offset: 4px;
}

.file-picker input {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    opacity: 0;
    cursor: pointer;
}

.selected-files h3 {
    margin: 23px 0 12px;
    font-size: 14px;
}

.file-list {
    padding: 0;
    margin: 0;
    list-style: none;
}

.file-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 14px 0;
    border-bottom: 1px solid #edf0f5;
}

.file-info {
    min-width: 0;
}

.file-info strong {
    display: block;
    overflow-wrap: anywhere;
    font-size: 13px;
}

.file-info span {
    display: block;
    margin-top: 5px;
    color: #758297;
    font-size: 12px;
}

.remove-button {
    border: none;
    padding: 8px;
    background: transparent;
    color: #a53636;
    cursor: pointer;
    font-size: 12px;
}

.form-actions {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 12px;
    margin-top: 26px;
}

.form-actions p {
    margin: 0;
    color: #6b7b91;
    font-size: 12px;
}

.primary-button {
    border: none;
    border-radius: 9px;
    padding: 14px 22px;
    background: #1e477b;
    color: white;
    font-weight: 600;
    cursor: pointer;
}

.primary-button:hover:not(:disabled) {
    background: #15365e;
}

.primary-button:disabled {
    background: #dce3ed;
    color: #66758a;
    cursor: not-allowed;
}

.secondary-button {
    margin-top: 15px;
    border: 1px solid #b9cce6;
    border-radius: 9px;
    padding: 11px 18px;
    background: white;
    color: #244f85;
    font-weight: 600;
    cursor: pointer;
}

.secondary-button:hover {
    background: #eaf1fb;
}

.guidance {
    padding: 26px;
}

.guidance h2 {
    margin-top: 12px;
}

.steps-list {
    padding-left: 20px;
    margin-bottom: 0;
}

.steps-list li {
    padding-left: 5px;
    margin-top: 23px;
    font-size: 14px;
}

.steps-list li::marker {
    color: #527197;
    font-weight: 700;
}

.steps-list p,
.tip p {
    margin-bottom: 0;
    color: #68778a;
    font-size: 13px;
    line-height: 1.7;
}

.tip {
    margin-top: 20px;
    padding: 23px;
    border-radius: 14px;
    background: #eaf0f9;
}

.tip h3 {
    margin: 0;
    font-size: 14px;
    color: #294c78;
}

.prototype-note {
    padding: 0 8px;
    color: #69788d;
    font-size: 12px;
    line-height: 1.6;
}

.error-box,
.notice {
    margin-top: 20px;
    padding: 15px;
    border-radius: 9px;
    font-size: 13px;
    line-height: 1.6;
    overflow-wrap: anywhere;
}

.error-box {
    background: #fff1f1;
    color: #922f2f;
}

.error-box ul {
    margin: 0;
    padding-left: 18px;
}

.notice {
    background: #edf4ff;
    color: #274e80;
}

.notice p {
    margin-bottom: 0;
}

@media (max-width: 850px) {
    .layout {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 480px) {
    .form-card {
        padding: 20px;
    }

    .primary-button {
        width: 100%;
    }

    .file-item {
        gap: 8px;
    }
}
</style>
