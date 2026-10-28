<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { entrar } from '../services/auth'

const router = useRouter()
const route = useRoute()

const identificador = ref('')
const senha = ref('')
const mostrarSenha = ref(false)
const enviando = ref(false)
const erro = ref('')

async function fazerLogin() {
    if (enviando.value) return

    erro.value = ''
    enviando.value = true

    try {
        const usuario = await entrar(
            identificador.value.trim(),
            senha.value
        )

        senha.value = ''


        if (usuario.perfil === 'CANDIDATO') {
            await router.replace('/candidato')
        } else if (usuario.perfil === 'COORDENADOR') {
            await router.replace('/coordenacao')
        } else {
            erro.value = 'Este perfil ainda não possui uma área disponível.'
        }

    } catch (excecao) {
        erro.value = excecao.message || 'Falha ao realizar login.'
    } finally {
        enviando.value = false
    }
}
</script>

<template>
    <section class="login-page">
        <div class="login-card">
            <div class="login-header">
                <div class="login-icon" aria-hidden="true">E</div>

                <span class="eyebrow">APROVEITAMENTO DE ESTUDOS</span>
                <h1>Bem-vindo de volta</h1>

                <p>
                    Entre com seus dados para acessar o sistema
                    de equivalência de disciplinas.
                </p>
            </div>

            <div v-if="route.query.cadastro === 'sucesso'" class="success-box" role="status">
                Cadastro realizado com sucesso!
                Agora você pode entrar com seu CPF ou e-mail e senha.
            </div>

            <form class="login-form" @submit.prevent="fazerLogin">
                <div class="field">
                    <label for="identificador">CPF ou e-mail</label>

                    <input id="identificador" v-model="identificador" type="text" autocomplete="username"
                        placeholder="Digite seu CPF ou e-mail" maxlength="254" required :disabled="enviando" />
                </div>

                <div class="field">
                    <label for="senha">Senha</label>

                    <div class="password-field">
                        <input id="senha" v-model="senha" :type="mostrarSenha ? 'text' : 'password'"
                            autocomplete="current-password" placeholder="Digite sua senha" required
                            :disabled="enviando" />

                        <button type="button" class="toggle-password"
                            :aria-label="mostrarSenha ? 'Ocultar senha' : 'Mostrar senha'" :aria-pressed="mostrarSenha"
                            @click="mostrarSenha = !mostrarSenha">
                            {{ mostrarSenha ? 'Ocultar' : 'Mostrar' }}
                        </button>
                    </div>
                </div>

                <div v-if="erro" class="error-box" role="alert">
                    {{ erro }}
                </div>

                <button type="submit" class="primary-button" :disabled="enviando || !identificador.trim() || !senha">
                    {{ enviando ? 'Entrando...' : 'Entrar' }}
                </button>
            </form>

            <div class="login-footer">
                <p>Ainda não possui uma conta?</p>

                <RouterLink to="/cadastro" class="cadastro-link">
                    Cadastre-se
                </RouterLink>
            </div>
        </div>

        <p class="security-note">
            Suas credenciais são utilizadas exclusivamente para autenticação.
            Não compartilhe sua senha.
        </p>
    </section>
</template>

<style scoped>
.login-page {
    min-height: 65vh;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 22px;
}

.login-card {
    width: 100%;
    max-width: 460px;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 38px;
    box-shadow: 0 12px 35px rgba(22, 52, 91, 0.05);
}

.login-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    margin-bottom: 30px;
}

.login-icon {
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
    letter-spacing: -0.8px;
    color: #16345b;
    margin: 13px 0 10px;
}

.login-header p {
    font-size: 14px;
    color: #68778a;
    line-height: 1.7;
    margin: 0;
}

.login-form {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.field label {
    display: block;
    margin-bottom: 9px;
    font-size: 13px;
    font-weight: 600;
    color: #34465e;
}

.field input {
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

.password-field {
    position: relative;
}

.password-field input {
    padding-right: 90px;
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
    background: #dce3ed;
    color: #66758a;
    cursor: not-allowed;
}

.error-box {
    padding: 13px;
    border-radius: 9px;
    background: #fff1f1;
    color: #922f2f;
    font-size: 13px;
    line-height: 1.6;
}

.login-footer {
    border-top: 1px solid #edf0f5;
    margin-top: 28px;
    padding-top: 20px;
    text-align: center;
}

.login-footer p {
    font-size: 13px;
    line-height: 1.8;
    color: #68778a;
    margin: 0;
}

.login-footer span {
    color: #527197;
    display: block;
    font-size: 12px;
}

.security-note {
    text-align: center;
    color: #758297;
    font-size: 12px;
    line-height: 1.6;
    max-width: 420px;
}


.cadastro-link {
    display: inline-block;
    margin-top: 5px;
    color: #24548d;
    font-weight: 600;
    font-size: 14px;
    text-decoration: none;
}

.cadastro-link:hover {
    text-decoration: underline;
}


.success-box {
    padding: 14px;
    margin-bottom: 20px;
    border-radius: 9px;
    background: #edf8f1;
    border: 1px solid #b9e3c9;
    color: #21613c;
    font-size: 13px;
    line-height: 1.6;
}


@media (max-width: 480px) {
    .login-card {
        padding: 25px 20px;
    }

    h1 {
        font-size: 25px;
    }
}
</style>
