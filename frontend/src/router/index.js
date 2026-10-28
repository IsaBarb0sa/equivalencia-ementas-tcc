
import { createRouter, createWebHistory } from 'vue-router'
import { obterUsuarioAtual } from '../services/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),

  routes: [
    {
      path: '/',
      redirect: '/login',
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/candidato',
      name: 'menu-candidato',
      component: () => import('../views/MenuCandidatoView.vue'),
      meta: { perfil: 'CANDIDATO' },
    },
    {
      path: '/candidato/nova-solicitacao',
      name: 'nova-solicitacao',
      component: () => import('../views/NovaSolicitacaoView.vue'),
      meta: { perfil: 'CANDIDATO' },
    },
    {
      path: '/candidato/minhas-solicitacoes',
      name: 'minhas-solicitacoes',
      component: () => import('../views/SolicitacoesView.vue'),
      meta: { perfil: 'CANDIDATO' },
    },
    {
      path: '/solicitacoes',
      redirect: '/candidato/minhas-solicitacoes',
    },
    {
      path: '/cadastro',
      name: 'cadastro',
      component: () => import('../views/CadastroView.vue'),
    },
    {
      path: '/coordenacao',
      name: 'menu-coordenador',
      component: () => import('../views/MenuCoordenadorView.vue'),
      meta: { perfil: 'COORDENADOR' },
    },
    {
      path: '/coordenacao/solicitacoes',
      name: 'solicitacoes-coordenacao',
      component: () =>
        import('../views/SolicitacoesCoordenadorView.vue'),
      meta: { perfil: 'COORDENADOR' },
    },
    {
      path: '/coordenacao/solicitacoes/:protocolo',
      name: 'detalhe-solicitacao-coordenacao',
      component: () =>
        import('../views/DetalheSolicitacaoCoordenadorView.vue'),
      meta: { perfil: 'COORDENADOR' },
    },
    {
      path: '/coordenacao/ementas',
      name: 'ementas-institucionais',
      component: () =>
        import('../views/EmentasInstitucionaisView.vue'),
      meta: { perfil: 'COORDENADOR' },
    },
    
{
  path: '/coordenacao/ementas/:matrizDisciplinaId/:ementaId',
  name: 'detalhe-ementa-institucional',
  component: () =>
    import('../views/DetalheEmentaInstitucionalView.vue'),
  meta: { perfil: 'COORDENADOR' },
},

  ],
})

router.beforeEach(async (to) => {
  let usuario = null

  try {
    usuario = await obterUsuarioAtual()
  } catch {
    usuario = null
  }

  const destinoPorPerfil = {
    CANDIDATO: '/candidato',
    COORDENADOR: '/coordenacao',
  }

  if (to.path === '/login' || to.path === '/cadastro') {
    if (usuario?.perfil in destinoPorPerfil) {
      return destinoPorPerfil[usuario.perfil]
    }

    return true
  }

  if (!usuario) {
    return '/login'
  }

  if (to.meta.perfil && usuario.perfil !== to.meta.perfil) {
    return destinoPorPerfil[usuario.perfil] || '/login'
  }

  return true
})


export default router
