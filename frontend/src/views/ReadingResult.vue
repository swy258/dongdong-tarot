<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import { readingsAPI } from '../api'

const route = useRoute()
const readingId = route.params.id

const reading = ref(null)
const loading = ref(true)
const interpreting = ref(false)
const interpretation = ref('')
const streamError = ref('')

onMounted(async () => {
  try {
    const { data } = await readingsAPI.getOne(readingId)
    reading.value = data

    // 如果没有解读，自动开始流式解读
    if (!data.interpretation) {
      await startInterpretation()
    } else {
      interpretation.value = data.interpretation
    }
  } catch (err) {
    console.error('Failed to load reading:', err)
    streamError.value = '加载占卜记录失败'
  } finally {
    loading.value = false
  }
})

const startInterpretation = async () => {
  interpreting.value = true
  streamError.value = ''
  interpretation.value = ''

  try {
    await new Promise((resolve, reject) => {
      // readingsAPI.interpret 返回 fetch 的 response
      readingsAPI.interpret(readingId).then(async (response) => {
        if (!response.ok) {
          reject(new Error(`HTTP ${response.status}`))
          return
        }
        const reader = response.body.getReader()
        const decoder = new TextDecoder('utf-8')

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const chunk = decoder.decode(value, { stream: true })
          interpretation.value += chunk
          await nextTick()
        }
        resolve()
      }).catch(reject)
    })

    // 刷新一下数据
    const { data } = await readingsAPI.getOne(readingId)
    reading.value = data
  } catch (err) {
    console.error('Interpretation error:', err)
    if (!interpretation.value) {
      streamError.value = '解读请求失败，请检查 DeepSeek API Key 是否配置正确'
    }
  } finally {
    interpreting.value = false
  }
}

const renderMarkdown = (text) => {
  if (!text) return ''
  return marked(text, { breaks: true })
}

const copyShareLink = () => {
  const link = `${window.location.origin}/share/${reading.value.share_code}`
  navigator.clipboard.writeText(link).then(() => {
    alert('分享链接已复制到剪贴板！')
  })
}

const openSharePage = () => {
  window.open(`/share/${reading.value.share_code}`, '_blank')
}
</script>

<template>
  <div class="reading-result-page fade-in">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <p>加载中...</p>
    </div>

    <template v-else-if="reading">
      <!-- 页面标题 -->
      <div class="page-header">
        <h1>🔮 占卜解读</h1>
        <p>{{ reading.spread?.name || '占卜' }} · {{ reading.created_at?.slice(0, 10) || '' }}</p>
      </div>

      <!-- 问题和牌阵概览 -->
      <div class="card summary-card">
        <div class="question-display">
          <span class="label">💭 你的问题</span>
          <p>{{ reading.question }}</p>
        </div>

        <div class="cards-display">
          <span class="label">🎴 抽牌结果</span>
          <div class="drawn-cards-row">
            <div
              v-for="card in reading.cards_drawn"
              :key="card.position"
              class="drawn-card-item"
            >
              <div class="drawn-card-visual" :class="{ reversed: card.is_reversed }">
                <span class="card-emoji">🃏</span>
                <span class="card-direction">{{ card.is_reversed ? '逆位' : '正位' }}</span>
              </div>
              <div class="drawn-card-name">{{ card.card_name }}</div>
              <div class="drawn-card-pos">{{ card.position_name }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 流式解读中 -->
      <div v-if="interpreting" class="card interpretation-card">
        <div class="interpreting-indicator">
          <span class="dot-pulse"></span>
          <span>AI 正在为你深入解读...</span>
        </div>
        <div
          v-if="interpretation"
          class="markdown-content"
          v-html="renderMarkdown(interpretation)"
        ></div>
      </div>

      <!-- 错误 -->
      <div v-if="streamError && !interpreting" class="card error-card">
        <p>⚠️ {{ streamError }}</p>
        <button class="btn btn-primary btn-sm" @click="startInterpretation">重试</button>
      </div>

      <!-- 完成解读 -->
      <div v-if="!interpreting && interpretation" class="card interpretation-card">
        <div class="markdown-content" v-html="renderMarkdown(interpretation)"></div>
      </div>

      <!-- 操作按钮 -->
      <div v-if="!interpreting && interpretation" class="action-buttons">
        <button class="btn btn-accent" @click="openSharePage">
          📤 生成分享卡片
        </button>
        <button class="btn btn-secondary" @click="copyShareLink">
          🔗 复制分享链接
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.summary-card, .interpretation-card {
  padding: 32px;
  margin-bottom: 24px;
}
.label {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  display: block;
  margin-bottom: 8px;
}
.question-display {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border);
}
.question-display p {
  font-size: 1.1rem;
  line-height: 1.7;
}
.drawn-cards-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.drawn-card-item {
  text-align: center;
  min-width: 80px;
}
.drawn-card-visual {
  width: 72px;
  height: 96px;
  border: 2px solid var(--border);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  background: var(--bg-card);
  margin: 0 auto 8px;
}
.drawn-card-visual.reversed {
  transform: rotate(180deg);
  border-color: var(--warning);
}
.card-emoji { font-size: 28px; }
.card-direction { font-size: 10px; color: var(--text-muted); }
.drawn-card-name {
  font-weight: 600;
  font-size: 13px;
}
.drawn-card-pos {
  font-size: 11px;
  color: var(--text-muted);
}

/* 解读中 */
.interpreting-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 0;
  color: var(--primary-light);
  font-size: 14px;
  margin-bottom: 20px;
}
.dot-pulse {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--primary);
  animation: pulse 1s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 0.4; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

.error-card {
  padding: 24px;
  text-align: center;
  color: var(--error);
}

.action-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding: 8px 0 32px;
}

.loading-state {
  text-align: center;
  padding: 80px 0;
  color: var(--text-secondary);
}
</style>
