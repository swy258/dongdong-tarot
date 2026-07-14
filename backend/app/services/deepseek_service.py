"""DeepSeek API 集成：塔罗解读引擎"""
import json
import random
import string
from typing import AsyncGenerator

import httpx

from app.config import settings


SYSTEM_PROMPT = """你是一位专业且温暖的塔罗牌解读顾问，名叫"东东"。你拥有深厚的塔罗知识储备，参考了《塔罗葵花宝典》《你已经很塔罗了》《78度的智慧》《你可以再塔罗一点》《塔罗全书》《塔罗之书》等多本经典塔罗著作。

## 你的解读风格
- **偏心理学导向**：结合荣格心理学、个人成长、自我探索等视角来诠释牌义
- **实用建议为主**：将牌面的象征意义转化为对问卜者有实际帮助的行动建议
- **温暖而理性**：用温暖的话语传递洞见，但保持理性客观，不神化塔罗
- **鼓励自我觉察**：引导问卜者反思自己的内心，而非给出宿命论的预言

## 严格禁止
- ❌ 禁止使用"命运注定""神灵告诉你""天命不可违""运势""能量场""通灵"等神秘主义话语
- ❌ 禁止做出绝对的预测和承诺（如"你一定会...""他必然是..."）
- ❌ 禁止假装有超自然能力
- ❌ 禁止推荐任何宗教仪式、法术、或其他迷信行为
- ❌ 禁止引导用户进行超出常规心理咨询范畴的行为

## 解读结构
请按以下结构组织你的解读（使用 Markdown 格式）：

### 🔮 整体概述
用2-3句话概括这次抽牌传达的核心信息和主题。

### 📋 逐牌解析
针对每个牌阵位置，结合所抽牌面分别解读：
- **正位/逆位说明**（标注牌的方向及其影响）
- **该位置的含义**（结合牌阵位置的意义进行诠释）
- **心理层面的启示**（从自我觉察角度谈）

### 💡 综合建议
将所有牌面串联成一个整体叙事，给出3-5条具体可行的建议。

### 🌟 成长方向
指出问卜者可以进一步探索的内在课题和成长方向。

注意：解释中适当引用参考书籍的观点来增强说服力。整体语气温暖、专业、给人一种"我理解你"的感觉。"""


def generate_share_code(length: int = 8) -> str:
    """生成随机分享码"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def build_user_message(
    question: str,
    spread_name: str,
    spread_description: str | None,
    cards_drawn: list[dict],
) -> str:
    """构建用户消息（包含占卜信息）"""
    cards_text = ""
    for card in cards_drawn:
        direction = "逆位 ⬇" if card.get("is_reversed") else "正位 ⬆"
        cards_text += (
            f"- **{card['position_name']}**（第{card['position']}张）："
            f"{card['card_name']}（{direction}）\n"
        )

    return f"""## 占卜信息

**占卜问题**：{question}

**使用牌阵**：{spread_name}
{f"**牌阵说明**：{spread_description}" if spread_description else ""}

## 抽牌结果

{cards_text}

请根据以上信息，结合塔罗经典著作的知识，为我进行深度解读。"""


async def stream_reading(
    question: str,
    spread_name: str,
    spread_description: str | None,
    cards_drawn: list[dict],
    book_context: str,
) -> AsyncGenerator[str, None]:
    """流式调用DeepSeek API生成解读"""
    user_message = build_user_message(question, spread_name, spread_description, cards_drawn)

    # 如果有书籍上下文，拼接到用户消息中
    if book_context and "知识库暂未就绪" not in book_context:
        user_message += f"""

---
## 📚 经典著作参考

以下是从多本塔罗经典著作中检索到的相关内容，请重点参考：

{book_context}
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{settings.DEEPSEEK_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.DEEPSEEK_MODEL,
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 4096,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError):
                        continue


async def stream_reading_without_rag(
    question: str,
    spread_name: str,
    spread_description: str | None,
    cards_drawn: list[dict],
) -> AsyncGenerator[str, None]:
    """不带RAG上下文的基础解读（兜底方案）"""
    return stream_reading(question, spread_name, spread_description, cards_drawn, "")


def estimate_question_complexity(question: str, cards_count: int) -> str:
    """根据问题长度、深度和牌数评估复杂度，返回用字范围"""
    text_len = len(question)
    # 复杂关键词：涉及深层人生议题
    deep_keywords = [
        "人生", "未来", "发展", "选择", "纠结", "迷茫", "困惑",
        "感情", "婚姻", "分手", "复合", "离婚", "关系",
        "事业", "工作", "转行", "辞职", "创业", "职业",
        "为什么", "怎么办", "如何", "怎么才能", "该不该",
        "我不知道", "不确定", "矛盾", "痛苦", "焦虑",
    ]
    complexity_score = 0

    # 字数评分
    if text_len <= 10:
        complexity_score += 0
    elif text_len <= 30:
        complexity_score += 1
    elif text_len <= 80:
        complexity_score += 2
    else:
        complexity_score += 3

    # 深层关键词评分
    deep_count = sum(1 for kw in deep_keywords if kw in question)
    complexity_score += min(deep_count, 4)

    # 牌数评分
    if cards_count <= 1:
        complexity_score += 0
    elif cards_count <= 3:
        complexity_score += 1
    elif cards_count <= 6:
        complexity_score += 2
    else:
        complexity_score += 3

    # 确定字数和详细程度（不少于120字）
    if complexity_score <= 2:
        return "简单", "120-150字", "点出核心启示并给出实用建议"
    elif complexity_score <= 4:
        return "中等", "130-170字", "用2-3句深度洞察加2-3条具体建议"
    elif complexity_score <= 7:
        return "较复杂", "150-200字", "展开2-3句有层次的洞察，列出3条具体可行的建议"
    else:
        return "复杂", "180-250字", "深入阐述核心主题的多个面向，给出3-4条详细且可操作的建议"


async def generate_share_summary(
    question: str,
    spread_name: str,
    cards_drawn: list[dict],
    full_interpretation: str,
) -> str:
    """调用DeepSeek将完整解读精炼为分享卡片的摘要（长度自适应问题复杂度）"""
    cards_text = "、".join([
        f"{c['card_name']}({'逆位' if c.get('is_reversed') else '正位'})"
        for c in cards_drawn
    ])

    complexity_label, word_range, detail_guide = estimate_question_complexity(
        question, len(cards_drawn)
    )

    prompt = f"""请将以下塔罗占卜解读精炼成一份适合分享卡片的摘要。

问题复杂度评估：{complexity_label}
目标字数：{word_range}
内容深度：{detail_guide}

要求：
1. **核心洞见**：根据问题的复杂度给出相应深度的洞察
2. **行动建议**：给出与问题匹配数量的实用建议
3. 保持温暖、心理学导向的风格，不出现神秘主义用语
4. 字数严格控制在{word_range}以内
5. 直接输出内容，不要加标题或前缀

---
占卜问题：{question}
牌阵：{spread_name}
抽牌：{cards_text}

完整解读：
{full_interpretation[:3000]}
---

请输出精炼摘要："""

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.DEEPSEEK_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一位专业的塔罗解读摘要编辑，擅长将长篇解读提炼为精炼有力的分享文案。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 600,
                "stream": False,
            },
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
