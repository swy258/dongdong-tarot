<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="home">
    <section class="hero-section">
      <div class="hero-icon">🃏</div>
      <h1 class="hero-title">东东塔罗</h1>
      <p class="hero-subtitle">
        以心理学视角探索塔罗智慧<br>
        结合多本经典塔罗著作，用理性与温暖为你解读人生课题
      </p>
      <div class="hero-actions">
        <button class="btn btn-accent btn-lg" @click="router.push('/reading/new')">
          ✨ 开始占卜
        </button>
        <button class="btn btn-secondary btn-lg" @click="router.push('/spreads')">
          📐 浏览牌阵
        </button>
      </div>
    </section>

    <section class="features grid-3">
      <div class="card feature-card">
        <div class="feature-icon">📚</div>
        <h3>经典文献知识库</h3>
        <p>深度参考《塔罗葵花宝典》《你已经很塔罗了》《78度的智慧》《你可以再塔罗一点》等多本经典塔罗著作</p>
      </div>
      <div class="card feature-card">
        <div class="feature-icon">🧠</div>
        <h3>心理学视角解读</h3>
        <p>融合荣格心理学与个人成长理论，提供深度自我觉察与实用建议，拒绝神秘主义话术</p>
      </div>
      <div class="card feature-card">
        <div class="feature-icon">🎴</div>
        <h3>灵活自定义牌阵</h3>
        <p>支持经典牌阵的同时，可自由创建属于你自己的牌阵，定义每个位置的意义</p>
      </div>
    </section>

    <section class="intro-section">
      <div class="card intro-card">
        <h2>🔮 如何使用</h2>
        <div class="steps">
          <div class="step">
            <div class="step-num">1</div>
            <div>
              <strong>选择或创建牌阵</strong>
              <p>从经典牌阵中选择，或自定义你的专属牌阵</p>
            </div>
          </div>
          <div class="step">
            <div class="step-num">2</div>
            <div>
              <strong>输入你的问题</strong>
              <p>在心中默念问题，从78张塔罗牌中抽取对应数量的牌</p>
            </div>
          </div>
          <div class="step">
            <div class="step-num">3</div>
            <div>
              <strong>录入抽到的牌</strong>
              <p>通过搜索、输入或可视化点选的方式录入牌面及正逆位</p>
            </div>
          </div>
          <div class="step">
            <div class="step-num">4</div>
            <div>
              <strong>获取AI解读</strong>
              <p>DeepSeek AI结合经典文献为你提供深度、温暖、实用的解读</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero-section {
  text-align: center;
  padding: 60px 20px 48px;
}
.hero-icon {
  font-size: 72px;
  margin-bottom: 16px;
  filter: drop-shadow(0 0 20px rgba(192,132,252,0.4));
}
.hero-title {
  font-size: 3.5rem;
  background: linear-gradient(135deg, var(--primary-light), var(--accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 16px;
}
.hero-subtitle {
  font-size: 1.15rem;
  color: var(--text-secondary);
  line-height: 1.8;
  max-width: 500px;
  margin: 0 auto 32px;
}
.hero-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}
.btn-lg {
  padding: 16px 32px;
  font-size: 17px;
  border-radius: 12px;
}
.features {
  padding: 20px 0 40px;
}
.feature-card {
  text-align: center;
  padding: 32px 24px;
}
.feature-icon {
  font-size: 48px;
  margin-bottom: 12px;
}
.feature-card h3 {
  margin-bottom: 8px;
}
.feature-card p {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.7;
}
.intro-section {
  padding: 20px 0;
}
.intro-card {
  padding: 40px;
}
.intro-card h2 {
  text-align: center;
  margin-bottom: 32px;
}
.steps {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.step {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}
.step-num {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-dark), var(--primary));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
  flex-shrink: 0;
  color: white;
}
.step strong {
  display: block;
  margin-bottom: 4px;
}
.step p {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0;
}
@media (max-width: 768px) {
  .hero-title { font-size: 2rem; }
  .hero-icon { font-size: 48px; }
}
</style>
