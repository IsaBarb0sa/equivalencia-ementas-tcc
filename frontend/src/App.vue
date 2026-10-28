<script setup>
import { RouterLink, RouterView } from 'vue-router'

import { useRoute } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()

const areaCoordenacao = computed(() =>
  route.path.startsWith('/coordenacao')
)

</script>

<template>
  <div class="app">
    <header class="header">
      <div class="header-content">

        <!-- IDENTIDADE DO SISTEMA -->
        <RouterLink to="/" class="brand">
          <span class="brand-icon" aria-hidden="true">E</span>
          <span>
            <strong>Equivalência</strong>
            <small>Aproveitamento de disciplinas</small>
          </span>
        </RouterLink>

        <!-- MENU DE NAVEGAÇÃO -->
        <nav v-if="!areaCoordenacao" class="navigation" aria-label="Navegação principal">
          <RouterLink to="/candidato/nova-solicitacao" class="nav-link" exact-active-class="nav-link-active">
            Nova solicitação
          </RouterLink>

          <RouterLink to="/candidato/minhas-solicitacoes" class="nav-link" exact-active-class="nav-link-active">
            Acompanhar solicitações
          </RouterLink>
        </nav>
      </div>
    </header>

    <!-- CONTEÚDO DAS PÁGINAS -->
    <main class="main">
      <RouterView />
    </main>

    <footer class="footer">
      A decisão sobre o aproveitamento de disciplinas depende
      da avaliação da coordenação.
    </footer>
  </div>
</template>

<style>
:root {
  font-family: 'Segoe UI', Arial, sans-serif;
  color: #203047;
  background: #f4f6fa;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}


.profile {
  text-decoration: none;
}


button,
input,
select {
  font: inherit;
}

button,
a,
select,
input {
  -webkit-tap-highlight-color: transparent;
}

:focus-visible {
  outline: 3px solid #4385e0;
  outline-offset: 4px;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* CABEÇALHO */

.header {
  background: white;
  border-bottom: 1px solid #e2e8f0;
}

.header-content {
  max-width: 1120px;
  margin: auto;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

/* MARCA */

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #16345b;
  text-decoration: none;
  flex-shrink: 0;
}

.brand-icon {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 13px;
  background: #16345b;
  color: white;
  font-size: 25px;
  font-weight: 700;
}

.brand strong {
  display: block;
  font-size: 20px;
}

.brand small {
  display: block;
  margin-top: 3px;
  color: #66758a;
  font-size: 12px;
}

/* NAVEGAÇÃO */

.navigation {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.nav-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 11px 15px;
  border-radius: 9px;
  color: #66758a;
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  transition: background 0.2s, color 0.2s;
}

.nav-link:hover {
  background: #f1f5fb;
  color: #244f85;
}

.nav-link-active {
  background: #eaf1fb;
  color: #244f85;
}

/* IDENTIFICAÇÃO */

.profile {
  border-radius: 30px;
  background: #edf3fc;
  padding: 9px 14px;
  color: #274e80;
  font-size: 13px;
  white-space: nowrap;
}

/* CONTEÚDO */

.main {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  padding: 48px 24px;
  flex: 1;
}

/* RODAPÉ */

.footer {
  padding: 24px;
  text-align: center;
  color: #67768a;
  font-size: 13px;
  line-height: 1.6;
}

/* RESPONSIVIDADE */

@media (max-width: 950px) {
  .header-content {
    flex-wrap: wrap;
  }

  .navigation {
    order: 3;
    width: 100%;
    justify-content: center;
    border-top: 1px solid #edf0f5;
    padding-top: 14px;
  }
}

@media (max-width: 600px) {
  .header-content {
    padding: 18px;
    gap: 16px;
  }

  .brand strong {
    font-size: 18px;
  }

  .brand small {
    font-size: 10px;
  }

  .profile {
    font-size: 11px;
    padding: 8px 10px;
  }

  .navigation {
    gap: 4px;
  }

  .nav-link {
    flex: 1;
    padding: 11px 8px;
    font-size: 12px;
    text-align: center;
  }

  .main {
    padding: 30px 18px;
  }
}
</style>
