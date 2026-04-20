"""
youtubedb/core/content_refinery.py
=====================================
從逐字稿自動拆解觀念結構，並逐觀念生成知識庫條目（標準回答 + Q&A）。

遷移自：
  sorlinebot0121/content_refinery.py
  sorlinebot0121/content_refinery_auditor.py

用法：
    from core.content_refinery import analyze_structure, generate_concept_detail, refine_transcript

    with open("my_transcript.txt") as f:
        text = f.read()

    # 步驟一：讓 AI 拆解出觀念骨架
    structure = analyze_structure(text)

    # 步驟二：逐觀念生成詳細內容
    for i, concept in enumerate(structure["concepts"]):
        content = generate_concept_detail(text, concept["title"], concept["summary"], i+1)
        print(content)
"""

import os
import json
from openai import OpenAI

# ─── 設定 ─────────────────────────────────────────
def _get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ 請設定環境變數 OPENAI_API_KEY")
    return OpenAI(api_key=api_key)


# ─── 第一階段：建築師（拆解觀念骨架） ───────────────

def analyze_structure(full_text: str, max_chars: int = 60000) -> dict | None:
    """
    讀取逐字稿，請 GPT-4o 按「話題自然轉折」拆解出核心觀念列表。

    回傳：
        {"concepts": [{"title": str, "summary": str}, ...]}
        失敗回傳 None
    """
    client = _get_client()
    print("   🏗️  結構分析中（建築師模式）...")

    prompt = f"""
    你是【蕭博士】的內容架構師。
    請閱讀以下長篇逐字稿，根據內容的「自然邏輯轉折」，將其拆解為適當數量的「核心觀念」。

    【要求】：
    1. 不用管時間長度，請依照話題的轉換來分段。
    2. 數量不限，通常 2 小時的演講約在 5~12 個觀念之間。
    3. 請回傳一個 JSON，只包含「標題」與「簡短摘要」。

    【回傳格式（JSON）】:
    {{
        "concepts": [
            {{"title": "觀念1標題", "summary": "簡述..."}},
            {{"title": "觀念2標題", "summary": "簡述..."}}
        ]
    }}

    【逐字稿】（前 {max_chars} 字）：
    {full_text[:max_chars]}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"   ❌ 結構分析失敗：{e}")
        return None


# ─── 第二階段：工班（逐觀念生成詳細內容） ────────────

def generate_concept_detail(
    full_text: str,
    concept_title: str,
    concept_summary: str,
    index: int,
) -> str | None:
    """
    針對單一觀念，從逐字稿中提取相關內容，生成標準回答 + 10 組 Q&A。

    回傳：
        格式化的文字字串，失敗回傳 None
    """
    client = _get_client()
    print(f"   🔨 施工觀念 {index}：{concept_title}...")

    prompt = f"""
    你是【蕭博士】的知識庫建置員。
    我們已規劃好一個重點單元，請從「完整逐字稿」中提取相關內容，製作標準問答。

    【當前單元】：
    * 標題：{concept_title}
    * 範圍摘要：{concept_summary}

    【任務】：
    1. Standard Answer（標準回答）：撰寫約 200 字的精煉回答，解釋這個觀念。
    2. Q&A Pairs（問答庫）：生成 10 組針對這個觀念的問答。

    【輸出格式】：
    ===觀念 {index} : {concept_title}===
    [STANDARD_ANSWER_START]
    （200字回答）
    [STANDARD_ANSWER_END]

    [QUESTIONS_START]
    1. （問題1）
    ...
    10. （問題10）
    [QUESTIONS_END]

    ---

    【完整逐字稿】：
    {full_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"   ❌ 觀念 {concept_title} 生成失敗：{e}")
        return None


# ─── 整合流程（一鍵執行 ─────────────────────────────

def refine_transcript(
    transcript_path: str,
    output_file: str = "knowledge_base.txt",
) -> bool:
    """
    完整流程：讀取逐字稿 → 拆解結構 → 逐觀念生成 → 寫入知識庫。

    參數：
        transcript_path : .txt 逐字稿路徑
        output_file     : 輸出知識庫路徑

    回傳：
        成功回傳 True
    """
    if not os.path.exists(transcript_path):
        print(f"❌ 找不到逐字稿：{transcript_path}")
        return False

    with open(transcript_path, "r", encoding="utf-8") as f:
        text = f.read()

    print(f"\n📄 分析：{os.path.basename(transcript_path)}")

    structure = analyze_structure(text)
    if not structure or "concepts" not in structure:
        print("❌ 結構分析失敗")
        return False

    concepts = structure["concepts"]
    print(f"   📊 共 {len(concepts)} 個核心觀念")

    results = []
    for i, concept in enumerate(concepts):
        result = generate_concept_detail(text, concept["title"], concept["summary"], i + 1)
        if result:
            results.append(result)

    if results:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"Source: {os.path.basename(transcript_path)}\n")
            f.write(f"Concepts: {len(concepts)}\n")
            f.write("\n\n".join(results))
            f.write("\n" + "=" * 50 + "\n")
        print(f"✅ {len(results)} 個觀念已存入：{output_file}")
        return True

    return False
