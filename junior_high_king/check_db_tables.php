<?php
$dbs = [
    "OpenClaw版" => "/Users/gray/openclaw/quiz.db",
    "網頁執行版" => "/Users/gray/Sites/junior_high_king/quiz.db",
    "桌面備份版" => "/Users/gray/Desktop/openclaw_backup/full_dot_openclaw/workspace/quiz.db"
];

foreach ($dbs as $name => $path) {
    echo "🔎 檢查 $name ($path):\n";
    if (!file_exists($path)) { echo "   ❌ 檔案不存在。\n\n"; continue; }
    
    try {
        $db = new PDO("sqlite:$path");
        // 抓出所有資料表名稱
        $tables = $db->query("SELECT name FROM sqlite_master WHERE type='table'")->fetchAll(PDO::FETCH_COLUMN);
        echo "   📊 包含資料表: " . (empty($tables) ? "【完全空白】" : implode(", ", $tables)) . "\n";
        
        // 如果有 questions 表，順便看看有沒有阿鳳
        if (in_array('questions', $tables)) {
            $r = $db->query("SELECT count(*) FROM questions WHERE question LIKE '%阿鳳%'")->fetchColumn();
            echo "   📝 發現『阿鳳』題數: $r\n";
        }
    } catch (Exception $e) {
        echo "   💥 錯誤: " . $e->getMessage() . "\n";
    }
    echo "------------------------------------------\n";
}
