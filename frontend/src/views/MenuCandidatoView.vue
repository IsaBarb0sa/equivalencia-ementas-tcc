<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { obterUsuarioAtual, sair } from '../services/auth'

const router = useRouter()
const usuario = ref(null)
const encerrando = ref(false)

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

    try {
        await sair()
        await router.replace('/login')
    } catch (erro) {
        alert(erro.message || 'Não foi possível sair.')
    } finally {
        encerrando.value = false
    }
}
</script>

<template>
    <main class="menu">
        <div class="menu-topo">
            <div>
                <span class="subtitulo">ÁREA DO CANDIDATO</span>
                <h1>Olá, {{ usuario?.nome_completo || 'candidato' }}!</h1>
                <p>
                    Acompanhe seus processos de aproveitamento
                    de disciplinas em um só lugar.
                </p>
            </div>

            <button class="botao-sair" :disabled="encerrando" @click="fazerLogout">
                {{ encerrando ? 'Saindo...' : 'Sair da conta' }}
            </button>
        </div>

        <div class="opcoes">
            <RouterLink to="/candidato/nova-solicitacao" class="cartao">
                <div class="icone">+</div>
                <h2>Nova solicitação</h2>
                <p>
                    Envie suas ementas em PDF para solicitar
                    a análise de equivalência.
                </p>
                <span class="acao">Iniciar solicitação →</span>
            </RouterLink>


            <RouterLink to="/candidato/minhas-solicitacoes" class="cartao">
                <div class="icone">▤</div>

                <h2>Minhas solicitações</h2>

                <p>
                    Consulte as solicitações que você enviou
                    e acompanhe o andamento de cada processo.
                </p>

                <span class="acao">
                    Visualizar minhas solicitações →
                </span>
            </RouterLink>

        </div>
    </main>
</template>

<style scoped>
.menu {
    max-width: 1100px;
    margin: 40px auto;
    padding: 20px;
}

.menu-topo {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 24px;
    margin-bottom: 40px;
}

.subtitulo {
    color: #5476a5;
    letter-spacing: 1.5px;
    font-size: 12px;
    font-weight: 700;
}

h1 {
    color: #16345b;
    font-size: 30px;
    margin: 12px 0;
}

.menu-topo p,
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
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 24px;
}

.cartao {
    display: flex;
    flex-direction: column;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 32px;
    text-decoration: none;
    transition: 0.2s;
}

a.cartao:hover {
    border-color: #7b9fd0;
    transform: translateY(-3px);
    box-shadow: 0 10px 25px rgba(22, 52, 91, 0.08);
}

.icone {
    width: 54px;
    height: 54px;
    display: grid;
    place-items: center;
    background: #e9f1fc;
    color: #1e477b;
    border-radius: 12px;
    font-size: 29px;
    font-weight: 600;
}

h2 {
    color: #16345b;
    margin: 22px 0 6px;
    font-size: 21px;
}

.acao {
    color: #24548d;
    font-weight: 600;
    margin-top: auto;
    padding-top: 26px;
    font-size: 14px;
}

.indisponivel {
    opacity: 0.65;
}

@media (max-width: 700px) {
    .menu-topo {
        flex-direction: column;
    }

    .opcoes {
        grid-template-columns: 1fr;
    }
}
</style>
