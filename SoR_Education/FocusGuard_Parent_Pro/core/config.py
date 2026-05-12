import os
import sys
import platform
from dotenv import load_dotenv

# --- 基礎配置 ---
def resource_path(relative_path):
    """ 獲取資源絕對路徑，兼容開發環境與 PyInstaller 打包環境 """
    try:
        base_path = sys._MEIPASS
    except Exception:
        # In this project, app.py was in the root, so __file__ of config.py is in core/
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

BASE_DIR = resource_path(".")
ANTI_HOVER_EXT_PATH = resource_path("anti_hover_ext")

# 嘗試多個路徑載入 .env
possible_env_paths = [
    resource_path("../../.env"),
    resource_path("../../../.env"),
    resource_path(".env"),
    os.path.expanduser("~/Documents/python_project/.env")
]
for p in possible_env_paths:
    if os.path.exists(p):
        load_dotenv(p)
        break
else:
    load_dotenv(os.path.join(BASE_DIR, ".env"))

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# 雲端伺服器位址 (正式版)
SERVER_URL = "https://sor14.duckdns.org/focus_pro"

IS_MAC = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"

CONFIG_FILE = os.path.join(BASE_DIR, "focus_guard_config.json")

# 執法名單 (從 app.py 搬過來的)
HARD_BLACKLIST = [
    "roblox", "minecraft", "steam", "genshin", "shorts", "reels", "tiktok", "netflix",
    "gameplay", "walkthrough", "speedrun", "esports", "league of legends", "valorant", 
    "apex", "pubg", "fortnite", "gta", "grand theft auto", "cyberpunk", "witcher", 
    "zelda", "mario", "pokemon", "pewdiepie", "mrbeast gaming", "markiplier", "ninja", 
    "shroud", "faker", "統神", "國動", "丁特", "史丹利", "toyz", "阿神", "老高", 
    "實況", "精華", "遊戲", "電競", "打機", "攻略", "抽卡", "上分", "lol", 
    "games", "gaming", "azagames", "動畫", "卡通", "comic", "manga", "anime", "劇集", "電影",
    "人生肥宅x尊", "loserzun", "人生肥宅"
]

# 學習白名單：只要標題包含這些字，系統就會優先放行（前提是沒有觸發黑名單）
HARD_WHITELIST = [
    "蕭博士", "sor", "自然", "生物", "歷史", "地理", "物理", "化學", "數學", 
    "國文", "英文", "理化", "地科", "公民", "社會", "科學", "教學", "課程", 
    "補習", "會考", "學測", "指考", "統測", "多益", "toeic", "托福", "toefl",
    "雅思", "ielts", "科普", "紀錄片", "documentary", "實驗", "experiment",
    "線上課程", "講義", "解題", "複習", "段考", "期中考", "期末考", "education",
    "learning", "tutorial", "study"
]
