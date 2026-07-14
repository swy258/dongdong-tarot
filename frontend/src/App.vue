<script setup>
import AppHeader from './components/AppHeader.vue'
</script>

<template>
  <div class="app-wrapper">
    <AppHeader />
    <main class="main-content">
      <router-view />
    </main>
    <footer class="app-footer">
      <p>🃏 东东塔罗 — 以心理学视角探索塔罗智慧</p>
      <p class="footer-sub">Powered by DeepSeek AI · 经典塔罗文献知识库</p>
    </footer>
  </div>
</template>

<style scoped>
.app-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.main-content {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 24px 20px;
  box-sizing: border-box;
}
.app-footer {
  text-align: center;
  padding: 32px 20px;
  border-top: 1px solid var(--border);
  margin-top: 48px;
}
.app-footer p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}
.footer-sub {
  margin-top: 4px !important;
  font-size: 12px !important;
  opacity: 0.6;
}
</style>
