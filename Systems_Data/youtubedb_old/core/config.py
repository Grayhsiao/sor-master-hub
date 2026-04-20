import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base Directory - Point to the root directory (parent of core/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Data Directory
DATA_DIR = BASE_DIR / "data"

# Directory Settings
DOWNLOAD_DIR = DATA_DIR / "downloaded_files"
SOURCE_DIR = DATA_DIR / "sources"
DB_PATH = DATA_DIR / "dr_hsiao_db"

# Files
INDEX_FILE = DATA_DIR / "videos.json"
# Legacy/Alternative DB File
DB_FILE = BASE_DIR / "archive" / "old_backups" / "sor_strategy_db.txt"

# Ensure directories exist
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
SOURCE_DIR.mkdir(parents=True, exist_ok=True)

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Embedding Model
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
CHROMA_COLLECTION_NAME = "dr_hsiao_knowledge"
