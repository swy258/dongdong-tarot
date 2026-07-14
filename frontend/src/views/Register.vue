<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const email = ref('')
const nickname = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

const handleRegister = async () => {
  error.value = ''
  if (password.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致'
    return
  }
  loading.value = true
  try {
    await auth.register(email.value, password.value, nickname.value || '塔罗爱好者')
    router.push('/login')
  } catch (err) {
    error.value = err.response?.data?.detail || '注册失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page fade-in">
    <div class="auth-card card">
      <div class="auth-header">
        <h2>✨ 注册东东塔罗</h2>
        <p>开启你的塔罗探索之旅</p>
      </div>

      <form @submit.prevent="handleRegister" class="auth-form">
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="email" type="email" class="input" placeholder="请输入邮箱" required />
        </div>
        <div class="form-group">
          <label>昵称（选填）</label>
          <input v-model="nickname" type="text" class="input" placeholder="你的昵称" />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" class="input" placeholder="至少6位密码" required minlength="6" />
        </div>
        <div class="form-group">
          <label>确认密码</label>
          <input v-model="confirmPassword" type="password" class="input" placeholder="再次输入密码" required />
        </div>

        <div v-if="error" class="error-msg">{{ error }}</div>

        <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>

      <p class="auth-footer">
        已有账号？<router-link to="/login">立即登录</router-link>
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
