<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const handleLogin = async () => {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.detail || '登录失败，请检查邮箱和密码'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page fade-in">
    <div class="auth-card card">
      <div class="auth-header">
        <h2>🔮 登录东东塔罗</h2>
        <p>继续你的塔罗探索之旅</p>
      </div>

      <form @submit.prevent="handleLogin" class="auth-form">
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="email" type="email" class="input" placeholder="请输入邮箱" required />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" class="input" placeholder="请输入密码" required />
        </div>

        <div v-if="error" class="error-msg">{{ error }}</div>

        <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>

      <p class="auth-footer">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  padding: 60px 20px;
}
.auth-card {
  width: 100%;
  max-width: 420px;
  padding: 40px;
}
.auth-header {
  text-align: center;
  margin-bottom: 32px;
}
.auth-header h2 { margin-bottom: 8px; }
.auth-header p { color: var(--text-secondary); font-size: 14px; }
.auth-form { display: flex; flex-direction: column; gap: 20px; }
.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}
.error-msg {
  background: rgba(248,113,113,0.1);
  border: 1px solid rgba(248,113,113,0.3);
  color: var(--error);
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
}
.auth-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: var(--text-secondary);
}
.auth-footer a { color: var(--primary-light); text-decoration: none; }
</style>
