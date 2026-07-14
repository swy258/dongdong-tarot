import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
  },
  {
    path: '/spreads',
    name: 'Spreads',
    component: () => import('../views/Spreads.vue'),
  },
  {
    path: '/spreads/custom',
    name: 'CustomSpread',
    component: () => import('../views/CustomSpread.vue'),
  },
  {
    path: '/reading/new',
    name: 'NewReading',
    component: () => import('../views/NewReading.vue'),
  },
  {
    path: '/reading/:id',
    name: 'ReadingResult',
    component: () => import('../views/ReadingResult.vue'),
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/History.vue'),
  },
  {
    path: '/share/:shareCode',
    name: 'ShareView',
    component: () => import('../views/ShareView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
