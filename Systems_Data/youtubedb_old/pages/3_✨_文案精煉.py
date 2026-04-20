import streamlit as st
import sys
import os
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

st.set_page_config(page_title="文案精煉 · 蕭博士 SoR", page_icon="✨", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans TC', 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #2d1a00 0%, #0D1117 100%);
    border-radius: 16px; padding: 2rem 2.5rem; margin-bottom: 1.5rem;
    border: 1px solid rgba(251,191,36,0.2);
}
.page-header h1 { font-size: 1.8rem; font-weight: 700; color: #E6EDF3; margin: 0 0 0.3rem; }
.page-header p { color: rgba(230,237,243,0.55); margin: 0; font-size: 0.9rem; }
.tab-content { background: rgba(22,27,34,0.8); border-radius: 12px; padding: 1.5rem; margin-top: 1rem; border: 1px solid rgba(48,54,61,0.6); }
.concept-chip {
    display: inline-block; background: rgba(251,191,36,0.12); border: 1px solid rgba(251,191,36,0.3);
    color: #fbbf24; border-radius: 20px; padding: 0.25rem 0.9rem; margin: 0.2rem;
    font-size: 0.82rem; font-weight: 500;
}
section[data-testid="stSidebar"] { background: #0D1117 !important; border-right: 1px solid rgba(48,54,61,0.6); }
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="page-header">
    <h1>✨ 文案精煉 — Step 2</h1>
    <p>在這裡選取素材（逐字稿/貼文），套用 Step 1 設定好的 Prompt 生成完整文案。確認後再到 Step 3 產出各平台格式。</p>
</div>
""", unsafe_allow_html=True)

# 流程提示
st.markdown("""
<div class="flow-bar">
    <span class="flow-inactive">⚙️ Step 1 設定規則</span>
    <span class="flow-arrow">──►</span>
    <span class="flow-step">✨ Step 2 文案精煉（你在這裡）</span>
    <span class="flow-arrow">──►</span>
    <span class="flow-inactive">🚀 Step 3 行銷素材（套格式輸出）</span>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([
    "📝 1. 文案生成（套用 Prompt）", 
    "🏗️ 2. 知識庫生成（舊版）", 
    "🎬 3. 互動修改（導演模式）"
])

# ─────────────────────────────────────────────────────────────────────────────
# Tab 1：文案生成 (Step 2 主力)
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("#### 📄 選擇素材並生成文案")
    
    # 載入 Step 1 選擇的 Prompt
    try:
        from core.utils import load_prompts, generate_sor_stream
        prompts = load_prompts()
        import json
        prompts_path = os.path.join(os.path.dirname(__file__), "..", "core", "prompts.json")
        default_p = next((p for p in prompts if p.get("is_default")), prompts[0])
    except Exception as e:
        st.error(f"無法載入 Prompt：{e}")
        default_p = None

    if default_p:
        st.info(f"💡 目前使用的 Prompt：**{default_p['name']}** （前往「⚙️ Prompt 管理」可更換）")
    
    c_src, c_text = st.columns([1, 2])
    
    transcript_text = ""
    video_title = "未命名素材"
    
    with c_src:
        source_mode = st.radio("素材來源", ["從已採收的檔案選取", "直接貼入文字", "上傳 txt/srt"])
        
        if source_mode == "從已採收的檔案選取":
            from core.config import SOURCE_DIR
            files = sorted(glob.glob(os.path.join(SOURCE_DIR, "*.txt")) + 
                           glob.glob(os.path.join(SOURCE_DIR, "*.srt")))
            if files:
                selected = st.selectbox("選擇檔案", [os.path.basename(f) for f in files])
                full_path = os.path.join(SOURCE_DIR, selected)
                video_title = os.path.splitext(selected)[0]
                with open(full_path, "r", encoding="utf-8") as f:
                    raw = f.read()
                if selected.endswith(".srt"):
                    from core.utils import clean_srt_to_text
                    transcript_text = clean_srt_to_text(raw)
                else:
                    transcript_text = raw
            else:
                st.warning("尚無檔案")
        elif source_mode == "上傳 txt/srt":
            uploaded = st.file_uploader("上傳檔案", type=["txt", "srt"])
            if uploaded:
                raw = uploaded.read().decode("utf-8")
                video_title = os.path.splitext(uploaded.name)[0]
                if uploaded.name.endswith(".srt"):
                    from core.utils import clean_srt_to_text
                    transcript_text = clean_srt_to_text(raw)
                else:
                    transcript_text = raw

    with c_text:
        if source_mode == "直接貼入文字":
            video_title = st.text_input("輸入標題", "貼上文字的標題")
            transcript_text = st.text_area("貼入素材內容（如 FB 貼文或逐字稿）", height=200)
        else:
            if transcript_text:
                st.text_area("預覽內容", transcript_text, height=200, disabled=True)
                st.caption(f"字數：{len(transcript_text)} 字")

    st.markdown("---")
    
    # AI 模型選擇
    col_m, col_btn = st.columns([1, 2])
    with col_m:
        model_choice = st.selectbox("選擇 AI 模型", ["gpt-4o", "gemini"])
    
    with col_btn:
        st.write("") # push down
        if st.button("🚀 開始生成文案", type="primary", use_container_width=True, disabled=not transcript_text):
            st.session_state.gen_started = True

    if getattr(st.session_state, "gen_started", False) and transcript_text:
        st.markdown("### 📝 生成結果")
        result_box = st.empty()
        full_result = ""
        
        try:
            for chunk in generate_sor_stream(
                video_title, transcript_text, 
                model_name=model_choice, 
                custom_prompt=default_p.get("template") if default_p else None
            ):
                full_result += chunk
                result_box.markdown(f'<div class="tab-content" style="white-space: pre-wrap;">{full_result}▌</div>', unsafe_allow_html=True)
            result_box.markdown(f'<div class="tab-content" style="white-space: pre-wrap;">{full_result}</div>', unsafe_allow_html=True)
            
            # 儲存策略文檔以供 Step 3 使用
            from core.config import SOURCE_DIR
            out_file = f"{video_title}_strategy.txt"
            out_path = os.path.join(SOURCE_DIR, out_file)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(full_result)
            
            st.success(f"✅ 生成完成！已自動儲存為 `{out_file}`。您現在可以前往【🚀 Step 3 行銷素材】套用排版格式了！")
            
        except Exception as e:
            st.error(f"❌ 生成失敗：{e}")
        
        st.session_state.gen_started = False

# ─────────────────────────────────────────────────────────────────────────────
# Tab 2：知識庫生成 (舊版)
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("#### 📄 選擇或上傳逐字稿")

    source_mode = st.radio("來源方式", ["從已採收的檔案選取", "直接貼入文字", "上傳 .txt 檔案"], horizontal=True)

    transcript_text = ""

    if source_mode == "從已採收的檔案選取":
        try:
            from config import SOURCE_DIR
            txt_files = sorted(glob.glob(os.path.join(SOURCE_DIR, "*.txt")) +
                               glob.glob(os.path.join(SOURCE_DIR, "*.srt")))
            if txt_files:
                selected = st.selectbox("選擇檔案", [os.path.basename(f) for f in txt_files])
                full_path = os.path.join(SOURCE_DIR, selected)
                with open(full_path, "r", encoding="utf-8") as f:
                    raw = f.read()
                if selected.endswith(".srt"):
                    from utils import clean_srt_to_text
                    transcript_text = clean_srt_to_text(raw)
                else:
                    transcript_text = raw
                st.caption(f"📄 字數：{len(transcript_text):,} 字")
            else:
                st.info("尚無採收的檔案，請先至「YouTube 採收」頁面採收影片")
        except Exception as e:
            st.error(f"❌ 無法讀取資料夾：{e}")

    elif source_mode == "直接貼入文字":
        transcript_text = st.text_area("貼入逐字稿內容", height=200,
                                        placeholder="直接貼入逐字稿文字...")
        if transcript_text:
            st.caption(f"📄 字數：{len(transcript_text):,} 字")

    else:  # 上傳檔案
        uploaded = st.file_uploader("上傳 .txt 或 .srt 檔案", type=["txt", "srt"])
        if uploaded:
            raw = uploaded.read().decode("utf-8")
            if uploaded.name.endswith(".srt"):
                from utils import clean_srt_to_text
                transcript_text = clean_srt_to_text(raw)
            else:
                transcript_text = raw
            st.caption(f"✅ 已上傳 `{uploaded.name}`，字數：{len(transcript_text):,} 字")

    st.markdown("---")

    col_out, col_opt = st.columns([3, 1])
    with col_opt:
        output_filename = st.text_input("輸出檔名", value="knowledge_base.txt")

    if st.button("🏗️ 開始拆解生成知識庫", type="primary", use_container_width=True,
                 disabled=(not transcript_text)):
        if len(transcript_text.strip()) < 100:
            st.warning("⚠️ 文字內容太短，請提供完整逐字稿")
        else:
            with st.spinner("🏗️ 建築師分析結構中..."):
                try:
                    from content_refinery import analyze_structure, generate_concept_detail

                    structure = analyze_structure(transcript_text)
                    if not structure or "concepts" not in structure:
                        st.error("❌ 結構分析失敗，請確認 OpenAI API Key 已設定")
                    else:
                        concepts = structure["concepts"]
                        st.success(f"✅ 識別出 **{len(concepts)}** 個核心觀念")

                        # 顯示觀念列表
                        st.markdown("**📊 觀念架構**")
                        for c in concepts:
                            st.markdown(f'<span class="concept-chip">💡 {c["title"]}</span>',
                                        unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)

                        # 逐觀念生成
                        results = []
                        progress = st.progress(0, text="生成知識庫中...")
                        for idx, concept in enumerate(concepts):
                            with st.spinner(f"🔨 施工觀念 {idx+1}/{len(concepts)}：{concept['title']}"):
                                result = generate_concept_detail(
                                    transcript_text, concept["title"], concept["summary"], idx + 1
                                )
                                if result:
                                    results.append(result)
                                    with st.expander(f"✅ 觀念 {idx+1}：{concept['title']}", expanded=False):
                                        st.markdown(result)
                            progress.progress((idx + 1) / len(concepts),
                                              text=f"進度：{idx+1}/{len(concepts)}")

                        # 儲存
                        if results:
                            from config import SOURCE_DIR
                            out_path = os.path.join(SOURCE_DIR, output_filename)
                            with open(out_path, "a", encoding="utf-8") as f:
                                f.write("\n\n".join(results))
                                f.write("\n" + "=" * 50 + "\n")
                            st.success(f"💾 已儲存 {len(results)} 個觀念至 `{output_filename}`")

                            # 提供下載
                            full_content = "\n\n".join(results)
                            st.download_button(
                                "⬇️ 下載知識庫", full_content,
                                file_name=output_filename, mime="text/plain"
                            )
                except ImportError as e:
                    st.error(f"❌ 載入失敗：{e}（請確認 OPENAI_API_KEY 已設定）")
                except Exception as e:
                    st.error(f"❌ 執行失敗：{e}")

# ─────────────────────────────────────────────────────────────────────────────
# Tab 2：互動式文案修改
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("#### ✏️ 互動式文案修改工具")
    st.info("💡 貼入逐字稿，告訴 AI 你想要什麼風格改變，AI 會幫你優化指令然後重寫文案。")

    mod_col1, mod_col2 = st.columns([2, 1])

    with mod_col1:
        mod_transcript = st.text_area(
            "📄 原始逐字稿或文案",
            height=200,
            placeholder="貼入逐字稿或原始文案..."
        )

    with mod_col2:
        mod_instruction = st.text_area(
            "💡 修改指令（導演模式）",
            height=120,
            placeholder="例如：改得更口語、加入更多家長痛點、縮短到200字..."
        )
        use_ai_optimizer = st.toggle("AI 優化指令", value=True,
                                      help="讓 AI 幫你把模糊的指令轉化為精確的生成規範")

    if st.button("✨ 重寫文案", type="primary", disabled=(not mod_transcript or not mod_instruction)):
        with st.spinner("✨ AI 重寫中..."):
            try:
                # 動態 import modifier 的函式
                modifier_path = os.path.join(os.path.dirname(__file__), "..", "modifier.py")
                import importlib.util
                spec = importlib.util.spec_from_file_location("modifier", modifier_path)
                mod = importlib.util.load_from_spec(spec)
                spec.loader.exec_module(mod)

                instruction = mod_instruction
                if use_ai_optimizer:
                    with st.spinner("✨ 優化指令中..."):
                        instruction = mod.optimize_instruction(mod_instruction)
                    st.markdown(f"**👉 優化後指令：** {instruction}")

                result = mod.rewrite_article(mod_transcript, instruction)
                if result:
                    st.markdown("---")
                    st.markdown("**📝 重寫結果**")
                    st.markdown(result)
                    st.download_button("⬇️ 下載文案", result,
                                       file_name="rewritten_article.txt", mime="text/plain")
                else:
                    st.error("❌ 重寫失敗")
            except Exception as e:
                st.error(f"❌ 執行失敗：{e}")
                st.info("💡 請確認 `OPENAI_API_KEY` 已設定在 `.env` 檔案中")
