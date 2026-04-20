<?php
try {
    $db = new PDO('sqlite:education.db');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // 強制重設 (更新結構)
    $db->exec("DROP TABLE IF EXISTS users");
    $db->exec("DROP TABLE IF EXISTS study_logs");

    // 建立用戶表
    $db->exec("CREATE TABLE users (
        user_id TEXT PRIMARY KEY, 
        name TEXT, 
        pic TEXT, 
        login_type TEXT, 
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )");

    // 建立學習日誌表 (記錄每一題的生死)
    $db->exec("CREATE TABLE study_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        category TEXT,
        subject TEXT,
        is_correct BOOLEAN,
        response_time INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )");

    echo "<div style='text-align:center; padding:50px;'>";
    echo "<h1 style='color:green;'>✅ 資料庫初始化成功！</h1>";
    echo "<p>舊數據已清空，欄位已完全對齊。</p>";
    echo "<a href='index.php' style='padding:10px 20px; background:#6c5ce7; color:white; text-decoration:none; border-radius:10px;'>回大廳</a>";
    echo "</div>";
} catch (PDOException $e) {
    die("資料庫錯誤：" . $e->getMessage());
}