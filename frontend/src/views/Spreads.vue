<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { spreadsAPI } from '../api'

const router = useRouter()
const spreads = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await spreadsAPI.getAll()
    spreads.value = data.spreads
  } catch (err) {
    console.error('Failed to load spreads:', err)
  } finally {
    loading.value = false
  }
})

const selectSpread = (spread) => {
  router.push({
    path: '/reading/new',
    query: { spread_id: spread.id }
  })
}
</script>

<template>
  <div class="spreads-page fade-in">
    <div class="page-header">
      <h1>选择牌阵</h1>
      <p>从经典牌阵中选择，或创建你自己的专属牌阵</p>
    </div>

    <div class="action-bar">
      <button class="btn btn-accent" @click="router.push('/spreads/custom')">
        ✨ 自定义牌阵
      </button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="spreads-grid">
      <div
        v-for="spread in spreads"
        :key="spread.id"
        class="card card-glow spread-card"
        @click="selectSpread(spread)"
      >
        <div class="spread-header">
          <h3>{{ spread.name }}</h3>
          <span class="tag">{{ spread.position_count }} 张牌</span>
          <span v-if="spread.is_preset" class="tag preset-tag">经典</span>
        </div>
        <p class="spread-desc">{{ spread.description || '自定义牌阵' }}</p>
        <div class="spread-positions">
          <span
            v-for="pos in spread.positions"
            :key="pos.index"
            class="position-chip"
          >
            {{ pos.name }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.action-bar {
  text-align: center;
  margin-bottom: 32px;
}
.spreads-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}
.spread-card {
  cursor: pointer;
  padding: 28px;
  transition: all 0.3s ease;
}
.spread-card:hover {
  transform: translateY(-2px);
}
.spread-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.spread-header h3 {
  margin-right: auto;
}
.preset-tag {
  background: rgba(245,158,11,0.15);
  color: var(--accent);
}
.spread-desc {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 16px;
  line-height: 1.6;
}
.spread-positions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.position-chip {
  padding: 4px 12px;
  background: rgba(192,132,252,0.08);
  border: 1px solid var(--border);
  border-radius: 20px;
  font-size: 12px;
  color: var(--text-secondary);
}
.loading {
  text-align: center;
  color: var(--text-secondary);
  padding: 60px 0;
}
</style>
