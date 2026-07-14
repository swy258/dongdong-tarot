<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { spreadsAPI, cardsAPI, readingsAPI } from '../api'

const router = useRouter()
const route = useRoute()

const spread = ref(null)
const spreadId = ref(null)
const allCards = ref([])
const question = ref('')

// 每个位置的选牌状态 { positionIndex: { cardName, isReversed } }
const selectedCards = ref({})

// 当前展开选牌面板的位置（用于显示卡牌选择区）
const activePosition = ref(null)

// 搜索文本
const searchText = ref('')
// 筛选
const filterType = ref('')   // '' | 'major' | 'minor'
const filterSuit = ref('')   // '' | '权杖' | '圣杯' | '宝剑' | '星币'

const submitting = ref(false)

onMounted(async () => {
  const sid = route.query.spread_id
  if (sid) {
    spreadId.value = parseInt(sid)
    try {
      const { data } = await spreadsAPI.getOne(spreadId.value)
      spread.value = data
    } catch (err) {
      console.error('Failed to load spread:', err)
    }
  }

  try {
    const { data } = await cardsAPI.getAll({})
    allCards.value = data.cards
  } catch (err) {
    console.error('Failed to load cards:', err)
  }
})

// 已选中的牌名列表
const usedCardNames = computed(() => {
  return Object.values(selectedCards.value)
    .map(v => v?.cardName)
    .filter(Boolean)
})

// 筛选后的卡牌
const filteredCards = computed(() => {
  let cards = allCards.value

  if (filterType.value === 'major') {
    cards = cards.filter(c => c.card_type === 'major')
  } else if (filterType.value === 'minor') {
    cards = cards.filter(c => c.card_type === 'minor')
  }

  if (filterSuit.value) {
    cards = cards.filter(c => c.suit === filterSuit.value)
  }

  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    cards = cards.filter(c =>
      c.name_zh.includes(q) || c.name_en.toLowerCase().includes(q) || c.keywords.includes(q)
    )
  }

  return cards
})

// 大阿尔卡纳
const majorCards = computed(() =>
  filteredCards.value.filter(c => c.card_type === 'major')
)

// 小阿尔卡纳按牌组
const minorBySuit = computed(() => {
  const result = {}
  for (const suit of ['权杖', '圣杯', '宝剑', '星币']) {
    const cards = filteredCards.value.filter(c => c.suit === suit)
    if (cards.length > 0) result[suit] = cards
  }
  return result
})

// 点击位置槽位 → 切换选牌面板
const togglePosition = (posIndex) => {
  activePosition.value = activePosition.value === posIndex ? null : posIndex
}

// 选取一张牌
const pickCard = (card) => {
  const pos = activePosition.value
  if (pos === null || pos === undefined) return
  if (usedCardNames.value.includes(card.name_zh)) return

  selectedCards.value = {
    ...selectedCards.value,
    [pos]: { cardName: card.name_zh, isReversed: false }
  }
  // 自动移到下一个位置
  autoAdvance(pos)
}

// 直接输入牌名选取
const inputCardName = ref('')
const pickCardByName = () => {
  const name = inputCardName.value.trim()
  if (!name) return
  const card = allCards.value.find(c => c.name_zh === name)
  if (card) {
    pickCard(card)
    inputCardName.value = ''
  }
}

// 移除某位置的牌
const removeCard = (posIndex) => {
  const newCards = { ...selectedCards.value }
  delete newCards[posIndex]
  selectedCards.value = newCards
  activePosition.value = posIndex
}

// 切换正逆位
const flipReversed = (posIndex) => {
  if (!selectedCards.value[posIndex]) return
  selectedCards.value = {
    ...selectedCards.value,
    [posIndex]: {
      ...selectedCards.value[posIndex],
      isReversed: !selectedCards.value[posIndex].isReversed
    }
  }
}

// 自动前进到下一个未选位置
const autoAdvance = (currentPos) => {
  if (!spread.value) return
  const positions = spread.value.positions
  // 找到下一个未选的位置
  for (const pos of positions) {
    if (pos.index > currentPos && !selectedCards.value[pos.index]) {
      activePosition.value = pos.index
      return
    }
  }
  // 如果后面都选了，检查前面有没有未选的
  for (const pos of positions) {
    if (!selectedCards.value[pos.index]) {
      activePosition.value = pos.index
      return
    }
  }
  // 全部选完了
  activePosition.value = null
}

const allSelected = computed(() => {
  if (!spread.value) return false
  return spread.value.positions.every(p => selectedCards.value[p.index])
})

const handleSubmit = async () => {
  if (!allSelected.value || !question.value.trim()) return
  submitting.value = true
  try {
    const cardsDrawn = spread.value.positions.map(pos => ({
      position: pos.index,
      position_name: pos.name,
      card_name: selectedCards.value[pos.index].cardName,
      is_reversed: selectedCards.value[pos.index].isReversed,
    }))

    const { data } = await readingsAPI.create({
      spread_id: spreadId.value,
      question: question.value,
      cards_drawn: cardsDrawn,
    })

    router.push(`/reading/${data.reading_id}`)
  } catch (err) {
    alert(err.response?.data?.detail || '提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

const getCardByName = (name) => allCards.value.find(c => c.name_zh === name)
</script>

<template>
  <div class="new-reading-page fade-in">
    <div class="page-header">
      <button class="back-btn" @click="router.push('/spreads')">← 返回牌阵</button>
      <h1>开始占卜</h1>
      <p v-if="spread">{{ spread.name }} · {{ spread.position_count }} 张牌</p>
    </div>

    <!-- 没选牌阵 -->
    <div v-if="!spread" class="card" style="text-align:center;padding:40px;">
      <h3>请先选择牌阵</h3>
      <button class="btn btn-accent" style="margin-top:16px;" @click="router.push('/spreads')">选择牌阵</button>
    </div>

    <template v-if="spread">
      <!-- 问题输入 -->
      <div class="card question-card">
        <h3>你想探索什么问题？</h3>
        <p>在心中默念问题，然后输入在这里</p>
        <textarea
          v-model="question"
          class="input"
          rows="3"
          placeholder="例如：我最近在感情上感到迷茫，想了解自己需要关注什么..."
        ></textarea>
      </div>

      <!-- 选牌区 -->
      <div class="card selection-card">
        <h3>录入你抽到的牌（点击位置开始选牌）</h3>

        <!-- 位置槽位 -->
        <div class="position-slots">
          <div
            v-for="pos in spread.positions"
            :key="pos.index"
            class="position-slot"
            :class="{
              active: activePosition === pos.index,
              filled: selectedCards[pos.index]
            }"
            @click="togglePosition(pos.index)"
          >
            <div class="slot-number">{{ pos.index }}</div>
            <div class="slot-info">
              <div class="slot-name">{{ pos.name }}</div>
              <div v-if="selectedCards[pos.index]" class="slot-card-name">
                {{ selectedCards[pos.index].cardName }}
                <span :class="selectedCards[pos.index].isReversed ? 'rev' : 'up'">
                  {{ selectedCards[pos.index].isReversed ? '逆位' : '正位' }}
                </span>
                <button class="btn-remove" @click.stop="removeCard(pos.index)">x</button>
              </div>
              <div v-else class="slot-empty">点击选牌</div>
            </div>
            <!-- 正逆位切换（已选牌时显示） -->
            <button
              v-if="selectedCards[pos.index]"
              class="btn btn-sm btn-secondary"
              @click.stop="flipReversed(pos.index)"
            >
              {{ selectedCards[pos.index].isReversed ? '逆位 ↓' : '正位 ↑' }}
            </button>
          </div>
        </div>

        <!-- 卡牌选择面板 -->
        <div v-if="activePosition !== null" class="selection-panel">
          <div class="panel-bar">
            <span>为 <strong>{{ spread.positions.find(p => p.index === activePosition)?.name }}</strong> 选牌</span>
            <button class="btn btn-sm btn-secondary" @click="activePosition = null">收起</button>
          </div>

          <!-- 搜索框 -->
          <div class="search-bar">
            <input v-model="searchText" class="input" placeholder="搜索牌名..." />
            <div class="filter-row">
              <button :class="{ on: filterType === '' }" @click="filterType = ''; filterSuit = ''">全部</button>
              <button :class="{ on: filterType === 'major' }" @click="filterType = 'major'; filterSuit = ''">大牌</button>
              <button :class="{ on: filterSuit === '权杖' }" @click="filterSuit = filterSuit === '权杖' ? '' : '权杖'">权杖</button>
              <button :class="{ on: filterSuit === '圣杯' }" @click="filterSuit = filterSuit === '圣杯' ? '' : '圣杯'">圣杯</button>
              <button :class="{ on: filterSuit === '宝剑' }" @click="filterSuit = filterSuit === '宝剑' ? '' : '宝剑'">宝剑</button>
              <button :class="{ on: filterSuit === '星币' }" @click="filterSuit = filterSuit === '星币' ? '' : '星币'">星币</button>
            </div>
          </div>

          <!-- 直接输入 -->
          <div class="input-row">
            <input
              v-model="inputCardName"
              class="input"
              placeholder="或直接输入牌名（如：愚者）"
              list="card-list"
              @keyup.enter="pickCardByName"
            />
            <datalist id="card-list">
              <option v-for="c in allCards" :key="c.id" :value="c.name_zh" />
            </datalist>
            <button class="btn btn-primary btn-sm" @click="pickCardByName">确认</button>
          </div>

          <!-- 卡牌网格 -->
          <div class="card-grid-wrapper">
            <template v-if="filteredCards.length === 0">
              <p class="no-result">没有匹配的牌</p>
            </template>

            <!-- 大阿尔卡纳 -->
            <div v-if="majorCards.length > 0" class="card-section">
              <h5>大阿尔卡纳</h5>
              <div class="card-grid">
                <button
                  v-for="card in majorCards"
                  :key="card.id"
                  class="card-btn"
                  :class="{ used: usedCardNames.includes(card.name_zh) }"
                  :disabled="usedCardNames.includes(card.name_zh)"
                  @click="pickCard(card)"
                >
                  <span class="card-num">{{ card.number }}</span>
                  <span class="card-label">{{ card.name_zh }}</span>
                </button>
              </div>
            </div>

            <!-- 小阿尔卡纳 -->
            <div v-for="(cards, suit) in minorBySuit" :key="suit" class="card-section">
              <h5>{{ suit }}</h5>
              <div class="card-grid">
                <button
                  v-for="card in cards"
                  :key="card.id"
                  class="card-btn minor"
                  :class="{ used: usedCardNames.includes(card.name_zh) }"
                  :disabled="usedCardNames.includes(card.name_zh)"
                  @click="pickCard(card)"
                >
                  <span class="card-label">{{ card.name_zh.replace(suit, '') }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 提交 -->
        <div class="submit-area">
          <button
            class="btn btn-accent btn-lg btn-block"
            :disabled="!allSelected || !question.trim() || submitting"
            @click="handleSubmit"
          >
            {{ submitting ? '提交中...' : `开始解读（${Object.keys(selectedCards).length}/${spread.position_count}张已选）` }}
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.question-card, .selection-card {
  padding: 32px;
  margin-bottom: 24px;
}
.question-card h3, .selection-card h3 { margin-bottom: 8px; }
.question-card p, .selection-card > p { color: var(--text-secondary); font-size: 14px; margin-bottom: 16px; }

/* 位置槽位 */
.position-slots {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 20px 0;
}
.position-slot {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  border: 2px solid var(--border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.position-slot:hover { border-color: var(--primary); background: rgba(192,132,252,0.05); }
.position-slot.active { border-color: var(--primary); background: rgba(192,132,252,0.1); }
.position-slot.filled { border-color: var(--success); background: rgba(52,211,153,0.05); }
.slot-number {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: var(--border);
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; flex-shrink: 0; font-size: 15px;
}
.position-slot.filled .slot-number {
  background: linear-gradient(135deg, var(--primary-dark), var(--primary));
  color: white;
}
.slot-info { flex: 1; }
.slot-name { font-weight: 600; }
.slot-card-name { font-size: 15px; color: var(--primary-light); display: flex; align-items: center; gap: 8px; }
.slot-card-name .up { font-size: 11px; color: var(--success); }
.slot-card-name .rev { font-size: 11px; color: var(--warning); }
.btn-remove {
  background: none; border: none; color: var(--error); cursor: pointer;
  font-size: 16px; padding: 0 4px; margin-left: auto;
}
.slot-empty { font-size: 14px; color: var(--text-muted); }

/* 选择面板 */
.selection-panel {
  margin-top: 20px;
  padding: 20px;
  background: var(--bg-input);
  border-radius: 12px;
  border: 1px solid var(--border);
}
.panel-bar {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px;
}
.panel-bar strong { color: var(--primary-light); }

.search-bar { margin-bottom: 14px; }
.search-bar .input { margin-bottom: 10px; }

.filter-row {
  display: flex; gap: 6px; flex-wrap: wrap;
}
.filter-row button {
  padding: 5px 12px; border: 1px solid var(--border); border-radius: 16px;
  background: transparent; color: var(--text-secondary); cursor: pointer;
  font-size: 12px; transition: all 0.15s;
}
.filter-row button.on {
  background: var(--primary); border-color: var(--primary); color: white;
}

.input-row {
  display: flex; gap: 8px; margin-bottom: 16px;
}
.input-row .input { flex: 1; }

/* 卡牌网格 */
.card-grid-wrapper {
  max-height: 400px; overflow-y: auto;
}
.card-section { margin-bottom: 16px; }
.card-section h5 {
  font-size: 13px; color: var(--text-muted); margin-bottom: 8px;
}
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(78px, 1fr));
  gap: 6px;
}
.card-btn {
  aspect-ratio: 3/4;
  border: 2px solid var(--border);
  border-radius: 8px;
  background: var(--bg-card);
  cursor: pointer;
  transition: all 0.15s;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 4px; font-family: var(--font-sans); color: var(--text-primary);
}
.card-btn:hover { border-color: var(--primary); transform: translateY(-2px); }
.card-btn:active { transform: scale(0.95); }
.card-btn.used { opacity: 0.35; cursor: not-allowed; border-color: var(--border); }
.card-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.card-num { font-size: 10px; color: var(--text-muted); }
.card-label { font-size: 11px; font-weight: 600; text-align: center; word-break: keep-all; }
.card-btn.minor { aspect-ratio: 3/5; }
.no-result { text-align: center; color: var(--text-muted); padding: 30px; }

.back-btn {
  display: inline-flex; align-items: center; gap: 4px;
  background: none; border: 1px solid var(--border); border-radius: 8px;
  color: var(--text-secondary); cursor: pointer; font-size: 14px;
  padding: 6px 14px; margin-bottom: 12px; transition: all 0.2s;
  font-family: var(--font-sans);
}
.back-btn:hover { border-color: var(--primary); color: var(--primary-light); }

.submit-area { margin-top: 28px; }
</style>
