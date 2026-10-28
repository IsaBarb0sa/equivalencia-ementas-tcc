<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
    listarCursosCoordenador,
    listarMatrizesCoordenador,
    listarDisciplinasMatriz,
} from '../services/ementasInstitucionais'

const cursos = ref([])
const matrizes = ref([])
const disciplinas = ref([])

const cursoId = ref('')
const matrizId = ref('')
const pesquisa = ref('')

const carregandoCursos = ref(false)
const carregandoMatrizes = ref(false)
const carregandoDisciplinas = ref(false)

const erro = ref('')

let consultaMatriz = 0
let consultaDisciplinas = 0

const matrizSelecionada = computed(() =>
    matrizes.value.find(
        (matriz) => String(matriz.matriz_curricular_id) === matrizId.value
    )
)

const total = computed(() => disciplinas.value.length)

const comEmenta = computed(() =>
    disciplinas.value.filter((disciplina) => disciplina.quantidade_ementas > 0)
        .length
)

const semEmenta = computed(() => total.value - comEmenta.value)

const emRevisao = computed(() =>
    disciplinas.value.filter(
        (disciplina) => disciplina.status_ementa === 'EM_REVISAO'
    ).length
)

const disciplinasFiltradas = computed(() => {
    const termo = pesquisa.value.trim().toLocaleLowerCase('pt-BR')

    if (!termo) return disciplinas.value

    return disciplinas.value.filter((disciplina) => {
        return (
            disciplina.nome.toLocaleLowerCase('pt-BR').includes(termo) ||
            disciplina.codigo.toLocaleLowerCase('pt-BR').includes(termo)
        )
    })
})

function formatarStatus(status) {
    const nomes = {
        RASCUNHO: 'Rascunho',
        EM_REVISAO: 'Em revisão',
        PUBLICADA: 'Publicada',
        ARQUIVADA: 'Arquivada',
        ATIVA: 'Ativa',
        INATIVA: 'Inativa',
    }

    return nomes[status] || status || 'Não informado'
}

function formatarNatureza(natureza) {
    const nomes = {
        OBRIGATORIA: 'Obrigatória',
        OPTATIVA: 'Optativa',
        ELETIVA: 'Eletiva',
        OUTRA: 'Outra',
    }

    return nomes[natureza] || natureza
}

function formatarCarga(valor) {
    if (valor === null || valor === undefined) {
        return 'Não informada'
    }

    return `${Number(valor).toLocaleString('pt-BR')} h`
}

async function carregarCursos() {
    carregandoCursos.value = true
    erro.value = ''

    try {
        cursos.value = await listarCursosCoordenador()

        if (cursos.value.length > 0) {
            cursoId.value = String(cursos.value[0].curso_id)
        }
    } catch (excecao) {
        erro.value = excecao.message
    } finally {
        carregandoCursos.value = false
    }
}

watch(cursoId, async (novoCursoId) => {
    const versao = ++consultaMatriz
    ++consultaDisciplinas

    matrizes.value = []
    disciplinas.value = []
    matrizId.value = ''
    pesquisa.value = ''
    erro.value = ''

    if (!novoCursoId) return

    carregandoMatrizes.value = true

    try {
        const resultado = await listarMatrizesCoordenador(novoCursoId)
        if (versao !== consultaMatriz) return

        matrizes.value = resultado

        if (resultado.length > 0) {
            matrizId.value = String(resultado[0].matriz_curricular_id)
        }
    } catch (excecao) {
        if (versao === consultaMatriz) erro.value = excecao.message
    } finally {
        if (versao === consultaMatriz) carregandoMatrizes.value = false
    }
})

watch(matrizId, async (novaMatrizId) => {
    const versao = ++consultaDisciplinas

    disciplinas.value = []
    pesquisa.value = ''
    erro.value = ''

    if (!novaMatrizId) return

    carregandoDisciplinas.value = true

    try {
        const resultado = await listarDisciplinasMatriz(novaMatrizId)

        if (versao !== consultaDisciplinas) return

        disciplinas.value = resultado
    } catch (excecao) {
        if (versao === consultaDisciplinas) erro.value = excecao.message
    } finally {
        if (versao === consultaDisciplinas) {
            carregandoDisciplinas.value = false
        }
    }
})


async function atualizar() {
    if (!matrizId.value) {
        await carregarCursos()
        return
    }

    const versao = ++consultaDisciplinas

    carregandoDisciplinas.value = true
    erro.value = ''

    try {
        const resultado = await listarDisciplinasMatriz(matrizId.value)

        if (versao === consultaDisciplinas) {
            disciplinas.value = resultado
        }
    } catch (excecao) {
        if (versao === consultaDisciplinas) {
            erro.value = excecao.message
        }
    } finally {
        if (versao === consultaDisciplinas) {
            carregandoDisciplinas.value = false
        }
    }
}


onMounted(carregarCursos)
</script>

<template>
    <main class="pagina">
        <RouterLink to="/coordenacao" class="voltar">
            ← Voltar ao painel
        </RouterLink>

        <header class="cabecalho">
            <div>
                <span class="subtitulo">ÁREA DA COORDENAÇÃO</span>
                <h1>Ementas institucionais</h1>
                <p>
                    Consulte as matrizes curriculares e acompanhe as ementas
                    das disciplinas dos seus cursos.
                </p>
            </div>
        </header>

        <section class="cartao selecao">
            <div class="campo">
                <label for="curso">Curso</label>

                <select id="curso" v-model="cursoId" :disabled="carregandoCursos || cursos.length === 0">
                    <option value="">Selecione um curso</option>
                    <option v-for="curso in cursos" :key="curso.curso_id" :value="String(curso.curso_id)">
                        {{ curso.nome }}
                    </option>
                </select>
            </div>

            <div class="campo">
                <label for="matriz">Matriz curricular</label>

                <select id="matriz" v-model="matrizId" :disabled="carregandoMatrizes || matrizes.length === 0">
                    <option value="">Selecione uma matriz</option>
                    <option v-for="matriz in matrizes" :key="matriz.matriz_curricular_id"
                        :value="String(matriz.matriz_curricular_id)">
                        {{ matriz.nome || matriz.codigo }} — {{ matriz.codigo }}
                    </option>
                </select>
            </div>

            <p v-if="matrizSelecionada" class="info-matriz">
                Situação da matriz:
                <strong>{{ formatarStatus(matrizSelecionada.status) }}</strong>
            </p>
        </section>

        <section v-if="!carregandoDisciplinas && matrizId && !erro" class="resumo">
            <div class="indicador">
                <span>Disciplinas</span>
                <strong>{{ total }}</strong>
            </div>

            <div class="indicador">
                <span>Com ementa</span>
                <strong>{{ comEmenta }}</strong>
            </div>

            <div class="indicador">
                <span>Sem ementa</span>
                <strong>{{ semEmenta }}</strong>
            </div>

            <div class="indicador">
                <span>Em revisão</span>
                <strong>{{ emRevisao }}</strong>
            </div>
        </section>

        <section v-if="erro" class="mensagem erro" role="alert">
            <strong>Não foi possível carregar as informações.</strong>
            <p>{{ erro }}</p>
            <button type="button" @click="atualizar">Tentar novamente</button>
        </section>

        <section v-else-if="carregandoCursos || carregandoMatrizes || carregandoDisciplinas" class="mensagem">
            Carregando informações institucionais...
        </section>

        <section v-else-if="cursos.length === 0" class="mensagem">
            Nenhum curso vinculado à sua conta.
        </section>

        <section v-else-if="matrizes.length === 0" class="mensagem">
            Nenhuma matriz curricular encontrada para o curso selecionado.
        </section>

        <section v-else-if="matrizId" class="cartao">
            <div class="lista-cabecalho">
                <div>
                    <h2>Disciplinas da matriz</h2>
                    <p>
                        {{ disciplinasFiltradas.length }} de
                        {{ disciplinas.length }} disciplinas
                    </p>
                </div>

                <input v-model="pesquisa" type="search" placeholder="Pesquisar disciplina ou código..."
                    aria-label="Pesquisar disciplina ou código" />
            </div>

            <div v-if="disciplinas.length === 0" class="mensagem-interna">
                Esta matriz ainda não possui disciplinas vinculadas.
            </div>

            <div v-else-if="disciplinasFiltradas.length === 0" class="mensagem-interna">
                Nenhuma disciplina encontrada para essa pesquisa.
            </div>

            <div v-else class="lista">
                <article v-for="disciplina in disciplinasFiltradas" :key="disciplina.matriz_disciplina_id"
                    class="disciplina">
                    <div class="disciplina-principal">
                        <span class="codigo">CÓDIGO {{ disciplina.codigo }}</span>
                        <h3>{{ disciplina.nome }}</h3>

                        <p>
                            {{ formatarNatureza(disciplina.natureza) }}
                            · {{ formatarCarga(disciplina.carga_horaria) }}
                            <template v-if="disciplina.periodo_sugerido">
                                · {{ disciplina.periodo_sugerido }}º período
                            </template>
                        </p>
                    </div>

                    <div class="disciplina-status">
                        <span class="etiqueta" :class="{
                            'sem-ementa': disciplina.quantidade_ementas === 0,
                            publicada: disciplina.status_ementa === 'PUBLICADA',
                        }">
                            {{
                                disciplina.quantidade_ementas === 0
                                    ? 'Sem ementa'
                                    : formatarStatus(disciplina.status_ementa)
                            }}
                        </span>

                        <small>
                            {{ disciplina.quantidade_ementas }}
                            versão(ões)
                        </small>

                        <RouterLink v-if="disciplina.ementa_id" :to="{
                            name: 'detalhe-ementa-institucional',
                            params: {
                                matrizDisciplinaId: disciplina.matriz_disciplina_id,
                                ementaId: disciplina.ementa_id,
                            },
                        }" class="botao-visualizar">
                            Visualizar ementa →
                        </RouterLink>

                        <span v-else class="sem-cadastro">
                            Ementa não cadastrada
                        </span>

                    </div>
                </article>
            </div>
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
    color: #24548d;
    font-weight: 600;
    font-size: 14px;
    text-decoration: none;
    margin-bottom: 28px;
}

.cabecalho {
    margin-bottom: 28px;
}

.subtitulo,
.codigo {
    font-size: 11px;
    letter-spacing: 1px;
    color: #6481a1;
    font-weight: 700;
}

h1 {
    font-size: 30px;
    color: #16345b;
    margin: 10px 0;
}

.cabecalho p,
.lista-cabecalho p {
    color: #64748b;
    line-height: 1.6;
}

.cartao,
.indicador {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 15px;
    padding: 25px;
}

.selecao {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 22px;
}

.campo label {
    display: block;
    font-size: 13px;
    color: #34465e;
    font-weight: 600;
    margin-bottom: 9px;
}

.campo select {
    width: 100%;
    padding: 12px;
    background: white;
    border: 1px solid #d4deea;
    border-radius: 9px;
    color: #16345b;
    font-size: 14px;
}

.info-matriz {
    grid-column: 1 / -1;
    margin: 0;
    color: #64748b;
    font-size: 13px;
}

.resumo {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 22px;
}

.indicador span {
    display: block;
    font-size: 12px;
    color: #64748b;
    margin-bottom: 12px;
}

.indicador strong {
    font-size: 29px;
    color: #16345b;
}

.lista-cabecalho {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    margin-bottom: 22px;
}

h2 {
    font-size: 21px;
    color: #16345b;
    margin: 0;
}

.lista-cabecalho p {
    font-size: 13px;
    margin: 8px 0 0;
}

.lista-cabecalho input {
    width: 310px;
    max-width: 100%;
    padding: 12px;
    border: 1px solid #d4deea;
    border-radius: 9px;
    font-size: 13px;
}

.lista {
    display: flex;
    flex-direction: column;
}

.disciplina {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    padding: 20px 0;
    border-top: 1px solid #edf0f5;
}

.disciplina h3 {
    font-size: 17px;
    color: #16345b;
    margin: 8px 0;
}

.disciplina p {
    font-size: 13px;
    color: #64748b;
    margin: 0;
}

.disciplina-status {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
    flex-shrink: 0;
}

.etiqueta {
    padding: 7px 12px;
    background: #fff5df;
    color: #91630a;
    font-size: 12px;
    font-weight: 600;
    border-radius: 20px;
}

.etiqueta.publicada {
    background: #eaf7ef;
    color: #22633e;
}

.etiqueta.sem-ementa {
    background: #f1f5f9;
    color: #64748b;
}

.disciplina-status small {
    font-size: 11px;
    color: #94a3b8;
}

.mensagem,
.mensagem-interna {
    text-align: center;
    padding: 35px;
    color: #64748b;
}

.mensagem {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 15px;
}

.mensagem.erro {
    background: #fff5f5;
    color: #922f2f;
}

.mensagem button {
    margin-top: 12px;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    background: #1e477b;
    color: white;
    cursor: pointer;
}

@media (max-width: 750px) {

    .selecao,
    .resumo {
        grid-template-columns: 1fr 1fr;
    }

    .lista-cabecalho,
    .disciplina {
        align-items: flex-start;
        flex-direction: column;
    }

    .disciplina-status {
        align-items: flex-start;
    }
}

@media (max-width: 500px) {

    .selecao,
    .resumo {
        grid-template-columns: 1fr;
    }

    .info-matriz {
        grid-column: auto;
    }
}

.botao-visualizar {
    display: inline-block;
    margin-top: 5px;
    padding: 9px 14px;
    background: #1e477b;
    color: white;
    border-radius: 9px;
    font-size: 12px;
    font-weight: 600;
    text-decoration: none;
}

.botao-visualizar:hover {
    background: #16345b;
}

.sem-cadastro {
    color: #94a3b8;
    font-size: 12px;
}
</style>
