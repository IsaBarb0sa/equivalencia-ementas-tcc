<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { obterUsuarioAtual, sair } from '../services/auth'

const router = useRouter()

const usuario = ref(null)
const encerrando = ref(false)
const erro = ref('')

onMounted(async () => {
    try {
        usuario.value = await obterUsuarioAtual()
    } catch {
        await router.replace('/login')
    }
})

async function fazerLogout() {
    if (encerrando.value) return

    encerrando.value = true
    erro.value = ''

    try {
        await sair()
        await router.replace('/login')
    } catch (excecao) {
        erro.value =
            excecao.message || 'Não foi possível encerrar a sessão.'
    } finally {
        encerrando.value = false
    }
}
</script>

<template>
    <main class="painel">
        <div class="cabecalho">
            <div>
                <span class="identificacao">ÁREA DA COORDENAÇÃO</span>

                <h1>Olá, {{ usuario?.nome_completo || 'coordenador' }}!</h1>

                <p>
                    Gerencie as solicitações de equivalência
                    e as ementas dos cursos sob sua responsabilidade.
                </p>
            </div>

            <button class="botao-sair" type="button" :disabled="encerrando" @click="fazerLogout">
                {{ encerrando ? 'Saindo...' : 'Sair da conta' }}
            </button>
        </div>

        <p v-if="erro" class="erro" role="alert">
            {{ erro }}
        </p>

        <div class="opcoes">

            <RouterLink to="/coordenacao/solicitacoes" class="cartao cartao-ativo">
                <div class="icone">▤</div>

                <h2>Solicitações recebidas</h2>

                <p>
                    Consulte e acompanhe os processos de equivalência
                    destinados aos cursos sob sua responsabilidade.
                </p>

                <span class="acao">
                    Visualizar solicitações →
                </span>
            </RouterLink>



            <RouterLink to="/coordenacao/ementas" class="cartao cartao-ativo">
                <div class="icone">▧</div>

                <h2>Ementas institucionais</h2>

                <p>
                    Consulte as matrizes curriculares e acompanhe
                    as ementas das disciplinas dos seus cursos.
                </p>

                <span class="acao">
                    Consultar ementas →
                </span>
            </RouterLink>


            <div class="cartao indisponivel">
                <div class="icone">◇</div>
                <h2>Análises de equivalência</h2>
                <p>
                    Revise as sugestões de equivalência
                    produzidas pelo sistema.
                </p>
                <span class="acao">Em desenvolvimento</span>
            </div>
        </div>
    </main>
</template>

<style scoped>
.painel {
    max-width: 1100px;
    margin: 40px auto;
    padding: 20px;
}

.cabecalho {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 24px;
    margin-bottom: 40px;
}

.identificacao {
    color: #527197;
    font-size: 12px;
    letter-spacing: 1.4px;
    font-weight: 700;
}

h1 {
    font-size: 30px;
    color: #16345b;
    margin: 12px 0;
}

.cabecalho p,
.cartao p {
    color: #64748b;
    line-height: 1.7;
}

.botao-sair {
    padding: 11px 18px;
    background: white;
    border: 1px solid #d2dce9;
    border-radius: 9px;
    color: #16345b;
    cursor: pointer;
    white-space: nowrap;
}

.opcoes {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 22px;
}

.cartao {
    display: flex;
    flex-direction: column;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 30px;
    min-height: 245px;
}

.icone {
    width: 54px;
    height: 54px;
    display: grid;
    place-items: center;
    background: #e9f1fc;
    color: #1e477b;
    border-radius: 12px;
    font-size: 28px;
}

h2 {
    font-size: 20px;
    color: #16345b;
    margin: 22px 0 8px;
}

.acao {
    margin-top: auto;
    padding-top: 22px;
    color: #527197;
    font-size: 13px;
    font-weight: 600;
}

.indisponivel {
    opacity: 0.7;
}

.erro {
    color: #922f2f;
    background: #fff1f1;
    border-radius: 9px;
    padding: 12px;
    margin-bottom: 20px;
}

.cartao-ativo {
    text-decoration: none;
    transition: 0.2s;
}

.cartao-ativo:hover {
    border-color: #7b9fd0;
    transform: translateY(-3px);
    box-shadow: 0 10px 25px rgba(22, 52, 91, 0.08);
}

@media (max-width: 850px) {
    .opcoes {
        grid-template-columns: 1fr 1fr;
    }
}

@media (max-width: 600px) {
    .cabecalho {
        flex-direction: column;
    }

    .opcoes {
        grid-template-columns: 1fr;
    }

    h1 {
        font-size: 25px;
    }
}
</style>
