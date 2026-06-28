import { createRouter, createWebHistory } from 'vue-router'
import DashboardPage from '@/views/dashboard/DashboardPage.vue'
import PortfolioListPage from '@/views/portfolio/PortfolioListPage.vue'
import PortfolioDetailPage from '@/views/portfolio/PortfolioDetailPage.vue'
import BrokerListPage from '@/views/broker/BrokerListPage.vue'
import LoginPage from '@/views/auth/LoginPage.vue'

const routes = [
  { path: '/login', name: 'Login', component: LoginPage, meta: { guest: true } },
  { path: '/', name: 'Dashboard', component: DashboardPage, meta: { requiresAuth: true } },
  { path: '/portfolios', name: 'Portfolios', component: PortfolioListPage, meta: { requiresAuth: true } },
  { path: '/portfolios/:id', name: 'PortfolioDetail', component: PortfolioDetailPage, meta: { requiresAuth: true }, props: true },
  { path: '/brokers', name: 'Brokers', component: BrokerListPage, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
