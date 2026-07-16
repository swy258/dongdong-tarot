<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import html2canvas from 'html2canvas'
import { readingsAPI } from '../api'

const route = useRoute()
const shareCode = route.params.shareCode

const reading = ref(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const res = await readingsAPI.getShared(shareCode)
    reading.value = res.data
  } catch (err) {
    error.value = '分享链接无效或已过期'
  } finally {
    loading.value = false
  }
})

const renderMarkdown = (text) => {
  if (!text) return ''
  return marked(text, { breaks: true })
}

const getShareSummary = (text) => {
  if (!text) return ''
  const sections = {}
  const headingRegex = /^###\s+(.+?)$/gm
  const headings = []
  let match
  while ((match = headingRegex.exec(text)) !== null) {
    headings.push({ title: match[1].trim(), pos: match.index })
  }
  for (let i = 0; i < headings.length; i++) {
    const start = headings[i].pos
    const end = i + 1 < headings.length ? headings[i + 1].pos : text.length
    sections[headings[i].title] = text.slice(start, end).replace(/^###\s+.+?\n+/gm, '').trim()
  }
  const result = []
  for (const key of Object.keys(sections)) {
    if (key.includes('概述')) { result.push(`### ${key}\n\n${sections[key]}`); break }
  }
  for (const key of Object.keys(sections)) {
    if (key.includes('建议')) { result.push(`### ${key}\n\n${sections[key]}`); break }
  }
  if (result.length === 0) return text.slice(0, 400) + '...'
  return result.join('\n\n')
}

const shareCardRef = ref(null)
const generating = ref(false)
const generatedImage = ref('')

const generateShareImage = async () => {
  if (!shareCardRef.value) return
  generating.value = true
  try {
    await nextTick()
    shareCardRef.value.scrollIntoView({ behavior: 'instant', block: 'start' })
    const isMobile = window.innerWidth < 640
    const canvas = await html2canvas(shareCardRef.value, {
      backgroundColor: '#0f0f1a',
      scale: isMobile ? 1.5 : 2,
      useCORS: true,
      allowTaint: true,
      logging: false,
    })
    generatedImage.value = canvas.toDataURL('image/png')
  } catch (err) {
    alert('图片生成失败：' + err.message)
    console.error('html2canvas error:', err)
  } finally {
    generating.value = false
  }
}

const downloadImage = () => {
  if (!generatedImage.value) return
  const link = document.createElement('a')
  link.download = `东东塔罗_${shareCode}.png`
  link.href = generatedImage.value
  link.click()
}

const formatDate = (d) => {
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

const getCardByPos = (pos) => {
  if (!reading.value) return null
  return reading.value.cards_drawn.find(c => c.position === pos)
}

// 将摘要文本拆成卡片
const parseSummaryCards = (text) => {
  if (!text) return []
  // 按空行拆分
  const blocks = text.split(/\n\n+/).filter(b => b.trim())
  if (blocks.length <= 1) return [{ text }]

  const cards = []
  for (const block of blocks) {
    const trimmed = block.trim()
    // 判断是否是标题行（以 ** 开头）
    const headingMatch = trimmed.match(/^\*\*(.+?)\*\*(.*)$/)
    if (headingMatch) {
      cards.push({ title: headingMatch[1], text: headingMatch[2].trim() || trimmed })
    } else {
      cards.push({ title: '', text: trimmed })
    }
  }
  return cards
}
</script>

<template>
  <div class="share-page fade-in">
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error-state card"><p>{{ error }}</p></div>

    <template v-else-if="reading">
      <!-- ====== 分享卡片（截图区域） ====== -->
      <div ref="shareCardRef" class="share-card">
        <!-- 顶部装饰条 -->
        <div class="share-top-bar"></div>

        <!-- 水印 -->
        <div class="share-card-watermark">东东塔罗</div>

        <!-- 头部 -->
        <div class="share-card-header">
          <div class="share-logo">🃏</div>
          <h1>东东塔罗</h1>
          <p class="share-subtitle">{{ reading.spread?.name || '塔罗占卜' }} · {{ formatDate(reading.created_at) }}</p>
        </div>

        <!-- 分割线 -->
        <div class="share-divider"></div>

        <!-- 问题 -->
        <div class="share-section">
          <div class="section-icon">❓</div>
          <div class="section-body">
            <p class="share-question-text">"{{ reading.question }}"</p>
          </div>
        </div>

        <!-- 抽牌结果 - 按牌阵排布 -->
        <div class="share-cards-section">
          <div class="summary-label">✦ 抽牌结果</div>

          <!-- 单牌阵 -->
          <div v-if="reading.spread?.layout_type === 'single'" class="layout-single">
            <div class="single-card" :class="{ reversed: reading.cards_drawn[0].is_reversed }">
              <span class="sg-name">{{ reading.cards_drawn[0].card_name }}</span>
              <span class="sg-dir">{{ reading.cards_drawn[0].is_reversed ? '逆位' : '正位' }}</span>
            </div>
          </div>

          <!-- 三牌阵（时间线）：水平箭头 -->
          <div v-else-if="reading.spread?.layout_type === 'timeline'" class="layout-timeline">
            <div v-for="(card, idx) in reading.cards_drawn" :key="card.position" class="tl-card" :class="{ reversed: card.is_reversed }">
              <span class="tl-pos">{{ card.position_name }}</span>
              <span class="tl-name">{{ card.card_name }}</span>
              <span class="tl-dir">{{ card.is_reversed ? '逆位' : '正位' }}</span>
            </div>
          </div>

          <!-- 三牌阵（身心灵）：垂直堆叠 -->
          <div v-else-if="reading.spread?.layout_type === 'stack'" class="layout-stack">
            <div v-for="card in reading.cards_drawn" :key="card.position" class="stack-card" :class="{ reversed: card.is_reversed }">
              <span class="sk-pos">{{ card.position_name }}</span>
              <span class="sk-name">{{ card.card_name }}</span>
              <span class="sk-dir">{{ card.is_reversed ? '逆位' : '正位' }}</span>
            </div>
          </div>

          <!-- 二选一阵 -->
          <div v-else-if="reading.spread?.layout_type === 'branch'" class="layout-branch">
            <div class="branch-top">
              <div class="br-card center" :class="{ reversed: reading.cards_drawn[0].is_reversed }">
                <span class="br-pos">{{ reading.cards_drawn[0].position_name }}</span>
                <span class="br-name">{{ reading.cards_drawn[0].card_name }}</span>
              </div>
            </div>
            <div class="branch-split">
              <div class="branch-arm left">
                <div class="br-card" :class="{ reversed: reading.cards_drawn[1].is_reversed }">
                  <span class="br-pos">{{ reading.cards_drawn[1].position_name }}</span>
                  <span class="br-name">{{ reading.cards_drawn[1].card_name }}</span>
                </div>
                <div class="br-card" :class="{ reversed: reading.cards_drawn[3].is_reversed }">
                  <span class="br-pos">{{ reading.cards_drawn[3].position_name }}</span>
                  <span class="br-name">{{ reading.cards_drawn[3].card_name }}</span>
                </div>
              </div>
              <div class="branch-arm right">
                <div class="br-card" :class="{ reversed: reading.cards_drawn[2].is_reversed }">
                  <span class="br-pos">{{ reading.cards_drawn[2].position_name }}</span>
                  <span class="br-name">{{ reading.cards_drawn[2].card_name }}</span>
                </div>
                <div class="br-card" :class="{ reversed: reading.cards_drawn[4].is_reversed }">
                  <span class="br-pos">{{ reading.cards_drawn[4].position_name }}</span>
                  <span class="br-name">{{ reading.cards_drawn[4].card_name }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 六芒星阵 -->
          <div v-else-if="reading.spread?.layout_type === 'hexagram'" class="layout-hexagram">
            <div class="hex-center">{{ getCardByPos(2)?.card_name || '' }}<span class="hx-pos">现在</span></div>
            <div class="hex-ring">
              <div class="hex-cell">{{ getCardByPos(1)?.card_name || '' }}<span class="hx-pos">过去</span></div>
              <div class="hex-cell">{{ getCardByPos(3)?.card_name || '' }}<span class="hx-pos">未来</span></div>
              <div class="hex-cell">{{ getCardByPos(4)?.card_name || '' }}<span class="hx-pos">对策</span></div>
              <div class="hex-cell">{{ getCardByPos(5)?.card_name || '' }}<span class="hx-pos">环境</span></div>
              <div class="hex-cell">{{ getCardByPos(6)?.card_name || '' }}<span class="hx-pos">希望</span></div>
              <div class="hex-cell">{{ getCardByPos(7)?.card_name || '' }}<span class="hx-pos">结果</span></div>
            </div>
          </div>

          <!-- 关系牌阵 -->
          <div v-else-if="reading.spread?.layout_type === 'relationship'" class="layout-relationship">
            <div class="rel-row">
              <div class="rel-card" :class="{ reversed: getCardByPos(1)?.is_reversed }">
                <span class="rl-pos">你</span>
                <span class="rl-name">{{ getCardByPos(1)?.card_name || '' }}</span>
              </div>
              <div class="rel-connector">💫</div>
              <div class="rel-card" :class="{ reversed: getCardByPos(2)?.is_reversed }">
                <span class="rl-pos">对方</span>
                <span class="rl-name">{{ getCardByPos(2)?.card_name || '' }}</span>
              </div>
            </div>
            <div class="rel-details">
              <div v-for="pos in [3,4,5,6]" :key="pos" class="rel-chip" :class="{ reversed: getCardByPos(pos)?.is_reversed }">
                <span class="rc-pos">{{ getCardByPos(pos)?.position_name || '' }}</span>
                <span class="rc-name">{{ getCardByPos(pos)?.card_name || '' }}</span>
              </div>
            </div>
          </div>

          <!-- 凯尔特十字阵 -->
          <div v-else-if="reading.spread?.layout_type === 'celtic-cross'" class="celtic-cross-layout">
            <div class="cross-area">
              <div class="cross-top">{{ getCardByPos(5)?.card_name || '' }}<span class="cr-pos">目标</span></div>
              <div class="cross-row">
                <div class="cross-cell">{{ getCardByPos(4)?.card_name || '' }}<span class="cr-pos">过去</span></div>
                <div class="cross-cell cross-center">{{ getCardByPos(1)?.card_name || '' }}<span class="cr-pos">现状</span></div>
                <div class="cross-cell">{{ getCardByPos(6)?.card_name || '' }}<span class="cr-pos">近未来</span></div>
              </div>
              <div class="cross-bottom">{{ getCardByPos(3)?.card_name || '' }}<span class="cr-pos">根源</span></div>
              <div class="cross-x">{{ getCardByPos(2)?.card_name || '' }}<span class="cr-pos">阻碍</span></div>
            </div>
            <div class="staff-area">
              <div v-for="pos in [7,8,9,10]" :key="pos" class="staff-cell" :class="{ reversed: getCardByPos(pos)?.is_reversed }">
                <span class="st-pos">{{ getCardByPos(pos)?.position_name || '' }}</span>
                <span class="st-name">{{ getCardByPos(pos)?.card_name || '' }}</span>
                <span class="st-dir" :class="{ rev: getCardByPos(pos)?.is_reversed }">{{ getCardByPos(pos)?.is_reversed ? '逆' : '正' }}</span>
              </div>
            </div>
          </div>

          <!-- 自定义排布：按用户拖拽的坐标定位 -->
          <div v-else-if="reading.spread?.layout_type === 'custom'" class="layout-free">
            <div v-for="card in reading.cards_drawn" :key="card.position" class="free-card"
              :class="{ reversed: card.is_reversed }"
              :style="{
                left: (reading.spread?.layout_data?.[card.position]?.x || 5) + '%',
                top: (reading.spread?.layout_data?.[card.position]?.y || 5) + '%',
              }">
              <span class="fcp-pos">{{ card.position_name }}</span>
              <span class="fcp-name">{{ card.card_name }}</span>
              <span class="fcp-dir">{{ card.is_reversed ? '逆位' : '正位' }}</span>
            </div>
          </div>

          <!-- 其他：默认网格 -->
          <div v-else class="share-cards-grid" :style="{ gridTemplateColumns: `repeat(${Math.min(reading.cards_drawn.length, 4)}, 1fr)` }">
            <div v-for="card in reading.cards_drawn" :key="card.position" class="drawn-card" :class="{ reversed: card.is_reversed }">
              <div class="dc-inner">
                <span class="dc-pos">{{ card.position_name }}</span>
                <span class="dc-name">{{ card.card_name }}</span>
                <span class="dc-dir">{{ card.is_reversed ? '逆位' : '正位' }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 解读卡片组 -->
        <div class="share-section-col" v-if="reading.share_summary || reading.interpretation">
          <div class="summary-label">✦ 解读</div>
          <div class="summary-cards">
            <template v-if="reading.share_summary">
              <div v-for="(card, idx) in parseSummaryCards(reading.share_summary)" :key="idx" class="summary-card">
                <div v-if="card.title" class="sc-title">{{ card.title }}</div>
                <div class="sc-text" v-html="renderMarkdown(card.text)"></div>
              </div>
            </template>
            <template v-else>
              <div v-for="(card, idx) in parseSummaryCards(getShareSummary(reading.interpretation))" :key="idx" class="summary-card">
                <div v-if="card.title" class="sc-title">{{ card.title }}</div>
                <div class="sc-text" v-html="renderMarkdown(card.text)"></div>
              </div>
            </template>
          </div>
        </div>

        <!-- 底部 -->
        <div class="share-divider"></div>
        <div class="share-footer">
          <p>Powered by DeepSeek AI · 经典塔罗文献知识库</p>
          <p class="share-brand">🃏 东东塔罗 DongDong Tarot</p>
        </div>

        <!-- 底部装饰条 -->
        <div class="share-bottom-bar"></div>
      </div>

      <!-- 操作按钮 -->
      <div class="share-actions">
        <button class="btn btn-accent" @click="generateShareImage" :disabled="generating">
          {{ generating ? '生成中...' : '生成图片' }}
        </button>
        <button v-if="generatedImage" class="btn btn-primary" @click="downloadImage">
          下载图片
        </button>
      </div>

      <!-- 预览 -->
      <div v-if="generatedImage" class="generated-preview">
        <h3>预览</h3>
        <img :src="generatedImage" alt="分享卡片" />
      </div>
    </template>
  </div>
</template>

<style scoped>
/* ====== 卡片整体 ====== */
.share-card {
  max-width: 600px;
  width: 100%;
  margin: 0 auto;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #1a1a2e 100%);
  border-radius: 16px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

/* 顶部装饰条 */
.share-top-bar {
  height: 4px;
  background: linear-gradient(90deg, #8b5cf6, #c084fc, #f59e0b, #c084fc, #8b5cf6);
}
.share-bottom-bar {
  height: 4px;
  background: linear-gradient(90deg, #f59e0b, #c084fc, #8b5cf6, #c084fc, #f59e0b);
}

/* 水印 */
.share-card-watermark {
  position: absolute;
  top: 55%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-25deg);
  font-size: 110px;
  font-weight: 900;
  color: rgba(192,132,252,0.04);
  pointer-events: none;
  white-space: nowrap;
  font-family: var(--font-heading);
  z-index: 0;
  user-select: none;
  letter-spacing: 20px;
}

/* ====== 头部 ====== */
.share-card-header {
  text-align: center;
  padding: 32px 40px 20px;
  position: relative;
  z-index: 1;
}
.share-logo {
  font-size: 48px;
  margin-bottom: 8px;
}
.share-card-header h1 {
  font-size: 28px;
  font-family: var(--font-heading);
  background: linear-gradient(135deg, var(--primary-light), var(--accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: #c084fc; /* fallback for html2canvas */
  margin-bottom: 6px;
}
.share-subtitle {
  font-size: 13px;
  color: var(--text-muted);
}

/* 分割线 */
.share-divider {
  width: 80%;
  height: 1px;
  margin: 0 auto;
  background: linear-gradient(90deg, transparent, rgba(192,132,252,0.3), transparent);
}

/* ====== 分区 ====== */
.share-section {
  display: flex;
  gap: 16px;
  padding: 20px 40px;
  position: relative;
  z-index: 1;
  align-items: flex-start;
}
.section-icon {
  font-size: 22px;
  flex-shrink: 0;
  margin-top: 1px;
}
.section-body {
  flex: 1;
}
.share-question-text {
  font-size: 16px;
  line-height: 1.7;
  color: var(--text-primary);
  font-style: italic;
  margin: 0;
}

/* ====== 牌面展示 ====== */
.share-cards-section {
  padding: 16px 40px 8px;
  position: relative;
  z-index: 1;
}

/* 普通网格 */
.share-cards-grid {
  display: grid;
  gap: 10px;
}
.drawn-card {
  aspect-ratio: 2.5/3;
  background: linear-gradient(180deg, rgba(192,132,252,0.08) 0%, rgba(192,132,252,0.02) 100%);
  border: 1.5px solid rgba(192,132,252,0.15);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 8px 4px;
}
.drawn-card.reversed {
  background: linear-gradient(180deg, rgba(251,191,36,0.06) 0%, rgba(251,191,36,0.01) 100%);
  border-color: rgba(251,191,36,0.25);
}
.dc-inner { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.dc-pos { font-size: 10px; color: var(--text-muted); letter-spacing: 1px; }
.dc-name { font-size: 13px; font-weight: 700; color: var(--text-primary); line-height: 1.3; }
.dc-dir { font-size: 10px; padding: 2px 8px; border-radius: 6px; background: rgba(52,211,153,0.15); color: var(--success); }
.drawn-card.reversed .dc-dir { background: rgba(251,191,36,0.15); color: var(--warning); }

/* ====== 凯尔特十字阵布局 ====== */
.celtic-cross-layout {
  display: flex;
  gap: 20px;
  align-items: center;
  justify-content: center;
}
.cross-area {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px;
}
.cross-top, .cross-bottom {
  text-align: center;
  padding: 10px 22px;
  background: rgba(192,132,252,0.07);
  border: 1px solid rgba(192,132,252,0.12);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  min-width: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.cross-row {
  display: flex;
  gap: 4px;
}
.cross-cell {
  text-align: center;
  padding: 10px 16px;
  background: rgba(192,132,252,0.07);
  border: 1px solid rgba(192,132,252,0.12);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  min-width: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.cross-center {
  background: rgba(192,132,252,0.12);
  border-color: rgba(192,132,252,0.25);
  box-shadow: 0 0 12px rgba(192,132,252,0.1);
}
.cross-x {
  position: absolute;
  top: calc(50% - 16px);
  left: calc(50% - 35px);
  transform: rotate(-25deg);
  background: rgba(251,191,36,0.1);
  border: 1px solid rgba(251,191,36,0.3);
  border-radius: 6px;
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 700;
  color: var(--warning);
  white-space: nowrap;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.cr-pos {
  font-size: 9px;
  color: var(--text-muted);
  font-weight: 400;
  margin-top: 2px;
}

/* 右侧柱状 */
.staff-area {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.staff-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 14px;
  background: rgba(192,132,252,0.05);
  border: 1px solid rgba(192,132,252,0.1);
  border-radius: 8px;
  text-align: center;
  min-width: 60px;
}
.st-pos { font-size: 9px; color: var(--text-muted); }
.st-name { font-size: 13px; font-weight: 700; color: var(--text-primary); margin: 2px 0; }
.st-dir { font-size: 9px; padding: 1px 6px; border-radius: 4px; background: rgba(52,211,153,0.15); color: var(--success); }
.st-dir.rev { background: rgba(251,191,36,0.15); color: var(--warning); }

/* ====== 单牌阵 ====== */
.layout-single { display: flex; justify-content: center; padding: 12px 0; }
.single-card {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 24px 40px;
  background: linear-gradient(180deg, rgba(192,132,252,0.1) 0%, rgba(192,132,252,0.03) 100%);
  border: 1.5px solid rgba(192,132,252,0.2); border-radius: 14px;
}
.single-card.reversed { border-color: rgba(251,191,36,0.3); background: linear-gradient(180deg, rgba(251,191,36,0.08) 0%, rgba(251,191,36,0.02) 100%); }
.sg-name { font-size: 18px; font-weight: 700; color: var(--text-primary); }
.sg-dir { font-size: 11px; padding: 2px 10px; border-radius: 8px; background: rgba(52,211,153,0.15); color: var(--success); }
.single-card.reversed .sg-dir { background: rgba(251,191,36,0.15); color: var(--warning); }

/* ====== 三牌阵（时间线） ====== */
.layout-timeline {
  display: flex; align-items: center; justify-content: center; gap: 0;
  padding: 12px 0;
  position: relative;
}
.tl-card {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 16px 20px;
  background: rgba(192,132,252,0.06); border: 1px solid rgba(192,132,252,0.12);
  border-radius: 10px; min-width: 70px;
  position: relative;
}
.tl-card:not(:last-child)::after {
  content: '→'; position: absolute; right: -18px; top: 50%;
  transform: translateY(-50%); color: var(--accent); font-size: 18px; font-weight: 700;
  z-index: 1;
}
.tl-card.reversed { border-color: rgba(251,191,36,0.25); }
.tl-pos { font-size: 10px; color: var(--text-muted); }
.tl-name { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.tl-dir { font-size: 9px; padding: 1px 6px; border-radius: 4px; background: rgba(52,211,153,0.15); color: var(--success); }
.tl-card.reversed .tl-dir { background: rgba(251,191,36,0.15); color: var(--warning); }

/* ====== 三牌阵（身心灵） ====== */
.layout-stack { display: flex; flex-direction: column; gap: 8px; padding: 12px 0; align-items: center; }
.stack-card {
  display: flex; align-items: center; gap: 14px;
  padding: 12px 24px; width: 100%; max-width: 300px;
  background: rgba(192,132,252,0.05); border: 1px solid rgba(192,132,252,0.1);
  border-radius: 10px;
}
.stack-card.reversed { border-color: rgba(251,191,36,0.25); }
.sk-pos { font-size: 12px; color: var(--text-muted); min-width: 60px; }
.sk-name { font-size: 14px; font-weight: 700; color: var(--text-primary); flex: 1; }
.sk-dir { font-size: 10px; padding: 2px 8px; border-radius: 6px; background: rgba(52,211,153,0.15); color: var(--success); }
.stack-card.reversed .sk-dir { background: rgba(251,191,36,0.15); color: var(--warning); }

/* ====== 二选一阵 ====== */
.layout-branch { padding: 12px 0; }
.branch-top { display: flex; justify-content: center; margin-bottom: 14px; }
.branch-split { display: flex; gap: 20px; justify-content: center; }
.branch-arm { display: flex; flex-direction: column; gap: 8px; align-items: center; }
.branch-arm.left { padding-right: 10px; border-right: 2px solid rgba(192,132,252,0.2); }
.branch-arm.right { padding-left: 10px; border-left: 2px solid rgba(192,132,252,0.2); }
.br-card {
  display: flex; flex-direction: column; align-items: center; gap: 3px;
  padding: 10px 18px;
  background: rgba(192,132,252,0.06); border: 1px solid rgba(192,132,252,0.12);
  border-radius: 8px; min-width: 80px;
}
.br-card.center { background: rgba(192,132,252,0.1); border-color: rgba(192,132,252,0.2); }
.br-card.reversed { border-color: rgba(251,191,36,0.25); }
.br-pos { font-size: 9px; color: var(--text-muted); }
.br-name { font-size: 13px; font-weight: 700; color: var(--text-primary); }

/* ====== 六芒星阵 ====== */
.layout-hexagram { padding: 12px 0; display: flex; flex-direction: column; align-items: center; gap: 12px; }
.hex-center {
  padding: 14px 28px;
  background: rgba(192,132,252,0.12); border: 1.5px solid rgba(192,132,252,0.25);
  border-radius: 12px; font-size: 14px; font-weight: 700; color: var(--text-primary);
  display: flex; flex-direction: column; align-items: center;
  box-shadow: 0 0 12px rgba(192,132,252,0.08);
}
.hex-ring { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.hex-cell {
  padding: 10px 16px;
  background: rgba(192,132,252,0.05); border: 1px solid rgba(192,132,252,0.1);
  border-radius: 8px; text-align: center; font-size: 13px; font-weight: 700;
  color: var(--text-primary);
  display: flex; flex-direction: column; align-items: center;
}
.hx-pos { font-size: 9px; color: var(--text-muted); font-weight: 400; margin-top: 2px; }

/* ====== 关系牌阵 ====== */
.layout-relationship { padding: 12px 0; }
.rel-row { display: flex; align-items: center; justify-content: center; gap: 14px; margin-bottom: 14px; }
.rel-card {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 14px 24px;
  background: rgba(192,132,252,0.07); border: 1px solid rgba(192,132,252,0.12);
  border-radius: 10px; min-width: 80px;
}
.rel-card.reversed { border-color: rgba(251,191,36,0.25); }
.rel-connector { font-size: 20px; }
.rl-pos { font-size: 10px; color: var(--text-muted); }
.rl-name { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.rel-details { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.rel-chip {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 8px 14px;
  background: rgba(192,132,252,0.04); border: 1px solid rgba(192,132,252,0.08);
  border-radius: 8px;
}
.rel-chip.reversed { border-color: rgba(251,191,36,0.25); }
.rc-pos { font-size: 9px; color: var(--text-muted); }
.rc-name { font-size: 12px; font-weight: 600; color: var(--text-primary); }

/* ====== 自由排布 ====== */
.layout-free {
  position: relative; width: 100%; aspect-ratio: 1.6;
  background: rgba(192,132,252,0.02);
  border: 1px solid rgba(192,132,252,0.08); border-radius: 10px;
  margin: 4px 0;
}
.layout-free .free-card {
  position: absolute;
  min-width: 50px; padding: 6px 10px;
  background: rgba(192,132,252,0.1); border: 1.5px solid rgba(192,132,252,0.2);
  border-radius: 8px;
  display: flex; flex-direction: column; align-items: center; gap: 2px;
}
.layout-free .free-card.reversed { border-color: rgba(251,191,36,0.3); }
.fcp-pos { font-size: 9px; color: var(--text-muted); }
.fcp-name { font-size: 12px; font-weight: 700; color: var(--text-primary); }
.fcp-dir { font-size: 9px; padding: 1px 6px; border-radius: 4px; background: rgba(52,211,153,0.15); color: var(--success); }
.layout-free .free-card.reversed .fcp-dir { background: rgba(251,191,36,0.15); color: var(--warning); }

/* ====== 解读卡片组 ====== */
.share-section-col {
  padding: 16px 40px 8px;
  position: relative;
  z-index: 1;
}
.summary-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 14px;
  letter-spacing: 2px;
  text-align: center;
}
.summary-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.summary-card {
  background: rgba(192,132,252,0.05);
  border: 1px solid rgba(192,132,252,0.1);
  border-radius: 10px;
  padding: 14px 18px;
}
.sc-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--primary-light);
  margin-bottom: 6px;
}
.sc-text {
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-primary);
}
.sc-text :deep(strong) { color: var(--accent); }
.sc-text :deep(li) { margin-bottom: 3px; }
.sc-text :deep(p) { margin: 0; }
.sc-text :deep(ul), .sc-text :deep(ol) { padding-left: 16px; margin: 4px 0; }

/* ====== 底部 ====== */
.share-footer {
  text-align: center;
  padding: 20px 40px 24px;
  position: relative;
  z-index: 1;
}
.share-footer p {
  font-size: 11px;
  color: var(--text-muted);
  margin: 0;
}
.share-brand {
  font-size: 14px !important;
  font-weight: 700;
  color: var(--primary-light) !important;
  margin-top: 6px !important;
  letter-spacing: 1px;
}

/* ====== 操作按钮 ====== */
.share-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding: 32px 0;
}
.generated-preview {
  text-align: center;
  padding-bottom: 40px;
}
.generated-preview h3 { margin-bottom: 16px; }
.generated-preview img {
  max-width: 100%;
  border-radius: 12px;
  box-shadow: var(--shadow-lg);
}
.loading, .error-state {
  text-align: center;
  padding: 80px 0;
  color: var(--text-secondary);
}

/* ====== Mobile responsive ====== */
@media (max-width: 640px) {
  .share-card-header { padding: 20px 16px 14px; }
  .share-card-header h1 { font-size: 22px; }
  .share-logo { font-size: 36px; }
  .share-section { padding: 12px 16px; gap: 10px; }
  .section-icon { font-size: 18px; }
  .share-question-text { font-size: 14px; }
  .share-cards-section { padding: 12px 16px 6px; }
  .share-cards-grid { gap: 6px; }
  .dc-name { font-size: 11px; }
  .dc-pos { font-size: 9px; }
  .dc-dir { font-size: 9px; padding: 1px 6px; }

  /* Timeline: smaller cards, arrow adjustment */
  .tl-card { padding: 10px 12px; min-width: 50px; }
  .tl-name { font-size: 12px; }
  .tl-card:not(:last-child)::after { right: -14px; font-size: 14px; }

  /* Stack: max-width 100% */
  .stack-card { max-width: 100%; padding: 10px 16px; gap: 8px; }
  .sk-pos { font-size: 10px; min-width: 40px; }
  .sk-name { font-size: 12px; }

  /* Branch: stack vertically */
  .branch-split { flex-direction: column; align-items: center; gap: 10px; }
  .branch-arm.left { border-right: none; padding-right: 0; border-bottom: 2px solid rgba(192,132,252,0.2); padding-bottom: 10px; }
  .branch-arm.right { border-left: none; padding-left: 0; border-top: 2px solid rgba(192,132,252,0.2); padding-top: 10px; }

  /* Celtic Cross: compact */
  .celtic-cross-layout { flex-direction: column; gap: 12px; }
  .cross-cell, .cross-top, .cross-bottom { padding: 8px 10px; font-size: 11px; min-width: 45px; }
  .cross-x { left: calc(50% - 25px); padding: 4px 10px; font-size: 10px; }
  .staff-area { flex-direction: row; flex-wrap: wrap; justify-content: center; }
  .staff-cell { padding: 6px 10px; min-width: 50px; }
  .st-name { font-size: 11px; }

  /* Hexagram: smaller grid */
  .hex-center { padding: 10px 20px; font-size: 12px; }
  .hex-cell { padding: 8px 10px; font-size: 11px; }
  .hex-ring { gap: 4px; }

  /* Relationship: compact */
  .rel-card { padding: 10px 16px; min-width: 60px; }
  .rel-details { grid-template-columns: repeat(2, 1fr); gap: 6px; }
  .rc-name { font-size: 11px; }

  /* Free layout: smaller aspect ratio */
  .layout-free { aspect-ratio: 1.2; }
  .layout-free .free-card { padding: 4px 7px; min-width: 40px; }
  .fcp-name { font-size: 10px; }

  /* Summary cards: reduced padding */
  .share-section-col { padding: 12px 16px 6px; }
  .summary-card { padding: 10px 14px; }
  .sc-text { font-size: 12px; }

  /* Footer */
  .share-footer { padding: 14px 16px 18px; }

  /* Watermark: smaller */
  .share-card-watermark { font-size: 70px; letter-spacing: 10px; }
}
</style>
