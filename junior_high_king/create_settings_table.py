import sqlite3

def create_system_settings_table(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 建立 system_settings 資料表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_name TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL
            )
        ''')

        # 插入預設參數，如果不存在的話
        settings = {
            "total_questions": "20",
            "voice_timeout": "5",
            "mc_timeout": "15" # Multiple choice timeout
        }

        for name, value in settings.items():
            cursor.execute('INSERT OR IGNORE INTO system_settings (setting_name, setting_value) VALUES (?, ?)', (name, value))
        
        conn.commit()
        print("System settings table created and default parameters inserted successfully.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    db_file_path = "/Users/gray/Sites/junior_high_king/quiz.db"
    create_system_settings_table(db_file_path)
