<script setup>
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

const handleLogout = () => {
  auth.logout()
  router.push('/')
}
</script>

<template>
  <header class="app-header">
    <div class="header-inner">
      <router-link to="/" class="logo">
        <span class="logo-icon">🃏</span>
        <span class="logo-text">东东塔罗</span>
      </router-link>

      <nav class="nav-links">
        <router-link to="/spreads">牌阵</router-link>
        <router-link to="/reading/new">开始占卜</router-link>
        <router-link to="/history" v-if="auth.isLoggedIn">历史记录</router-link>

        <template v-if="auth.isLoggedIn">
          <span class="nav-user">{{ auth.user?.nickname || '塔罗爱好者' }}</span>
          <button class="btn btn-sm btn-secondary" @click="handleLogout">退出</button>
        </template>
        <template v-else>
          <router-link to="/login" class="btn btn-sm btn-secondary">登录</router-link>
          <router-link to="/register" class="btn btn-sm btn-primary">注册</router-link>
        </template>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg-header);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
}
.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 64px;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--text-primary);
}
.logo-icon {
  font-size: 28px;
}
.logo-text {
  font-family: var(--font-heading);
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary-light), var(--accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.nav-links {
  display: flex;
  align-items: center;
  gap: 16px;
}
.nav-links > a {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 15px;
  transition: color 0.2s;
  padding: 4px 0;
}
.nav-links > a:hover {
  color: var(--primary-light);
}
.nav-links > a.router-link-active:not(.btn) {
  color: var(--primary-light);
}
.nav-user {
  color: var(--text-primary);
  font-size: 14px;
}
@media (max-width: 768px) {
  .nav-links > a:not(.btn) {
    display: none;
  }
}
</style>
