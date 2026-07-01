import { createRouter, createWebHistory } from 'vue-router'
import DashboardPage from '@/views/dashboard/DashboardPage.vue'
import PortfolioListPage from '@/views/portfolio/PortfolioListPage.vue'
import PortfolioDetailPage from '@/views/portfolio/PortfolioDetailPage.vue'
import BrokerListPage from '@/views/broker/BrokerListPage.vue'
import LoginPage from '@/views/auth/LoginPage.vue'
import SettingsPage from '@/views/auth/SettingsPage.vue'
import OrgAdminPage from '@/views/org/OrgAdminPage.vue'
import AiArenaPage from '@/views/arena/AiArenaPage.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginPage,
    meta: { guest: true },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: DashboardPage,
    meta: { requiresAuth: true },
  },
  {
    path: '/portfolios',
    name: 'Portfolios',
    component: PortfolioListPage,
    meta: { requiresAuth: true },
  },
  {
    path: '/portfolios/:id',
    name: 'PortfolioDetail',
    component: PortfolioDetailPage,
    meta: { requiresAuth: true },
    props: true,
  },
  {
    path: '/brokers',
    name: 'Brokers',
    component: BrokerListPage,
    meta: { requiresAuth: true },
  },
  {
    path: '/arena',
    name: 'AiArena',
    component: AiArenaPage,
    meta: { requiresAuth: true },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: SettingsPage,
    meta: { requiresAuth: true },
  },
  {
    path: '/org',
    name: 'OrgAdmin',
    component: OrgAdminPage,
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.meta.guest && token) {
    next('/')
  } else {
    next()
  }
})

export default router
