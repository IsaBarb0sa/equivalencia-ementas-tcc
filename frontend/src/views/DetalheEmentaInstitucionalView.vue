<script setup>
import { reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
    buscarEmentaInstitucional,
    atualizarEmentaInstitucional,
    atualizarObjetivoInstitucional,
    atualizarConteudoInstitucional,
    atualizarBibliografiaInstitucional,
} from '../services/ementasInstitucionais'

const route = useRoute()

const ementa = ref(null)
const carregando = ref(false)
const erro = ref('')

let consultaAtual = 0

const editando = ref(false)
const salvando = ref(false)
const erroEdicao = ref('')
const sucessoEdicao = ref('')
const conflitoEdicao = ref(false)

const formulario = reactive({
    resumo: '',
    competencias_habilidades: '',
    carga_horaria_total: '',
    carga_horaria_teorica: '',
    carga_horaria_pratica: '',
})

function preencherFormulario(dados) {
    formulario.resumo = dados.resumo ?? ''
    formulario.competencias_habilidades =
        dados.competencias_habilidades ?? ''

    formulario.carga_horaria_total =
        dados.carga_horaria_total?.toString() ?? ''

    formulario.carga_horaria_teorica =
        dados.carga_horaria_teorica?.toString() ?? ''

    formulario.carga_horaria_pratica =
        dados.carga_horaria_pratica?.toString() ?? ''
}

function iniciarEdicao() {
    if (
        !ementa.value ||
        salvando.value ||
        objetivoEditandoId.value !== null ||
        conteudoEditandoId.value !== null ||
        bibliografiaEditandoId.value !== null
    ) return

    if (!['RASCUNHO', 'EM_REVISAO'].includes(ementa.value.status)) {
        return
    }

    preencherFormulario(ementa.value)
    erroEdicao.value = ''
    sucessoEdicao.value = ''
    conflitoEdicao.value = false
    editando.value = true
}

function cancelarEdicao() {
    if (salvando.value) return

    editando.value = false
    erroEdicao.value = ''
    conflitoEdicao.value = false
}

function converterCarga(valor) {
    const texto = String(valor ?? '').trim()

    if (!texto) return null

    // O campo numérico HTML utiliza ponto como separador decimal.
    const numero = Number(texto)

    if (!Number.isFinite(numero)) {
        throw new Error('Informe uma carga horária numérica válida.')
    }

    return numero
}

async function salvarEdicao() {
    if (!ementa.value || salvando.value || conflitoEdicao.value) {
        return
    }

    salvando.value = true
    erroEdicao.value = ''
    sucessoEdicao.value = ''

    try {
        const dados = {
            versao_linha: ementa.value.versao_linha,
            resumo: formulario.resumo.trim() || null,
            competencias_habilidades:
                formulario.competencias_habilidades.trim() || null,
            carga_horaria_total: converterCarga(formulario.carga_horaria_total),
            carga_horaria_teorica: converterCarga(formulario.carga_horaria_teorica),
            carga_horaria_pratica: converterCarga(formulario.carga_horaria_pratica),
        }

        const resultado = await atualizarEmentaInstitucional(
            ementa.value.matriz_disciplina_id,
            ementa.value.ementa_id,
            dados
        )

        ementa.value = resultado
        preencherFormulario(resultado)

        editando.value = false
        sucessoEdicao.value = 'Ementa atualizada com sucesso!'
    } catch (excecao) {
        erroEdicao.value =
            excecao.message || 'Não foi possível salvar as alterações.'

        if (excecao.status === 409) {
            conflitoEdicao.value = true
        }
    } finally {
        salvando.value = false
    }
}

async function descartarERecarregar() {
    if (salvando.value) return

    editando.value = false
    conflitoEdicao.value = false
    erroEdicao.value = ''
    sucessoEdicao.value = ''

    await carregarEmenta()
}

function exibir(valor) {
    if (valor === null || valor === undefined || valor === '') {
        return 'Não informado'
    }

    return valor
}

function cargaHoraria(valor) {
    if (valor === null || valor === undefined) {
        return 'Não informada'
    }

    return `${Number(valor).toLocaleString('pt-BR')} h`
}

function formatarData(valor) {
    if (!valor) return 'Não informada'

    const partes = valor.slice(0, 10).split('-')

    if (partes.length !== 3) return valor

    const [ano, mes, dia] = partes
    return `${dia}/${mes}/${ano}`
}

function formatarStatus(valor) {
    const status = {
        RASCUNHO: 'Rascunho',
        EM_REVISAO: 'Em revisão',
        PUBLICADA: 'Publicada',
        ARQUIVADA: 'Arquivada',
    }

    return status[valor] || exibir(valor)
}

async function carregarEmenta() {
    const versao = ++consultaAtual

    carregando.value = true
    erro.value = ''
    ementa.value = null

    try {
        const resultado = await buscarEmentaInstitucional(
            route.params.matrizDisciplinaId,
            route.params.ementaId
        )

        if (versao === consultaAtual) {
            ementa.value = resultado
            preencherFormulario(resultado)
        }
    } catch (excecao) {
        if (versao === consultaAtual) {
            erro.value =
                excecao.message || 'Não foi possível consultar a ementa.'
        }
    } finally {
        if (versao === consultaAtual) {
            carregando.value = false
        }
    }
}

watch(
    () => [route.params.matrizDisciplinaId, route.params.ementaId],
    carregarEmenta,
    { immediate: true }
)

const objetivoEditandoId = ref(null)
const textoObjetivo = ref('')
const salvandoObjetivo = ref(false)
const erroObjetivo = ref('')
const conflitoObjetivo = ref(false)

function iniciarEdicaoObjetivo(objetivo) {
    if (
        !ementa.value ||
        editando.value ||
        salvando.value ||
        salvandoObjetivo.value ||
        objetivoEditandoId.value !== null ||
        conteudoEditandoId.value !== null ||
        bibliografiaEditandoId.value !== null ||
        !['RASCUNHO', 'EM_REVISAO'].includes(ementa.value.status)
    ) {
        return
    }

    objetivoEditandoId.value = objetivo.objetivo_id
    textoObjetivo.value = objetivo.texto
    erroObjetivo.value = ''
    conflitoObjetivo.value = false
    sucessoEdicao.value = ''
}

function cancelarEdicaoObjetivo() {
    if (salvandoObjetivo.value) return

    objetivoEditandoId.value = null
    textoObjetivo.value = ''
    erroObjetivo.value = ''
    conflitoObjetivo.value = false
}

async function salvarObjetivo(objetivoId) {
    if (
        salvandoObjetivo.value ||
        conflitoObjetivo.value ||
        objetivoEditandoId.value !== objetivoId ||
        !ementa.value
    ) {
        return
    }

    const texto = textoObjetivo.value.trim()

    if (!texto) {
        erroObjetivo.value = 'O objetivo não pode ficar vazio.'
        return
    }

    salvandoObjetivo.value = true
    erroObjetivo.value = ''

    try {
        const resultado = await atualizarObjetivoInstitucional(
            ementa.value.matriz_disciplina_id,
            ementa.value.ementa_id,
            objetivoId,
            {
                versao_linha: ementa.value.versao_linha,
                texto,
            }
        )

        ementa.value = resultado
        preencherFormulario(resultado)

        objetivoEditandoId.value = null
        textoObjetivo.value = ''
        sucessoEdicao.value = 'Objetivo atualizado com sucesso!'
    } catch (excecao) {
        erroObjetivo.value =
            excecao.message || 'Não foi possível atualizar o objetivo.'

        if (excecao.status === 409) {
            conflitoObjetivo.value = true
        }
    } finally {
        salvandoObjetivo.value = false
    }
}

async function descartarObjetivoERecarregar() {
    if (salvandoObjetivo.value) return

    cancelarEdicaoObjetivo()
    sucessoEdicao.value = ''
    await carregarEmenta()
}

const conteudoEditandoId = ref(null)
const textoConteudo = ref('')
const salvandoConteudo = ref(false)
const erroConteudo = ref('')
const conflitoConteudo = ref(false)

function iniciarEdicaoConteudo(conteudo) {
    if (
        !ementa.value ||
        editando.value ||
        objetivoEditandoId.value !== null ||
        conteudoEditandoId.value !== null ||
        bibliografiaEditandoId.value !== null ||
        salvando.value ||
        salvandoObjetivo.value ||
        salvandoConteudo.value ||
        salvandoBibliografia.value ||
        !['RASCUNHO', 'EM_REVISAO'].includes(ementa.value.status)
    ) {
        return
    }


    conteudoEditandoId.value = conteudo.conteudo_id
    textoConteudo.value = conteudo.texto
    erroConteudo.value = ''
    conflitoConteudo.value = false
    sucessoEdicao.value = ''
}

function cancelarEdicaoConteudo() {
    if (salvandoConteudo.value) return

    conteudoEditandoId.value = null
    textoConteudo.value = ''
    erroConteudo.value = ''
    conflitoConteudo.value = false
}

async function salvarConteudo(conteudoId) {
    if (
        salvandoConteudo.value ||
        conflitoConteudo.value ||
        conteudoEditandoId.value !== conteudoId ||
        !ementa.value
    ) {
        return
    }

    const texto = textoConteudo.value.trim()

    if (!texto) {
        erroConteudo.value = 'O tópico não pode ficar vazio.'
        return
    }

    salvandoConteudo.value = true
    erroConteudo.value = ''

    try {
        const resultado = await atualizarConteudoInstitucional(
            ementa.value.matriz_disciplina_id,
            ementa.value.ementa_id,
            conteudoId,
            {
                versao_linha: ementa.value.versao_linha,
                texto,
            }
        )

        ementa.value = resultado
        preencherFormulario(resultado)

        conteudoEditandoId.value = null
        textoConteudo.value = ''
        sucessoEdicao.value = 'Conteúdo programático atualizado com sucesso!'
    } catch (excecao) {
        erroConteudo.value =
            excecao.message || 'Não foi possível atualizar o conteúdo.'

        if (excecao.status === 409) {
            conflitoConteudo.value = true
        }
    } finally {
        salvandoConteudo.value = false
    }
}

async function descartarConteudoERecarregar() {
    if (salvandoConteudo.value) return

    cancelarEdicaoConteudo()
    sucessoEdicao.value = ''
    await carregarEmenta()
}

const bibliografiaEditandoId = ref(null)
const textoBibliografia = ref('')
const salvandoBibliografia = ref(false)
const erroBibliografia = ref('')
const conflitoBibliografia = ref(false)

function iniciarEdicaoBibliografia(bibliografia) {
    if (
        !ementa.value ||
        editando.value ||
        objetivoEditandoId.value !== null ||
        conteudoEditandoId.value !== null ||
        bibliografiaEditandoId.value !== null ||
        salvando.value ||
        salvandoObjetivo.value ||
        salvandoConteudo.value ||
        salvandoBibliografia.value ||
        !['RASCUNHO', 'EM_REVISAO'].includes(ementa.value.status)
    ) {
        return
    }

    bibliografiaEditandoId.value = bibliografia.bibliografia_id
    textoBibliografia.value = bibliografia.referencia
    erroBibliografia.value = ''
    conflitoBibliografia.value = false
    sucessoEdicao.value = ''
}

function cancelarEdicaoBibliografia() {
    if (salvandoBibliografia.value) return

    bibliografiaEditandoId.value = null
    textoBibliografia.value = ''
    erroBibliografia.value = ''
    conflitoBibliografia.value = false
}

async function salvarBibliografia(bibliografiaId) {
    if (
        salvandoBibliografia.value ||
        conflitoBibliografia.value ||
        bibliografiaEditandoId.value !== bibliografiaId ||
        !ementa.value
    ) {
        return
    }

    const texto = textoBibliografia.value.trim()

    if (!texto) {
        erroBibliografia.value = 'A bibliografia não pode ficar vazia.'
        return
    }

    salvandoBibliografia.value = true
    erroBibliografia.value = ''

    try {
        const resultado = await atualizarBibliografiaInstitucional(
            ementa.value.matriz_disciplina_id,
            ementa.value.ementa_id,
            bibliografiaId,
            {
                versao_linha: ementa.value.versao_linha,
                texto,
            }
        )

        ementa.value = resultado
        preencherFormulario(resultado)

        bibliografiaEditandoId.value = null
        textoBibliografia.value = ''
        sucessoEdicao.value = 'Bibliografia atualizada com sucesso!'
    } catch (excecao) {
        erroBibliografia.value =
            excecao.message || 'Não foi possível atualizar a bibliografia.'

        if (excecao.status === 409) {
            conflitoBibliografia.value = true
        }
    } finally {
        salvandoBibliografia.value = false
    }
}

async function descartarBibliografiaERecarregar() {
    if (salvandoBibliografia.value) return

    cancelarEdicaoBibliografia()
    sucessoEdicao.value = ''
    await carregarEmenta()
}

</script>

<template>
    <main class="pagina">
        <RouterLink to="/coordenacao/ementas" class="voltar">
            ← Voltar às ementas institucionais
        </RouterLink>

        <header class="cabecalho">
            <div>
                <span class="subtitulo">ÁREA DA COORDENAÇÃO</span>
                <h1>Detalhes da ementa</h1>
                <p>
                    Consulte as informações acadêmicas registradas
                    para esta disciplina.
                </p>
            </div>
            <button type="button" class="botao" :disabled="carregando ||
                editando ||
                salvando ||
                objetivoEditandoId !== null ||
                conteudoEditandoId !== null ||
                bibliografiaEditandoId !== null
                " @click="carregarEmenta">
                {{ carregando ? 'Carregando...' : 'Atualizar' }}
            </button>
        </header>

        <section v-if="carregando" class="mensagem">
            Carregando ementa institucional...
        </section>

        <section v-else-if="erro" class="mensagem erro" role="alert">
            <h2>Não foi possível carregar a ementa.</h2>
            <p>{{ erro }}</p>
            <button type="button" class="botao" @click="carregarEmenta">
                Tentar novamente
            </button>
        </section>

        <template v-else-if="ementa">

            <!-- AÇÕES DA EMENTA -->
            <section class="acoes-edicao">
                <div>
                    <h2>Revisão da ementa</h2>
                    <p v-if="!editando">
                        Consulte os dados cadastrados ou inicie uma revisão.
                    </p>
                    <p v-else>
                        Altere os campos necessários e salve ao finalizar.
                    </p>
                </div>

                <button v-if="
                    !editando &&
                    objetivoEditandoId === null &&
                    conteudoEditandoId === null &&
                    bibliografiaEditandoId === null &&
                    ['RASCUNHO', 'EM_REVISAO'].includes(ementa.status)" type="button" class="botao"
                    @click="iniciarEdicao">
                    Editar ementa
                </button>

                <span v-else-if="!editando && !['RASCUNHO', 'EM_REVISAO'].includes(ementa.status)"
                    class="aviso-somente-leitura">
                    Ementa disponível somente para consulta
                </span>
            </section>

            <p v-if="sucessoEdicao" class="mensagem-sucesso" role="status">
                {{ sucessoEdicao }}
            </p>

            <!-- FORMULÁRIO DE EDIÇÃO -->
            <section v-if="editando" class="cartao formulario-edicao">
                <h2>Editar informações principais</h2>

                <p class="aviso-formulario">
                    As alterações serão salvas na ementa institucional.
                    O status continuará em revisão.
                </p>

                <div v-if="erroEdicao" class="mensagem-erro" role="alert">
                    <p>{{ erroEdicao }}</p>

                    <button v-if="conflitoEdicao" type="button" class="botao" :disabled="salvando"
                        @click="descartarERecarregar">
                        Descartar alterações e atualizar ementa
                    </button>
                </div>

                <form @submit.prevent="salvarEdicao">
                    <div class="campo-formulario">
                        <label for="resumo-edicao">Resumo da ementa</label>
                        <textarea id="resumo-edicao" v-model="formulario.resumo" rows="6" maxlength="30000"
                            :disabled="salvando || conflitoEdicao"></textarea>
                    </div>

                    <div class="campo-formulario">
                        <label for="competencias-edicao">
                            Competências e habilidades
                        </label>

                        <textarea id="competencias-edicao" v-model="formulario.competencias_habilidades" rows="8"
                            maxlength="30000" :disabled="salvando || conflitoEdicao"></textarea>
                    </div>

                    <h3>Carga horária</h3>

                    <p class="aviso-formulario">
                        Utilize valores na mesma unidade. Não misture
                        horas-aula e horas-relógio.
                    </p>

                    <div class="campos-carga">
                        <div class="campo-formulario">
                            <label for="carga-total">Total</label>
                            <input id="carga-total" v-model="formulario.carga_horaria_total" type="number" min="0.01"
                                max="999999.99" step="0.01" :disabled="salvando || conflitoEdicao" />
                        </div>

                        <div class="campo-formulario">
                            <label for="carga-teorica">Teórica</label>
                            <input id="carga-teorica" v-model="formulario.carga_horaria_teorica" type="number" min="0"
                                max="999999.99" step="0.01" :disabled="salvando || conflitoEdicao" />
                        </div>

                        <div class="campo-formulario">
                            <label for="carga-pratica">Prática</label>
                            <input id="carga-pratica" v-model="formulario.carga_horaria_pratica" type="number" min="0"
                                max="999999.99" step="0.01" :disabled="salvando || conflitoEdicao" />
                        </div>
                    </div>

                    <div class="botoes-formulario">
                        <button type="button" class="botao-cancelar" :disabled="salvando" @click="cancelarEdicao">
                            Cancelar
                        </button>

                        <button type="submit" class="botao" :disabled="salvando || conflitoEdicao">
                            {{ salvando ? 'Salvando...' : 'Salvar alterações' }}
                        </button>
                    </div>
                </form>
            </section>

            <section class="cartao">
                <div class="titulo-disciplina">
                    <div>
                        <span class="subtitulo">
                            DISCIPLINA {{ ementa.codigo_disciplina }}
                        </span>

                        <h2>{{ ementa.nome_disciplina }}</h2>

                        <p>
                            {{ ementa.nome_curso }} ·
                            {{ ementa.nome_matriz || ementa.codigo_matriz }}
                        </p>
                    </div>

                    <span class="status" :class="{ publicada: ementa.status === 'PUBLICADA' }">
                        {{ formatarStatus(ementa.status) }}
                    </span>
                </div>

                <div class="dados">
                    <div>
                        <span class="rotulo">VERSÃO</span>
                        <strong>{{ ementa.versao }}</strong>
                    </div>

                    <div>
                        <span class="rotulo">MATRIZ</span>
                        <strong>{{ ementa.codigo_matriz }}</strong>
                    </div>

                    <div>
                        <span class="rotulo">IDIOMA</span>
                        <strong>{{ exibir(ementa.idioma) }}</strong>
                    </div>

                    <div>
                        <span class="rotulo">ANO DE VIGÊNCIA</span>
                        <strong>{{ exibir(ementa.ano_vigencia) }}</strong>
                    </div>
                </div>
            </section>

            <section class="cartao">
                <h2>Carga horária</h2>

                <div class="cargas">
                    <div class="carga">
                        <span>Total declarada</span>
                        <strong>{{ cargaHoraria(ementa.carga_horaria_total) }}</strong>
                    </div>

                    <div class="carga">
                        <span>Teórica</span>
                        <strong>{{ cargaHoraria(ementa.carga_horaria_teorica) }}</strong>
                    </div>

                    <div class="carga">
                        <span>Prática</span>
                        <strong>{{ cargaHoraria(ementa.carga_horaria_pratica) }}</strong>
                    </div>
                </div>

                <p class="observacao">
                    Unidade informada:
                    {{ exibir(ementa.unidade_carga_horaria) }}
                </p>
            </section>

            <section class="cartao">
                <h2>Resumo da ementa</h2>

                <p class="texto-conteudo">
                    {{ exibir(ementa.resumo) }}
                </p>
            </section>

            <section class="cartao">
                <h2>Competências e habilidades</h2>

                <p class="texto-conteudo">
                    {{ exibir(ementa.competencias_habilidades) }}
                </p>
            </section>


            <!-- OBJETIVOS DA DISCIPLINA -->
            <section class="cartao">
                <div class="secao-cabecalho">
                    <h2>Objetivos da disciplina</h2>

                    <span class="contador">
                        {{ ementa.objetivos?.length || 0 }} objetivo(s)
                    </span>
                </div>

                <div v-if="!ementa.objetivos?.length" class="sem-informacao">
                    Nenhum objetivo cadastrado.
                </div>

                <div v-else class="grupo-itens">
                    <article v-for="objetivo in ementa.objetivos" :key="objetivo.objetivo_id" class="item-conteudo">
                        <div class="objetivo-cabecalho">
                            <span class="tipo-item">
                                {{
                                    objetivo.tipo === 'GERAL'
                                        ? 'Objetivo geral'
                                        : objetivo.tipo === 'ESPECIFICO'
                                            ? 'Objetivo específico'
                                            : 'Objetivo não classificado'
                                }}
                            </span>

                            <button v-if="
                                objetivoEditandoId !== objetivo.objetivo_id &&
                                !editando &&
                                objetivoEditandoId === null &&
                                conteudoEditandoId === null &&
                                bibliografiaEditandoId === null &&
                                ['RASCUNHO', 'EM_REVISAO'].includes(ementa.status)
                            " type="button" class="botao-editar-item" @click="iniciarEdicaoObjetivo(objetivo)">
                                Editar objetivo
                            </button>
                        </div>

                        <template v-if="objetivoEditandoId === objetivo.objetivo_id">
                            <form @submit.prevent="salvarObjetivo(objetivo.objetivo_id)">
                                <div class="campo-formulario">
                                    <label :for="`objetivo-${objetivo.objetivo_id}`">
                                        Texto do objetivo
                                    </label>

                                    <textarea :id="`objetivo-${objetivo.objetivo_id}`" v-model="textoObjetivo" rows="8"
                                        maxlength="30000" required
                                        :disabled="salvandoObjetivo || conflitoObjetivo"></textarea>
                                </div>

                                <div v-if="erroObjetivo" class="mensagem-erro" role="alert">
                                    <p>{{ erroObjetivo }}</p>

                                    <button v-if="conflitoObjetivo" type="button" class="botao"
                                        @click="descartarObjetivoERecarregar">
                                        Descartar e atualizar ementa
                                    </button>
                                </div>

                                <div class="botoes-formulario">
                                    <button type="button" class="botao-cancelar" :disabled="salvandoObjetivo"
                                        @click="cancelarEdicaoObjetivo">
                                        Cancelar
                                    </button>

                                    <button type="submit" class="botao"
                                        :disabled="salvandoObjetivo || conflitoObjetivo">
                                        {{
                                            salvandoObjetivo
                                                ? 'Salvando...'
                                                : 'Salvar objetivo'
                                        }}
                                    </button>
                                </div>
                            </form>
                        </template>

                        <p v-else class="texto-conteudo">
                            {{ objetivo.texto }}
                        </p>
                    </article>
                </div>
            </section>

            <!-- CONTEÚDO PROGRAMÁTICO -->
            <section class="cartao">
                <div class="secao-cabecalho">
                    <h2>Conteúdo programático</h2>
                    <span class="contador">
                        {{ ementa.conteudos_programaticos?.length || 0 }} tópico(s)
                    </span>
                </div>

                <div v-if="!ementa.conteudos_programaticos?.length" class="sem-informacao">
                    Nenhum conteúdo programático cadastrado.
                </div>

                <div v-else class="lista-conteudos">
                    <div v-for="conteudo in ementa.conteudos_programaticos" :key="conteudo.conteudo_id"
                        class="linha-conteudo">
                        <span class="numero-conteudo">
                            {{ conteudo.ordem }}
                        </span>

                        <div class="corpo-conteudo">
                            <div class="topico-cabecalho">
                                <div class="topico-textos">
                                    <strong v-if="conteudo.titulo" class="topico-titulo">
                                        {{ conteudo.titulo }}
                                    </strong>

                                    <p v-if="conteudoEditandoId !== conteudo.conteudo_id" class="texto-conteudo">
                                        {{ conteudo.texto }}
                                    </p>
                                </div>

                                <button v-if="
                                    conteudoEditandoId === null &&
                                    objetivoEditandoId === null &&
                                    bibliografiaEditandoId === null &&
                                    !editando &&
                                    ['RASCUNHO', 'EM_REVISAO'].includes(ementa.status)
                                " type="button" class="botao-editar-item" @click="iniciarEdicaoConteudo(conteudo)">
                                    Editar tópico
                                </button>
                            </div>

                            <form v-if="conteudoEditandoId === conteudo.conteudo_id"
                                @submit.prevent="salvarConteudo(conteudo.conteudo_id)">
                                <div class="campo-formulario">
                                    <label :for="`conteudo-${conteudo.conteudo_id}`">
                                        Texto do tópico
                                    </label>

                                    <textarea :id="`conteudo-${conteudo.conteudo_id}`" v-model="textoConteudo" rows="4"
                                        maxlength="30000" required
                                        :disabled="salvandoConteudo || conflitoConteudo"></textarea>
                                </div>

                                <div v-if="erroConteudo" class="mensagem-erro" role="alert">
                                    <p>{{ erroConteudo }}</p>

                                    <button v-if="conflitoConteudo" type="button" class="botao"
                                        @click="descartarConteudoERecarregar">
                                        Descartar e atualizar ementa
                                    </button>
                                </div>

                                <div class="botoes-formulario">
                                    <button type="button" class="botao-cancelar" :disabled="salvandoConteudo"
                                        @click="cancelarEdicaoConteudo">
                                        Cancelar
                                    </button>

                                    <button type="submit" class="botao"
                                        :disabled="salvandoConteudo || conflitoConteudo">
                                        {{ salvandoConteudo ? 'Salvando...' : 'Salvar tópico' }}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </section>


            <!-- BIBLIOGRAFIA -->
            <section class="cartao">
                <div class="secao-cabecalho">
                    <h2>Referências bibliográficas</h2>

                    <span class="contador">
                        {{ ementa.bibliografias?.length || 0 }} grupo(s)
                    </span>
                </div>

                <div v-if="!ementa.bibliografias?.length" class="sem-informacao">
                    Nenhuma referência bibliográfica cadastrada.
                </div>

                <div v-else class="grupo-itens">
                    <article v-for="bibliografia in ementa.bibliografias" :key="bibliografia.bibliografia_id"
                        class="item-conteudo">
                        <div class="bibliografia-cabecalho">
                            <h3>
                                {{
                                    bibliografia.tipo === 'BASICA'
                                        ? 'Bibliografia básica'
                                        : bibliografia.tipo === 'COMPLEMENTAR'
                                            ? 'Bibliografia complementar'
                                            : bibliografia.tipo
                                }}
                            </h3>

                            <button v-if="
                                !editando &&
                                objetivoEditandoId === null &&
                                conteudoEditandoId === null &&
                                bibliografiaEditandoId === null &&
                                ['RASCUNHO', 'EM_REVISAO'].includes(ementa.status)
                            " type="button" class="botao-editar-item" @click="iniciarEdicaoBibliografia(bibliografia)">
                                Editar bibliografia
                            </button>
                        </div>

                        <form v-if="bibliografiaEditandoId === bibliografia.bibliografia_id"
                            @submit.prevent="salvarBibliografia(bibliografia.bibliografia_id)">
                            <div class="campo-formulario">
                                <label :for="`bibliografia-${bibliografia.bibliografia_id}`">
                                    Referências bibliográficas
                                </label>

                                <textarea :id="`bibliografia-${bibliografia.bibliografia_id}`"
                                    v-model="textoBibliografia" rows="12" maxlength="30000" required
                                    :disabled="salvandoBibliografia || conflitoBibliografia"></textarea>

                                <p class="aviso-formulario">
                                    Preserve cada referência bibliográfica e suas informações.
                                    Você pode utilizar quebras de linha para separá-las.
                                </p>
                            </div>

                            <div v-if="erroBibliografia" class="mensagem-erro" role="alert">
                                <p>{{ erroBibliografia }}</p>

                                <button v-if="conflitoBibliografia" type="button" class="botao"
                                    @click="descartarBibliografiaERecarregar">
                                    Descartar alterações e atualizar ementa
                                </button>
                            </div>

                            <div class="botoes-formulario">
                                <button type="button" class="botao-cancelar" :disabled="salvandoBibliografia"
                                    @click="cancelarEdicaoBibliografia">
                                    Cancelar
                                </button>

                                <button type="submit" class="botao"
                                    :disabled="salvandoBibliografia || conflitoBibliografia">
                                    {{
                                        salvandoBibliografia
                                            ? 'Salvando...'
                                            : 'Salvar bibliografia'
                                    }}
                                </button>
                            </div>
                        </form>

                        <template v-else>
                            <p class="texto-conteudo">
                                {{ bibliografia.referencia }}
                            </p>

                            <p v-if="bibliografia.isbn" class="isbn">
                                ISBN: {{ bibliografia.isbn }}
                            </p>
                        </template>
                    </article>
                </div>
            </section>

            <!-- INFORMAÇÕES DO REGISTRO -->
            <section class="cartao">
                <h2>Informações do registro</h2>

                <div class="dados">
                    <div>
                        <span class="rotulo">IDENTIFICADOR DA EMENTA</span>
                        <strong>{{ ementa.ementa_id }}</strong>
                    </div>
                    <div>
                        <span class="rotulo">CRIADA EM</span>
                        <strong>{{ formatarData(ementa.criado_em) }}</strong>
                    </div>
                    <div>
                        <span class="rotulo">ATUALIZADA EM</span>
                        <strong>{{ formatarData(ementa.atualizado_em) }}</strong>
                    </div>
                </div>
            </section>
        </template>
    </main>
</template>

<style scoped>
/* ESTRUTURA E TIPOGRAFIA */
.pagina {
    width: min(100% - 32px, 1100px);
    margin: 40px auto;
    padding: 0 0 40px;
    box-sizing: border-box;
}

.voltar {
    display: inline-block;
    margin-bottom: 28px;
    color: #24548d;
    font-size: 14px;
    font-weight: 600;
    text-decoration: none;
}

.voltar:hover {
    text-decoration: underline;
}

.cabecalho,
.titulo-disciplina {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 20px;
}

.cabecalho {
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
    margin: 10px 0;
    color: #16345b;
    font-size: 30px;
}

h2 {
    margin: 0 0 18px;
    color: #16345b;
    font-size: 21px;
}

.cabecalho p,
.titulo-disciplina p {
    color: #64748b;
    line-height: 1.6;
}

.cartao {
    margin-bottom: 22px;
    padding: 28px;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    background: #fff;
}

.texto-conteudo {
    margin: 0;
    color: #34465e;
    line-height: 1.75;
    white-space: pre-line;
    overflow-wrap: anywhere;
}

/* IDENTIFICAÇÃO, STATUS E DADOS DA EMENTA */
.titulo-disciplina h2 {
    margin: 12px 0;
    font-size: 25px;
}

.status {
    padding: 8px 14px;
    border-radius: 25px;
    background: #fff5df;
    color: #91630a;
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
}

.status.publicada {
    background: #eaf7ef;
    color: #22633e;
}

.dados {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 24px;
    margin-top: 24px;
}

.dados>div {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.dados strong {
    color: #34465e;
    font-size: 14px;
    overflow-wrap: anywhere;
}

.cargas {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
}

.carga {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 22px;
    border-radius: 12px;
    background: #f5f8fc;
}

.carga span {
    color: #64748b;
    font-size: 13px;
}

.carga strong {
    color: #16345b;
    font-size: 25px;
}

.observacao {
    margin: 18px 0 0;
    color: #64748b;
    font-size: 12px;
}

/* CABEÇALHO DAS SEÇÕES E ITENS ACADÊMICOS */
.secao-cabecalho {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
}

.secao-cabecalho h2 {
    margin: 0;
}

.contador {
    color: #64748b;
    font-size: 12px;
    white-space: nowrap;
}

.grupo-itens {
    display: flex;
    flex-direction: column;
    gap: 18px;
}

.item-conteudo {
    padding: 20px;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    background: #fafcff;
}

.item-conteudo h3 {
    margin: 0 0 15px;
    color: #16345b;
    font-size: 16px;
}

.tipo-item {
    display: inline-block;
    color: #527197;
    font-size: 12px;
    font-weight: 700;
}

.objetivo-cabecalho {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
}

.sem-informacao {
    padding: 15px 0;
    color: #94a3b8;
    font-size: 14px;
}

.isbn {
    margin: 15px 0 0;
    color: #64748b;
    font-size: 12px;
}

/* CONTEÚDO PROGRAMÁTICO: NUMERAÇÃO ÚNICA */
.lista-conteudos {
    display: flex;
    flex-direction: column;
    margin: 0;
    padding: 0;
}

.linha-conteudo {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 18px 0;
    border-bottom: 1px solid #edf0f5;
}

.linha-conteudo:last-child {
    border-bottom: none;
}

.numero-conteudo {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 40px;
    height: 40px;
    border-radius: 10px;
    background: #edf4fc;
    color: #24548d;
    font-size: 14px;
    font-weight: 700;
}

.corpo-conteudo {
    flex: 1;
    min-width: 0;
}

.topico-cabecalho {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;
    width: 100%;
}

.topico-textos {
    flex: 1;
    min-width: 0;
    padding-top: 8px;
}

.topico-titulo {
    display: block;
    margin-bottom: 6px;
    color: #16345b;
}

.topico-textos .texto-conteudo {
    margin: 0;
    line-height: 1.6;
}

.topico-cabecalho .botao-editar-item {
    flex-shrink: 0;
    margin-left: auto;
}

/* BOTÕES E AÇÕES DE REVISÃO */
.botao,
.botao-cancelar,
.botao-editar-item {
    font: inherit;
    cursor: pointer;
    transition: background-color 0.15s ease;
}

.botao {
    padding: 12px 18px;
    border: none;
    border-radius: 9px;
    background: #1e477b;
    color: white;
}

.botao:hover:not(:disabled) {
    background: #16345b;
}

.botao-cancelar {
    padding: 12px 20px;
    border: 1px solid #cbd5e1;
    border-radius: 9px;
    background: white;
    color: #34465e;
}

.botao-cancelar:hover:not(:disabled) {
    background: #f1f5f9;
}

.botao-editar-item {
    padding: 8px 12px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    background: #fff;
    color: #24548d;
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
}

.botao-editar-item:hover:not(:disabled) {
    background: #edf4fc;
}

.botao:disabled,
.botao-cancelar:disabled,
.botao-editar-item:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.acoes-edicao {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    margin-bottom: 22px;
    padding: 24px;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    background: #f5f8fc;
}

.acoes-edicao h2 {
    margin: 0 0 8px;
}

.acoes-edicao p {
    margin: 0;
    color: #64748b;
    font-size: 14px;
}

.aviso-somente-leitura,
.aviso-formulario {
    color: #64748b;
    font-size: 13px;
    line-height: 1.7;
}

/* FORMULÁRIOS DE EDIÇÃO */
.formulario-edicao {
    border-color: #b8cce3;
}

.formulario-edicao h3 {
    margin-top: 28px;
    color: #16345b;
    font-size: 17px;
}

.campo-formulario {
    display: flex;
    flex-direction: column;
    gap: 9px;
    margin-bottom: 22px;
}

.campo-formulario label {
    color: #34465e;
    font-size: 14px;
    font-weight: 600;
}

.campo-formulario textarea,
.campo-formulario input {
    width: 100%;
    box-sizing: border-box;
    padding: 13px;
    border: 1px solid #cbd5e1;
    border-radius: 9px;
    background: white;
    color: #25354b;
    font: inherit;
}

.campo-formulario textarea:focus,
.campo-formulario input:focus {
    outline: 2px solid #93b4d9;
    border-color: #24548d;
}

.campo-formulario textarea:disabled,
.campo-formulario input:disabled {
    background: #f1f5f9;
    cursor: not-allowed;
}

.campos-carga {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
}

.botoes-formulario {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 28px;
}

/* MENSAGENS E FEEDBACK */
.mensagem {
    padding: 45px 24px;
    border: 1px solid #e2e8f0;
    border-radius: 15px;
    background: #fff;
    color: #64748b;
    text-align: center;
}

.mensagem.erro {
    background: #fff5f5;
    color: #922f2f;
}

.mensagem-sucesso,
.mensagem-erro {
    margin-bottom: 20px;
    padding: 16px 20px;
    border-radius: 10px;
}

.mensagem-sucesso {
    background: #ecfdf3;
    color: #166534;
}

.mensagem-erro {
    background: #fef2f2;
    color: #991b1b;
}

.mensagem-erro button {
    margin-top: 10px;
}

/* BIBLIOGRAFIAS */

.bibliografia-cabecalho {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 18px;
}

.bibliografia-cabecalho h3 {
    margin: 0;
    color: #16345b;
    font-size: 16px;
}

.bibliografia-cabecalho .botao-editar-item {
    flex-shrink: 0;
    margin-left: auto;
}


/* RESPONSIVIDADE */
@media (max-width: 650px) {
    .pagina {
        width: min(100% - 24px, 1100px);
        margin-top: 24px;
    }

    .cabecalho,
    .titulo-disciplina,
    .acoes-edicao {
        flex-direction: column;
        align-items: stretch;
    }

    .dados,
    .cargas,
    .campos-carga {
        grid-template-columns: 1fr;
    }

    .cartao {
        padding: 20px;
    }

    h1 {
        font-size: 25px;
    }

    .objetivo-cabecalho {
        flex-wrap: wrap;
        align-items: flex-start;
    }

    .botoes-formulario {
        flex-direction: column;
    }

    .bibliografia-cabecalho {
        flex-wrap: wrap;
    }

    .topico-cabecalho {
        gap: 10px;
    }

    .topico-cabecalho .botao-editar-item {
        font-size: 11px;
        padding: 7px 9px;
    }
}
</style>
