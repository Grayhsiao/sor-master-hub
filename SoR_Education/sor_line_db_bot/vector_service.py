import os
import json
import chromadb
import re
from sentence_transformers import SentenceTransformer

class VectorService:
    def __init__(self, db_path="./chroma_db", source_dir="knowledge_base", manifest_path="./chroma_manifest.json"):
        self.db_path = db_path
        self.source_dir = source_dir
        self.manifest_path = manifest_path
        
        # 初始化數據庫與模型
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.collection = self.client.get_or_create_collection(name="sor_knowledge")
        
        if not os.path.exists(self.source_dir):
            os.makedirs(self.source_dir)
            print(f"Created directory: {self.source_dir}")

        # 載入或是重置 Manifest
        self.manifest = self._load_manifest()

        # 啟動時自動掃描並更新
        self.refresh_database()

    def _load_manifest(self):
        """讀取檔案索引清單，避免重覆計算向量"""
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_manifest(self):
        """儲存目前的檔案異動狀態"""
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2)

    def _split_text(self, text):
        """依據 🌟 標記切割段落，若無標記則視為整篇"""
        if '🌟' not in text:
            return [text.strip()]
        sections = text.split('🌟')
        return [("🌟" + s).strip() for s in sections if s.strip()]

    def refresh_database(self):
        """掃描資料夾內所有 .txt 和 .md 檔案，僅更新異動的部分"""
        all_new_docs = []
        all_new_ids = []
        
        support_extensions = ('.txt', '.md')
        update_count = 0
        total_files = 0
        
        # 獲取當前所有的檔案列表
        for filename in os.listdir(self.source_dir):
            if filename.endswith(support_extensions):
                total_files += 1
                file_path = os.path.join(self.source_dir, filename)
                # 使用檔案最後修改時間作為判定基準
                mtime = os.path.getmtime(file_path)
                
                # 檢查 Manifest：如果檔案不在裡面，或者修改時間不同，則需要重讀
                if filename not in self.manifest or self.manifest[filename] != mtime:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        docs = self._split_text(content)
                        for i, doc in enumerate(docs):
                            # ID 格式：檔名_序號 (Upsert 會覆蓋舊 ID)
                            doc_id = f"{filename}_{i}"
                            all_new_docs.append(doc)
                            all_new_ids.append(doc_id)
                        
                        # 在 Manifest 中更新此檔案的時間戳
                        self.manifest[filename] = mtime
                        update_count += 1
                    except Exception as e:
                        print(f"Error reading {filename}: {e}")

        if all_new_docs:
            print(f"🔄 偵測到 {update_count} 個新/異動檔案。正在更新 {len(all_new_docs)} 個知識片段向量...")
            # 進行批量向量化
            embeddings = self.model.encode(all_new_docs).tolist()

            # 存入 ChromaDB (Upsert 邏輯會自動處理更新或新增)
            self.collection.upsert(
                documents=all_new_docs,
                ids=all_new_ids,
                embeddings=embeddings
            )
            self._save_manifest()
            print(f"✅ 增量更新完成，共處理 {len(all_new_docs)} 個片段。")
        else:
            print(f"💤 知識庫資料夾內 {total_files} 個檔案皆為最新狀態，跳過重新索引。")

    def query(self, user_query, top_k=2):
        """檢索最相關的段落，並回傳內容與來源 ID"""
        # 在 query 時也檢查術語修正
        from term_corrector import TermCorrector
        corrector = TermCorrector()
        user_query = corrector.correct(user_query)
        
        print(f"🔍 檢索中: {user_query}")
        query_embedding = self.model.encode([user_query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        
        documents = results['documents'][0]
        ids = results['ids'][0]
        
        # 整理來源標號 (例如從 fb_post_398.txt_0 提取出 398)
        sources = []
        for doc_id in ids:
            match = re.search(r'fb_post_(\d+)', doc_id)
            if match:
                sources.append(match.group(1))
            else:
                # 若非 fb 格式，則取檔名去掉 ID 部分
                base_name = doc_id.rsplit('_', 1)[0]
                sources.append(base_name)
        
        # 去重
        unique_sources = sorted(list(set(sources)))
        
        return "\n\n".join(documents), unique_sources

if __name__ == "__main__":
    # 測試代碼
    svc = VectorService()
    print("Testing query: 'PA 是什麼？'")
    content, src = svc.query("PA 是什麼？")
    print(f"Result (first 100 chars): {content[:100]}...")
    print(f"Sources: {src}")
