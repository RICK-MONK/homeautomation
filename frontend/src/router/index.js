// Composables
import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Control from '@/views/Control.vue'
import Dashboard from '@/views/Dashboard.vue'
import Analysis from '@/views/Analysis.vue'

const routes = [
  { path: '/', name: 'Home', component: Home, meta:{ transition: 'fade'} },
  { path: '/control', name: 'Control', component: Control, meta:{ transition: 'fade'} },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard, meta:{ transition: 'fade'} },
  { path: '/analysis', name: 'Analysis', component: Analysis, meta:{ transition: 'fade'} },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
})

export default router
