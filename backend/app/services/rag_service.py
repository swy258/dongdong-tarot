"""RAG知识检索服务：PDF文本提取、向量嵌入、语义检索"""
import json
import os
import ssl
from pathlib import Path
from typing import List

import fitz  # PyMuPDF
import numpy as np

from app.config import settings

# 修复 HuggingFace SSL 证书问题
os.environ["HF_HUB_DISABLE_SSL_VERIFY"] = "1"
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""

# 尝试取消 SSL 验证（适用于企业网络环境）
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass


class RAGService:
    """塔罗知识检索增强服务（延迟加载）"""

    def __init__(self):
        self.model = None
        self.chunks: List[dict] = []
        self.embeddings_matrix = None
        self._initialized = False
        self._init_error = None

    def _ensure_initialized(self):
        """延迟初始化：仅在第一次查询时加载"""
        if self._initialized:
            return
        self._initialized = True

        os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
        chunks_path = os.path.join(settings.VECTOR_STORE_DIR, "chunks.json")
        embeddings_path = os.path.join(settings.VECTOR_STORE_DIR, "embeddings.npy")

        # 尝试从缓存加载
        if os.path.exists(chunks_path) and os.path.exists(embeddings_path):
            try:
                print("Loading cached vector store...")
                with open(chunks_path, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                self.embeddings_matrix = np.load(embeddings_path)
                print(f"Loaded {len(self.chunks)} chunks from cache.")
                return
            except Exception as e:
                print(f"Failed to load cache: {e}, rebuilding...")

        # 构建向量存储
        try:
            self._build_from_pdfs()
            if self.chunks and self.embeddings_matrix is not None:
                self._save_vector_store()
        except Exception as e:
            self._init_error = str(e)
            print(f"RAG initialization error: {e}")
            print("Will use keyword-based search as fallback.")

    def _get_model(self):
        """获取嵌入模型（延迟加载）"""
        if self.model is not None:
            return self.model

        # 尝试加载 HuggingFace 模型
        model_names = [
            "paraphrase-multilingual-MiniLM-L12-v2",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        ]

        for model_name in model_names:
            try:
                from sentence_transformers import SentenceTransformer
                print(f"Loading embedding model: {model_name}")
                self.model = SentenceTransformer(
                    model_name,
                    trust_remote_code=True,
                )
                print("Embedding model loaded successfully.")
                return self.model
            except Exception as e:
                print(f"Failed to load {model_name}: {e}")

        # 如果所有模型都加载失败，尝试使用本地简单嵌入
        print("WARNING: Could not load any embedding model. Using TF-IDF-like fallback.")
        return None

    def _get_simple_embedding(self, text: str, vocab: dict = None) -> np.ndarray:
        """简单字符级嵌入作为fallback（不依赖外部模型）"""
        # 使用字符bigram作为特征
        vec = np.zeros(1024, dtype=np.float32)
        for i in range(len(text) - 1):
            bigram = text[i:i+2]
            idx = hash(bigram) % 1024
            vec[idx] += 1
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def _save_vector_store(self):
        chunks_path = os.path.join(settings.VECTOR_STORE_DIR, "chunks.json")
        embeddings_path = os.path.join(settings.VECTOR_STORE_DIR, "embeddings.npy")
        with open(chunks_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        np.save(embeddings_path, self.embeddings_matrix)

    def _build_from_pdfs(self):
        """从所有PDF提取文本并向量化"""
        books_dir = Path(settings.BOOKS_DIR)
        if not books_dir.exists():
            print(f"Books directory not found: {settings.BOOKS_DIR}")
            return

        pdf_files = list(books_dir.glob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files.")

        all_chunks = []

        for pdf_path in pdf_files:
            book_name = pdf_path.stem
            print(f"Processing: {book_name}")

            try:
                doc = fitz.open(str(pdf_path))
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text()

                    if not text.strip():
                        continue

                    paragraphs = text.split("\n\n")
                    for para in paragraphs:
                        para = para.strip().replace("\n", " ")
                        if len(para) < 50:
                            continue

                        chunk = {
                            "text": para[:2000],
                            "book": book_name,
                            "page": page_num + 1,
                            "card_names": self._find_card_names(para),
                        }
                        all_chunks.append(chunk)

                doc.close()
            except Exception as e:
                print(f"Error processing {book_name}: {e}")

        print(f"Total chunks extracted: {len(all_chunks)}")

        if not all_chunks:
            print("No text extracted from PDFs!")
            return

        self.chunks = all_chunks

        # 向量化
        model = self._get_model()
        texts = [chunk["text"] for chunk in all_chunks]
        print("Generating embeddings...")

        if model is not None:
            # 使用sentence-transformers模型
            embeddings = model.encode(texts, show_progress_bar=True)
        else:
            # Fallback: 使用简单嵌入
            print("Using simple fallback embeddings...")
            embeddings = np.array([self._get_simple_embedding(t) for t in texts])

        self.embeddings_matrix = np.array(embeddings)
        print("Vector store built successfully.")

    def _find_card_names(self, text: str) -> List[str]:
        """在文本中寻找提到的塔罗牌名"""
        card_keywords = [
            "愚者", "魔术师", "女祭司", "女皇", "皇帝", "教皇",
            "恋人", "战车", "力量", "隐者", "命运之轮", "正义",
            "倒吊人", "死神", "节制", "恶魔", "高塔", "星星", "月亮", "太阳",
            "审判", "世界",
            "权杖王牌", "权杖一", "权杖二", "权杖三", "权杖四", "权杖五",
            "权杖六", "权杖七", "权杖八", "权杖九", "权杖十",
            "权杖侍从", "权杖骑士", "权杖王后", "权杖国王",
            "圣杯王牌", "圣杯一", "圣杯二", "圣杯三", "圣杯四", "圣杯五",
            "圣杯六", "圣杯七", "圣杯八", "圣杯九", "圣杯十",
            "圣杯侍从", "圣杯骑士", "圣杯王后", "圣杯国王",
            "宝剑王牌", "宝剑一", "宝剑二", "宝剑三", "宝剑四", "宝剑五",
            "宝剑六", "宝剑七", "宝剑八", "宝剑九", "宝剑十",
            "宝剑侍从", "宝剑骑士", "宝剑王后", "宝剑国王",
            "星币王牌", "星币一", "星币二", "星币三", "星币四", "星币五",
            "星币六", "星币七", "星币八", "星币九", "星币十",
            "星币侍从", "星币骑士", "星币王后", "星币国王",
        ]

        found = []
        for kw in card_keywords:
            if kw in text:
                found.append(kw)
        return found

    def search(self, query: str, drawn_cards: List[str], top_k: int = 15) -> str:
        """
        搜索相关知识（延迟初始化）
        """
        self._ensure_initialized()

        if not self.chunks:
            return "（知识库暂未就绪，将依靠DeepSeek自身知识进行解读）"

        # 关键词搜索 + 向量搜索
        if self.embeddings_matrix is not None and self._get_model() is not None:
            return self._semantic_search(query, drawn_cards, top_k)
        else:
            return self._keyword_search(drawn_cards, top_k)

    def _semantic_search(self, query: str, drawn_cards: List[str], top_k: int) -> str:
        """语义搜索（有嵌入模型时使用）"""
        model = self._get_model()
        if model is None:
            return self._keyword_search(drawn_cards, top_k)

        card_names_str = "、".join(drawn_cards)
        enhanced_query = f"问题：{query}。涉及塔罗牌：{card_names_str}"

        query_embedding = model.encode([enhanced_query])
        scores = np.dot(self.embeddings_matrix, query_embedding.T).flatten()

        # 关键词加分
        keyword_boost = np.zeros(len(self.chunks))
        for i, chunk in enumerate(self.chunks):
            for card in drawn_cards:
                if card in chunk["card_names"]:
                    keyword_boost[i] += 0.3
            if any(kw in chunk["text"] for kw in drawn_cards):
                keyword_boost[i] += 0.1

        combined_scores = scores + keyword_boost
        top_indices = combined_scores.argsort()[-top_k:][::-1]

        results = []
        for idx in top_indices:
            if combined_scores[idx] > 0.1:
                chunk = self.chunks[idx]
                results.append(
                    f"【{chunk['book']} 第{chunk['page']}页】\n{chunk['text']}"
                )

        if not results:
            return "（知识库中未找到高度相关的段落，将依靠DeepSeek自身知识进行解读）"

        return "\n\n---\n\n".join(results)

    def _keyword_search(self, drawn_cards: List[str], top_k: int) -> str:
        """纯关键词搜索（fallback，不需要嵌入模型）"""
        scored = []
        for i, chunk in enumerate(self.chunks):
            score = 0
            for card in drawn_cards:
                if card in chunk["card_names"]:
                    score += 3
                count = chunk["text"].count(card)
                if count > 0:
                    score += count
            if score > 0:
                scored.append((score, i))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_chunks = scored[:top_k]

        results = []
        for score, idx in top_chunks:
            chunk = self.chunks[idx]
            results.append(
                f"【{chunk['book']} 第{chunk['page']}页】\n{chunk['text']}"
            )

        if not results:
            return "（知识库中未找到高度相关的段落，将依靠DeepSeek自身知识进行解读）"

        return "\n\n---\n\n".join(results)


# 全局单例（延迟初始化）
rag_service = RAGService()
