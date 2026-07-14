<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { spreadsAPI } from '../api'

const router = useRouter()
const name = ref('')
const description = ref('')
const layoutType = ref('grid')
const positions = ref([
  { index: 1, name: '', meaning: '' },
  { index: 2, name: '', meaning: '' },
  { index: 3, name: '', meaning: '' },
])
const saving = ref(false)
const error = ref('')

// 自由排布 - 每个位置在画布上的坐标 (百分比)
const layoutCoords = ref({})

const addPosition = () => {
  const idx = positions.value.length + 1
  positions.value.push({ index: idx, name: '', meaning: '' })
  // 为新位置分配随机坐标
  layoutCoords.value[idx] = { x: 10 + Math.random() * 30, y: 10 + Math.random() * 40 }
}

const removePosition = (index) => {
  if (positions.value.length <= 1) return
  const removed = positions.value[index]
  delete layoutCoords.value[removed.index]
  positions.value.splice(index, 1)
  positions.value.forEach((p, i) => p.index = i + 1)
  // 刷新坐标映射
  syncCoords()
}

const syncCoords = () => {
  const coords = { ...layoutCoords.value }
  layoutCoords.value = {}
  positions.value.forEach((p, i) => {
    const oldIdx = Object.keys(coords).find(k => !positions.value.find(pp => pp.index === parseInt(k)))
    // 重新映射：让新 index 获得旧的坐标（按顺序）
  })
  // 给没有坐标的分配默认值
  positions.value.forEach((p, i) => {
    if (!layoutCoords.value[p.index]) {
      const col = i % 4
      const row = Math.floor(i / 4)
      layoutCoords.value[p.index] = { x: 5 + col * 24, y: 5 + row * 22 }
    }
  })
}

// 初始化坐标
syncCoords()

// 自由拖拽
const canvasRef = ref(null)
const draggingCard = ref(null)
const dragOffset = ref({ x: 0, y: 0 })

const onMouseDown = (e, posIndex) => {
  if (layoutType.value !== 'custom') return
  e.preventDefault()
  draggingCard.value = posIndex
  const rect = canvasRef.value.getBoundingClientRect()
  dragOffset.value = {
    x: e.clientX - rect.left - (layoutCoords.value[posIndex]?.x || 0) * rect.width / 100,
    y: e.clientY - rect.top - (layoutCoords.value[posIndex]?.y || 0) * rect.height / 100,
  }
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

const onMouseMove = (e) => {
  if (!draggingCard.value || !canvasRef.value) return
  const rect = canvasRef.value.getBoundingClientRect()
  const x = ((e.clientX - rect.left - dragOffset.value.x) / rect.width) * 100
  const y = ((e.clientY - rect.top - dragOffset.value.y) / rect.height) * 100
  layoutCoords.value[draggingCard.value] = {
    x: Math.max(0, Math.min(90, x)),
    y: Math.max(0, Math.min(85, y)),
  }
}

const onMouseUp = () => {
  draggingCard.value = null
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
}

// 预设排布模板
const applyCoordinatePreset = (type) => {
  const count = positions.value.length
  layoutCoords.value = {}
  if (type === 'row') {
    positions.value.forEach((p, i) => {
      layoutCoords.value[p.index] = { x: 3 + i * (92 / (count - 1 || 1)), y: 42 }
    })
  } else if (type === 'col') {
    positions.value.forEach((p, i) => {
      layoutCoords.value[p.index] = { x: 45, y: 3 + i * (82 / (count - 1 || 1)) }
    })
  } else if (type === 'circle') {
    positions.value.forEach((p, i) => {
      const angle = (i / count) * Math.PI * 2 - Math.PI / 2
      layoutCoords.value[p.index] = {
        x: 48 + Math.cos(angle) * 30,
        y: 45 + Math.sin(angle) * 28,
      }
    })
  } else if (type === 'cross') {
    // 十字形
    const mid = Math.floor(count / 2)
    positions.value.forEach((p, i) => {
      if (i === 0) { layoutCoords.value[p.index] = { x: 42, y: 42 } }
      else if (i % 2 === 1) { layoutCoords.value[p.index] = { x: 42 + (i * 8), y: 42 } }
      else { layoutCoords.value[p.index] = { x: 42, y: 42 + ((i/2) * 8) } }
    })
  } else if (type === 'vshape') {
    // V型
    positions.value.forEach((p, i) => {
      layoutCoords.value[p.index] = {
        x: 5 + i * (88 / (count - 1)),
        y: i <= Math.floor(count / 2) ? 10 + i * 14 : 80 - (count - 1 - i) * 14,
      }
    })
  }
}

const layoutOptions = [
  { v: 'grid', n: '网格', p: '均衡排列' },
  { v: 'timeline', n: '时间线', p: '水平箭头' },
  { v: 'stack', n: '层叠', p: '纵向排列' },
  { v: 'branch', n: '分叉', p: 'Y型决策' },
  { v: 'hexagram', n: '六芒星', p: '中心环绕' },
  { v: 'relationship', n: '关系', p: '双方对照' },
  { v: 'custom', n: '自由排布', p: '拖拽任意位置' },
]

const handleSave = async () => {
  error.value = ''
  if (!name.value.trim()) { error.value = '请输入牌阵名称'; return }
  const emptyPos = positions.value.find(p => !p.name.trim())
  if (emptyPos) { error.value = `第${emptyPos.index}个位置的名称为空`; return }

  saving.value = true
  try {
    const { data } = await spreadsAPI.create({
      name: name.value,
      description: description.value,
      layout_type: layoutType.value,
      positions: positions.value.map(p => ({
        index: p.index, name: p.name,
        meaning: p.meaning || `${p.name}的含义`,
      })),
      layout_coords: layoutType.value === 'custom' ? layoutCoords.value : null,
    })
    router.push({ path: '/reading/new', query: { spread_id: data.id } })
  } catch (err) {
    error.value = err.response?.data?.detail || '创建失败'
  } finally { saving.value = false }
}
</script>

<template>
  <div class="custom-spread-page fade-in">
    <div class="page-header">
      <h1>自定义牌阵</h1>
      <p>定义位置 + 选择/拖拽排布 = 专属牌阵</p>
    </div>

    <div class="card form-card">
      <div class="form-group">
        <label>牌阵名称</label>
        <input v-model="name" class="input" placeholder="例如：爱情十字阵" />
      </div>
      <div class="form-group">
        <label>牌阵描述</label>
        <textarea v-model="description" class="input" placeholder="描述用途..." rows="2"></textarea>
      </div>

      <!-- 排布方式 -->
      <div class="form-group">
        <label>分享卡片排布方式</label>
        <div class="layout-options">
          <label v-for="opt in layoutOptions" :key="opt.v"
            class="layout-opt" :class="{ on: layoutType === opt.v }">
            <input type="radio" v-model="layoutType" :value="opt.v" />
            <span>{{ opt.n }}</span>
            <small>{{ opt.p }}</small>
          </label>
        </div>
      </div>

      <!-- 自由排布画布 -->
      <div v-if="layoutType === 'custom'" class="custom-canvas-area">
        <div class="canvas-toolbar">
          <span>快速布局：</span>
          <button class="btn btn-sm btn-secondary" @click="applyCoordinatePreset('row')">一横排</button>
          <button class="btn btn-sm btn-secondary" @click="applyCoordinatePreset('col')">一竖列</button>
          <button class="btn btn-sm btn-secondary" @click="applyCoordinatePreset('circle')">环绕</button>
          <button class="btn btn-sm btn-secondary" @click="applyCoordinatePreset('vshape')">V型</button>
          <span class="hint">选模板后还可自由微调</span>
        </div>

        <!-- 画布 -->
        <div ref="canvasRef" class="free-canvas">
          <div v-for="pos in positions" :key="pos.index"
            class="free-card"
            :class="{ dragging: draggingCard === pos.index }"
            :style="{
              left: (layoutCoords[pos.index]?.x || 5) + '%',
              top: (layoutCoords[pos.index]?.y || 5) + '%',
            }"
            @mousedown="onMouseDown($event, pos.index)"
          >
            <span class="fc-idx">{{ pos.index }}</span>
            <span class="fc-name">{{ pos.name || '未命名' }}</span>
          </div>
          <span class="canvas-hint" v-if="positions.length <= 1">➕ 添加更多位置后可拖拽排布</span>
        </div>
      </div>

      <!-- 位置定义 -->
      <div class="positions-section">
        <div class="positions-header">
          <h3>位置定义</h3>
          <button class="btn btn-sm btn-secondary" @click="addPosition">+ 添加</button>
        </div>
        <div class="positions-list">
          <div v-for="(pos, idx) in positions" :key="idx" class="position-row">
            <div class="pos-number">{{ pos.index }}</div>
            <input v-model="pos.name" class="input pos-name" :placeholder="`位置${pos.index}名称`" />
            <input v-model="pos.meaning" class="input pos-meaning" placeholder="代表含义" />
            <button class="btn btn-sm btn-secondary remove-btn"
              @click="removePosition(idx)" :disabled="positions.length <= 1">✕</button>
          </div>
        </div>
      </div>

      <div v-if="error" class="error-msg">{{ error }}</div>

      <div class="form-actions">
        <button class="btn btn-secondary" @click="router.back()">返回</button>
        <button class="btn btn-accent" @click="handleSave" :disabled="saving">
          {{ saving ? '保存中...' : '保存并开始占卜' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.form-card { max-width: 750px; margin: 0 auto; padding: 40px; }
.form-group { margin-bottom: 24px; }
.form-group label { display: block; margin-bottom: 8px; font-weight: 600; color: var(--text-secondary); font-size: 14px; }

/* 排布选项 */
.layout-options { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.layout-opt {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 10px 6px; border: 2px solid var(--border); border-radius: 10px;
  cursor: pointer; transition: all 0.15s; text-align: center;
}
.layout-opt.on { border-color: var(--primary); background: rgba(192,132,252,0.08); }
.layout-opt input { display: none; }
.layout-opt span { font-size: 13px; font-weight: 600; }
.layout-opt small { font-size: 10px; color: var(--text-muted); }

/* 自由排布画布 */
.custom-canvas-area {
  margin: 20px 0; padding: 16px;
  background: var(--bg-input); border: 1px solid var(--border); border-radius: 12px;
}
.canvas-toolbar {
  display: flex; align-items: center; gap: 6px; margin-bottom: 12px;
  font-size: 13px; color: var(--text-secondary); flex-wrap: wrap;
}
.canvas-toolbar .hint { font-size: 11px; color: var(--text-muted); margin-left: auto; }

.free-canvas {
  position: relative;
  width: 100%;
  aspect-ratio: 1.6;
  background:
    radial-gradient(circle, rgba(192,132,252,0.06) 1px, transparent 1px);
  background-size: 20px 20px;
  border: 1px solid var(--border); border-radius: 10px;
  overflow: hidden;
  cursor: default;
}
.canvas-hint {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  color: var(--text-muted); font-size: 13px; pointer-events: none;
}

.free-card {
  position: absolute;
  min-width: 56px;
  padding: 8px 10px;
  background: rgba(192,132,252,0.12);
  border: 2px solid rgba(192,132,252,0.3);
  border-radius: 8px;
  cursor: grab;
  user-select: none;
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  transition: box-shadow 0.15s, border-color 0.15s;
  z-index: 1;
}
.free-card:hover { border-color: var(--primary); box-shadow: 0 0 10px rgba(192,132,252,0.2); }
.free-card.dragging { cursor: grabbing; z-index: 10; border-color: var(--accent); box-shadow: 0 4px 20px rgba(245,158,11,0.3); }
.fc-idx { font-size: 11px; color: var(--text-muted); }
.fc-name { font-size: 12px; font-weight: 700; color: var(--text-primary); white-space: nowrap; }

/* 位置定义 */
.positions-section { margin: 24px 0; }
.positions-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.positions-header h3 { color: var(--primary-light); font-size: 1rem; }
.positions-list { display: flex; flex-direction: column; gap: 10px; }
.position-row { display: flex; gap: 10px; align-items: center; }
.pos-number {
  width: 32px; height: 32px; border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-dark), var(--primary));
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 14px; flex-shrink: 0; color: white;
}
.pos-name { flex: 1; min-width: 100px; }
.pos-meaning { flex: 2; min-width: 130px; }
.remove-btn { flex-shrink: 0; }

.error-msg {
  background: rgba(248,113,113,0.1); border: 1px solid rgba(248,113,113,0.3);
  color: var(--error); padding: 10px 16px; border-radius: 8px; font-size: 14px; margin-bottom: 16px;
}
.form-actions { display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px; }

@media (max-width: 768px) {
  .layout-options { grid-template-columns: repeat(2, 1fr); }
  .position-row { flex-wrap: wrap; }
  .pos-meaning { flex: 1 1 100%; }
}
</style>
