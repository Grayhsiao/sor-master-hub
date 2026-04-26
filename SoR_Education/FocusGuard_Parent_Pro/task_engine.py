"""
SoR Task Engine (task_engine.py)
=================================
管理所有學習任務、代幣計算與錯題本。
功能：
  - 今日任務生成 / 讀取
  - 代幣增減 (Thread-Safe)
  - 解鎖時間管理
  - 錯題本 (weak_points.json) 讀寫
  - 作答歷史記錄
"""

import os
import json
import time
import threading
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.expanduser("~/sor_tutor_data")
os.makedirs(DATA_DIR, exist_ok=True)

TASKS_FILE       = os.path.join(DATA_DIR, "daily_tasks.json")
STATE_FILE       = os.path.join(DATA_DIR, "focus_state.json")
WEAK_POINTS_FILE = os.path.join(DATA_DIR, "weak_points.json")
HISTORY_FILE     = os.path.join(DATA_DIR, "answer_history.json")

# 每枚代幣換多少分鐘
TOKEN_MINUTES = 30


# ── 工具函數 ───────────────────────────────────────────────────────────────────

def _load_json(path: str, default) -> dict | list:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def _save_json(path: str, data) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[TaskEngine] 儲存失敗 {path}: {e}")


def _today() -> str:
    return date.today().isoformat()


# ── 狀態管理 (Thread-Safe) ────────────────────────────────────────────────────

class FocusState:
    """
    管理全域專注狀態，線程安全。
    狀態儲存在 ~/sor_tutor_data/focus_state.json
    """
    _lock = threading.Lock()

    @classmethod
    def load(cls) -> dict:
        default = {
            "tokens": 0,
            "unlock_until": 0,   # Unix timestamp，0 表示未解鎖
            "is_monitoring": True,
            "last_updated": ""
        }
        return _load_json(STATE_FILE, default)

    @classmethod
    def save(cls, state: dict) -> None:
        state["last_updated"] = datetime.now().isoformat()
        _save_json(STATE_FILE, state)

    @classmethod
    def add_tokens(cls, count: int = 1, reason: str = "") -> dict:
        """增加代幣，回傳最新狀態。"""
        with cls._lock:
            state = cls.load()
            state["tokens"] = max(0, state["tokens"] + count)
            cls.save(state)
            # 記錄代幣歷史
            _append_token_log(count, reason, state["tokens"])
            print(f"[TaskEngine] +{count} 代幣（{reason}），目前：{state['tokens']} 枚")
            return state

    @classmethod
    def redeem_token(cls) -> dict:
        """
        消耗 1 枚代幣，解鎖 TOKEN_MINUTES 分鐘。
        如果已在解鎖期間，則延長時間。
        回傳 {"ok": bool, "unlock_until": int, "tokens_left": int, "message": str}
        """
        with cls._lock:
            state = cls.load()
            if state["tokens"] <= 0:
                return {
                    "ok": False,
                    "unlock_until": state["unlock_until"],
                    "tokens_left": 0,
                    "message": "代幣不足！請先完成今日作業或練習。"
                }
            
            state["tokens"] -= 1
            now = time.time()
            # 如果已在解鎖期，從「現在」或「當前截止」兩者較大值開始延長
            current_unlock = max(state["unlock_until"], now)
            state["unlock_until"] = current_unlock + TOKEN_MINUTES * 60
            cls.save(state)
            
            unlock_dt = datetime.fromtimestamp(state["unlock_until"])
            _append_token_log(-1, "兌換娛樂時間", state["tokens"])
            
            return {
                "ok": True,
                "unlock_until": state["unlock_until"],
                "tokens_left": state["tokens"],
                "message": f"✅ 解鎖成功！自由使用至 {unlock_dt.strftime('%H:%M')}（剩餘 {state['tokens']} 枚代幣）"
            }

    @classmethod
    def get_unlock_status(cls) -> dict:
        """
        回傳當前解鎖狀態。
        {"is_unlocked": bool, "seconds_remaining": int, "tokens": int}
        """
        state = cls.load()
        now = time.time()
        unlock_until = state.get("unlock_until", 0)
        
        if unlock_until > now:
            remaining = int(unlock_until - now)
            return {
                "is_unlocked": True,
                "seconds_remaining": remaining,
                "minutes_remaining": remaining // 60,
                "unlock_until": unlock_until,
                "tokens": state["tokens"]
            }
        else:
            # 解鎖時間已到，確保狀態清零
            if state.get("unlock_until", 0) != 0 and unlock_until <= now:
                with cls._lock:
                    state["unlock_until"] = 0
                    cls.save(state)
            return {
                "is_unlocked": False,
                "seconds_remaining": 0,
                "minutes_remaining": 0,
                "unlock_until": 0,
                "tokens": state["tokens"]
            }


def _append_token_log(delta: int, reason: str, current_total: int):
    """記錄代幣異動歷史。"""
    log_file = os.path.join(DATA_DIR, "token_log.json")
    logs = _load_json(log_file, [])
    logs.append({
        "time": datetime.now().isoformat(),
        "delta": delta,
        "reason": reason,
        "total": current_total
    })
    logs = logs[-200:]  # 保留最近 200 筆
    _save_json(log_file, logs)


# ── 每日任務管理 ───────────────────────────────────────────────────────────────

class DailyTaskManager:
    """
    管理今日任務列表與完成狀態。
    任務資料儲存在 ~/sor_tutor_data/daily_tasks.json
    """

    @classmethod
    def get_today_tasks(cls) -> dict:
        """取得今日任務，如果是新的一天則自動重置。"""
        data = _load_json(TASKS_FILE, {})
        today = _today()
        
        if data.get("date") != today:
            # 新的一天，重置任務
            data = cls._create_default_tasks(today)
            _save_json(TASKS_FILE, data)
        
        return data

    @classmethod
    def _create_default_tasks(cls, today: str) -> dict:
        """建立預設的每日任務結構。"""
        return {
            "date": today,
            "tasks": {
                "homework": {
                    "id": "homework",
                    "title": "AI 智慧作業",
                    "description": "完成今日 AI 出的練習題（由家長設定科目）",
                    "icon": "📚",
                    "token_reward": 1,
                    "status": "pending",      # pending / in_progress / completed
                    "required": True,
                    "subject_key": "",        # 由家長設定
                    "questions": [],          # 由 generate_questions() 填充
                    "answers": [],            # 學生作答記錄
                    "score": 0,
                },
                "piano": {
                    "id": "piano",
                    "title": "鋼琴練習",
                    "description": f"有效練習 30 分鐘",
                    "icon": "🎹",
                    "token_reward": 1,
                    "status": "pending",
                    "required": False,
                    "target_minutes": 30,
                    "accumulated_seconds": 0,
                },
                "reading": {
                    "id": "reading",
                    "title": "自主閱讀",
                    "description": "閱讀 20 分鐘（可選）",
                    "icon": "📖",
                    "token_reward": 1,
                    "status": "pending",
                    "required": False,
                    "target_minutes": 20,
                    "accumulated_seconds": 0,
                }
            },
            "total_tokens_earned_today": 0
        }

    @classmethod
    def set_homework_config(cls, subject_key: str, questions: list, difficulty: int = 1) -> bool:
        """家長設定今日作業（科目 + 題目）。"""
        data = cls.get_today_tasks()
        data["tasks"]["homework"]["subject_key"] = subject_key
        data["tasks"]["homework"]["difficulty"] = difficulty
        data["tasks"]["homework"]["questions"] = questions
        data["tasks"]["homework"]["status"] = "pending"
        data["tasks"]["homework"]["answers"] = []
        data["tasks"]["homework"]["score"] = 0
        _save_json(TASKS_FILE, data)
        return True

    @classmethod
    def submit_answer(cls, task_id: str, question_id: int, grade_result: dict) -> dict:
        """
        記錄學生的作答結果。
        
        Args:
            task_id: "homework"
            question_id: 題目序號
            grade_result: grade_answer() 回傳的批改結果

        Returns:
            {"task_completed": bool, "tokens_earned": int, "homework_score": float}
        """
        data = cls.get_today_tasks()
        task = data["tasks"].get(task_id)
        if not task:
            return {"error": f"找不到任務 {task_id}"}
        
        # 更新作答記錄
        answers = task.get("answers", [])
        # 找到同題號的最新作答
        existing = next((a for a in answers if a["question_id"] == question_id), None)
        
        answer_record = {
            "question_id": question_id,
            "is_correct": grade_result.get("is_correct", False),
            "score": grade_result.get("score", 0),
            "attempt_count": grade_result.get("attempt_count", 1),
            "error_step": grade_result.get("error_step", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        if existing:
            # 更新已有的記錄
            idx = answers.index(existing)
            answers[idx] = answer_record
        else:
            answers.append(answer_record)
        
        task["answers"] = answers
        task["status"] = "in_progress"
        
        # 計算整體分數
        questions = task.get("questions", [])
        if questions:
            completed_count = len(answers)
            correct_count = sum(1 for a in answers if a["is_correct"])
            task["score"] = round(correct_count / len(questions) * 100)
            
            # 判斷是否完成（所有題目都已作答）
            all_answered = len({a["question_id"] for a in answers}) >= len(questions)
            if all_answered:
                task["status"] = "completed"
        
        _save_json(TASKS_FILE, data)
        
        # 如果任務完成且達到及格標準（≥60分），給予代幣
        tokens_earned = 0
        task_completed = task["status"] == "completed"
        
        if task_completed and task["score"] >= 60 and task.get("token_given") != True:
            token_reward = task["token_reward"]
            FocusState.add_tokens(
                token_reward,
                f"完成{task['title']}（得分：{task['score']}分）"
            )
            tokens_earned = token_reward
            data = cls.get_today_tasks()  # 重新載入避免覆蓋
            data["tasks"][task_id]["token_given"] = True
            data["total_tokens_earned_today"] = data.get("total_tokens_earned_today", 0) + tokens_earned
            _save_json(TASKS_FILE, data)
        
        return {
            "task_completed": task_completed,
            "tokens_earned": tokens_earned,
            "homework_score": task["score"],
            "answers_count": len(answers),
            "questions_count": len(questions)
        }

    @classmethod
    def complete_timed_task(cls, task_id: str) -> dict:
        """標記計時任務（鋼琴/閱讀）為完成，給予代幣。"""
        data = cls.get_today_tasks()
        task = data["tasks"].get(task_id)
        if not task:
            return {"error": f"找不到任務 {task_id}"}
        
        if task.get("status") == "completed":
            return {"error": "任務已完成", "tokens_earned": 0}
        
        task["status"] = "completed"
        tokens_earned = 0
        
        if not task.get("token_given"):
            token_reward = task["token_reward"]
            FocusState.add_tokens(token_reward, f"完成{task['title']}")
            tokens_earned = token_reward
            task["token_given"] = True
            data["total_tokens_earned_today"] = data.get("total_tokens_earned_today", 0) + tokens_earned
        
        _save_json(TASKS_FILE, data)
        return {"ok": True, "tokens_earned": tokens_earned, "task": task}

    @classmethod
    def update_piano_time(cls, seconds: int) -> dict:
        """更新鋼琴練習累計時間。"""
        data = cls.get_today_tasks()
        task = data["tasks"]["piano"]
        
        if task["status"] == "completed":
            return {"already_completed": True}
        
        task["accumulated_seconds"] = task.get("accumulated_seconds", 0) + seconds
        target_seconds = task["target_minutes"] * 60
        
        if task["accumulated_seconds"] >= target_seconds:
            _save_json(TASKS_FILE, data)
            return cls.complete_timed_task("piano")
        
        task["status"] = "in_progress"
        _save_json(TASKS_FILE, data)
        
        return {
            "accumulated_seconds": task["accumulated_seconds"],
            "target_seconds": target_seconds,
            "progress_percent": min(100, round(task["accumulated_seconds"] / target_seconds * 100))
        }


# ── 錯題本 ─────────────────────────────────────────────────────────────────────

class WeakPointsManager:
    """管理學生的錯題本與弱點知識點。"""

    @classmethod
    def add_wrong_answer(cls, topic: str, question: str, error_step: str, subject_key: str = "") -> None:
        """將答錯的題目加入錯題本。"""
        data = _load_json(WEAK_POINTS_FILE, {"topics": {}, "history": []})
        
        # 更新主題錯誤次數
        if topic not in data["topics"]:
            data["topics"][topic] = {"count": 0, "errors": []}
        data["topics"][topic]["count"] += 1
        data["topics"][topic]["errors"].append({
            "error": error_step[:50],
            "time": _today()
        })
        # 每個主題只保留最近 5 筆錯誤
        data["topics"][topic]["errors"] = data["topics"][topic]["errors"][-5:]
        
        # 加入歷史記錄
        data["history"].append({
            "date": _today(),
            "topic": topic,
            "question_preview": question[:50],
            "error_step": error_step[:100],
            "subject_key": subject_key
        })
        data["history"] = data["history"][-100:]  # 保留最近 100 筆
        
        _save_json(WEAK_POINTS_FILE, data)

    @classmethod
    def get_weak_topics(cls, top_n: int = 5) -> list[str]:
        """取得錯誤次數最多的 top_n 個主題。"""
        data = _load_json(WEAK_POINTS_FILE, {"topics": {}})
        topics = data.get("topics", {})
        
        sorted_topics = sorted(topics.items(), key=lambda x: x[1]["count"], reverse=True)
        
        result = []
        for topic, info in sorted_topics[:top_n]:
            latest_error = info["errors"][-1]["error"] if info["errors"] else ""
            if latest_error:
                result.append(f"{topic}（常見錯誤：{latest_error}）")
            else:
                result.append(topic)
        
        return result

    @classmethod
    def get_all_weak_points(cls) -> dict:
        """取得完整錯題本資料（供家長端顯示）。"""
        return _load_json(WEAK_POINTS_FILE, {"topics": {}, "history": []})


# ── 測試 ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== 測試 TaskEngine ===\n")
    
    print("📋 取得今日任務...")
    tasks = DailyTaskManager.get_today_tasks()
    print(f"   日期：{tasks['date']}")
    for tid, t in tasks["tasks"].items():
        print(f"   {t['icon']} {t['title']} — 狀態：{t['status']}")
    
    print("\n💰 測試代幣系統...")
    state = FocusState.add_tokens(2, "測試")
    print(f"   目前代幣：{state['tokens']} 枚")
    
    result = FocusState.redeem_token()
    print(f"   兌換結果：{result['message']}")
    
    status = FocusState.get_unlock_status()
    print(f"   解鎖狀態：{'已解鎖' if status['is_unlocked'] else '未解鎖'}")
    if status['is_unlocked']:
        print(f"   剩餘時間：{status['minutes_remaining']} 分鐘")
    
    print("\n📚 測試錯題本...")
    WeakPointsManager.add_wrong_answer(
        topic="一元一次方程式",
        question="解方程式：2x + 3 = 13",
        error_step="移項時符號錯誤",
        subject_key="math_7"
    )
    weak_topics = WeakPointsManager.get_weak_topics()
    print(f"   弱點主題：{weak_topics}")
    
    print("\n✅ TaskEngine 測試完成！資料儲存於：", DATA_DIR)
