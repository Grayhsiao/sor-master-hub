import os
import time
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 設定目錄與過期時間 (預設 24 小時)
STATIC_DIR = "static"
EXPIRATION_SECONDS = 24 * 60 * 60 

def cleanup_static_files():
    """
    掃描 static 資料夾，刪除超過 24 小時的 mp3 檔案
    """
    if not os.path.exists(STATIC_DIR):
        logger.info(f"Directory {STATIC_DIR} does not exist. Skipping cleanup.")
        return

    now = time.time()
    deleted_count = 0
    total_size = 0

    for filename in os.listdir(STATIC_DIR):
        if filename.endswith(".mp3"):
            file_path = os.path.join(STATIC_DIR, filename)
            try:
                # 取得檔案最後修改時間
                file_age = os.path.getmtime(file_path)
                if now - file_age > EXPIRATION_SECONDS:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted_count += 1
                    total_size += file_size
                    logger.info(f"Deleted expired file: {filename}")
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")

    if deleted_count > 0:
        logger.info(f"Cleanup complete. Deleted {deleted_count} files (Total: {total_size / 1024 / 1024:.2f} MB).")
    else:
        logger.info("No expired files found. Cleanup skipped.")

if __name__ == "__main__":
    cleanup_static_files()
