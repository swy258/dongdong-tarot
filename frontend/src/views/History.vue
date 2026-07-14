<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { readingsAPI } from '../api'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const readings = ref([])
const total = ref(0)
const loading = ref(true)
const page = ref(0)

onMounted(async () => {
  if (!auth.isLoggedIn) {
    router.push('/login')
    return
  }
  await loadHistory()
})

const loadHistory = async () => {
  loading.value = true
  try {
    const { data } = await readingsAPI.getHistory({ skip: page.value * 20, limit: 20 })
    readings.value = data.readings
    total.value = data.total
  } catch (err) {
    console.error('Failed to load history:', err)
  } finally {
    loading.value = false
  }
}

const viewReading = (id) => {
  router.push(`/reading/${id}`)
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="history-page fade-in">
    <div class="page-header">
      <h1>📜 占卜历史</h1>
      <p>共 {{ total }} 条记录</p>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="readings.length === 0" class="empty-state card">
      <p>还没有占卜记录</p>
      <button class="btn btn-accent" @click="router.push('/reading/new')">开始第一次占卜</button>
    </div>

    <div v-else class="history-list">
      <div
        v-for="reading in readings"
        :key="reading.id"
        class="card history-card"
        @click="viewReading(reading.id)"
      >
        <div class="history-card-header">
          <h3 class="history-question">{{ reading.question }}</h3>
          <span class="tag" v-if="reading.has_interpretation">已解读</span>
          <span class="tag pending-tag" v-else>待解读</span>
        </div>

        <div class="history-cards">
          <span
            v-for="card in reading.cards_drawn"
            :key="card.position"
            class="history-card-chip"
          >
            {{ card.card_name }}{{ card.is_reversed ? '(逆)' : '' }}
          </span>
        </div>

        <div class="history-footer">
          <span class="history-date">{{ formatDate(reading.created_at) }}</span>
          <span class="history-share" v-if="reading.share_code">🔗 可分享</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.history-card {
  cursor: pointer;
  padding: 24px;
  transition: all 0.3s;
}
.history-card:hover {
  transform: translateY(-2px);
  border-color: var(--primary);
}
.history-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}
.history-question {
  flex: 1;
  font-size: 1.1rem;
}
.pending-tag {
  background: rgba(251,191,36,0.15);
  color: var(--warning);
}
.history-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}
.history-card-chip {
  padding: 3px 10px;
  background: rgba(192,132,252,0.08);
  border: 1px solid var(--border);
  border-radius: 12px;
  font-size: 12px;
}
.history-footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-muted);
}
.loading, .empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--text-secondary);
}
.empty-state button { margin-top: 20px; }
</style>
