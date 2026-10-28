<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { cadastrarCandidato } from '../services/auth'

const router = useRouter()

const nomeCompleto = ref('')
const cpf = ref('')
const email = ref('')
const senha = ref('')
const confirmarSenha = ref('')

const mostrarSenha = ref(false)
const enviando = ref(false)
const erro = ref('')

function formatarCpf(evento) {
    let numeros = evento.target.value.replace(/\D/g, '').slice(0, 11)

    numeros = numeros.replace(/^(\d{3})(\d)/, '$1.$2')
    numeros = numeros.replace(/^(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
    numeros = numeros.replace(/\.(\d{3})\.(\d{3})(\d)/, '.$1.$2-$3')

    cpf.value = numeros
}

async function fazerCadastro() {
    if (enviando.value) return

    erro.value = ''

    if (nomeCompleto.value.trim().length < 3) {
        erro.value = 'Informe seu nome completo.'
        return
    }

    if (cpf.value.replace(/\D/g, '').length !== 11) {
        erro.value = 'O CPF deve conter 11 dígitos.'
        return
    }

    if (senha.value.length < 12) {
        erro.value = 'A senha deve conter pelo menos 12 caracteres.'
        return
    }

    if (senha.value !== confirmarSenha.value) {
        erro.value = 'As senhas informadas não coincidem.'
        return
    }

    enviando.value = true

    try {
        await cadastrarCandidato({
            nome_completo: nomeCompleto.value.trim(),
            cpf: cpf.value.replace(/\D/g, ''),
            email: email.value.trim().toLowerCase(),
            senha: senha.value,
        })

        senha.value = ''
        confirmarSenha.value = ''

        await router.replace({
            path: '/login',
            query: { cadastro: 'sucesso' },
        })
    } catch (excecao) {
        erro.value =
            excecao.message || 'Não foi possível realizar o cadastro.'
    } finally {
        enviando.value = false
    }
}
</script>

<template>
    <section class="cadastro-page">
        <div class="cadastro-card">
            <div class="cadastro-header">
                <div class="cadastro-icon" aria-hidden="true">E</div>

                <span class="eyebrow">APROVEITAMENTO DE ESTUDOS</span>

                <h1>Criar minha conta</h1>

                <p>
                    Cadastre-se para solicitar a análise de
                    equivalência das suas disciplinas.
                </p>
            </div>

            <form class="cadastro-form" @submit.prevent="fazerCadastro">
                <div class="field">
                    <label for="nome">Nome completo</label>

                    <input id="nome" v-model="nomeCompleto" type="text" autocomplete="name"
                        placeholder="Digite seu nome completo" maxlength="200" minlength="3" required
                        :disabled="enviando" />
                </div>

                <div class="fields-row">
                    <div class="field">
                        <label for="cpf">CPF</label>

                        <input id="cpf" v-model="cpf" type="text" inputmode="numeric" autocomplete="off"
                            placeholder="000.000.000-00" maxlength="14" required :disabled="enviando"
                            @input="formatarCpf" />
                    </div>

                    <div class="field">
                        <label for="email">E-mail</label>

                        <input id="email" v-model="email" type="email" autocomplete="email" placeholder="seu@email.com"
                            maxlength="254" required :disabled="enviando" />
                    </div>
                </div>

                <div class="field">
                    <label for="senha">Senha</label>

                    <div class="password-field">
                        <input id="senha" v-model="senha" :type="mostrarSenha ? 'text' : 'password'"
                            autocomplete="new-password" placeholder="Crie uma senha" minlength="12" maxlength="128"
                            required :disabled="enviando" />

                        <button type="button" class="toggle-password"
                            :aria-label="mostrarSenha ? 'Ocultar senha' : 'Mostrar senha'"
                            @click="mostrarSenha = !mostrarSenha">
                            {{ mostrarSenha ? 'Ocultar' : 'Mostrar' }}
                        </button>
                    </div>

                    <small>Utilize pelo menos 12 caracteres.</small>
                </div>

                <div class="field">
                    <label for="confirmar-senha">Confirmar senha</label>

                    <input id="confirmar-senha" v-model="confirmarSenha" :type="mostrarSenha ? 'text' : 'password'"
                        autocomplete="new-password" placeholder="Digite a senha novamente" minlength="12"
                        maxlength="128" required :disabled="enviando" />
                </div>

                <div v-if="erro" class="error-box" role="alert">
                    {{ erro }}
                </div>

                <button type="submit" class="primary-button" :disabled="enviando">
                    {{ enviando ? 'Criando conta...' : 'Criar conta' }}
                </button>
            </form>

            <div class="cadastro-footer">
                <p>Já possui uma conta?</p>

                <RouterLink to="/login">
                    Fazer login
                </RouterLink>
            </div>
        </div>
    </section>
</template>

<style scoped>
.cadastro-page {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 35px 16px 60px;
}

.cadastro-card {
    width: 100%;
    max-width: 560px;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 38px;
    box-shadow: 0 12px 35px rgba(22, 52, 91, 0.06);
}

.cadastro-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    margin-bottom: 30px;
}

.cadastro-icon {
    display: grid;
    place-items: center;
    width: 56px;
    height: 56px;
    background: #16345b;
    color: white;
    font-size: 27px;
    font-weight: 700;
    border-radius: 15px;
    margin-bottom: 20px;
}

.eyebrow {
    color: #527197;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.4px;
}

h1 {
    font-size: 29px;
    color: #16345b;
    margin: 13px 0 10px;
}

.cadastro-header p {
    font-size: 14px;
    color: #68778a;
    line-height: 1.7;
    margin: 0;
}

.cadastro-form {
    display: flex;
    flex-direction: column;
    gap: 19px;
}

.fields-row {
    display: grid;
    grid-template-columns: 1fr 1.2fr;
    gap: 16px;
}

.field {
    min-width: 0;
}

.field label {
    display: block;
    margin-bottom: 9px;
    font-size: 13px;
    font-weight: 600;
    color: #34465e;
}

.field input {
    box-sizing: border-box;
    width: 100%;
    padding: 13px 14px;
    border: 1px solid #cbd5e1;
    border-radius: 9px;
    color: #203047;
    background: white;
    outline: none;
    font-size: 14px;
}

.field input:focus {
    border-color: #4385e0;
    box-shadow: 0 0 0 3px rgba(67, 133, 224, 0.12);
}

.field input:disabled {
    background: #f8fafc;
}

.field small {
    display: block;
    margin-top: 7px;
    color: #758297;
    font-size: 12px;
}

.password-field {
    position: relative;
}

.password-field input {
    padding-right: 88px;
}

.toggle-password {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    border: none;
    background: transparent;
    padding: 7px;
    color: #527197;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
}

.error-box {
    padding: 13px;
    border-radius: 9px;
    background: #fff1f1;
    color: #922f2f;
    font-size: 13px;
}

.primary-button {
    width: 100%;
    padding: 14px 20px;
    border: none;
    border-radius: 9px;
    background: #1e477b;
    color: white;
    font-weight: 600;
    cursor: pointer;
    margin-top: 6px;
}

.primary-button:hover:not(:disabled) {
    background: #15365e;
}

.primary-button:disabled {
    opacity: 0.65;
    cursor: not-allowed;
}

.cadastro-footer {
    text-align: center;
    border-top: 1px solid #edf0f5;
    margin-top: 28px;
    padding-top: 20px;
    font-size: 13px;
    color: #68778a;
}

.cadastro-footer a {
    color: #24548d;
    font-weight: 600;
    text-decoration: none;
}

.cadastro-footer a:hover {
    text-decoration: underline;
}

@media (max-width: 600px) {
    .cadastro-card {
        padding: 25px 20px;
    }

    .fields-row {
        grid-template-columns: 1fr;
    }

    h1 {
        font-size: 25px;
    }
}
</style>
