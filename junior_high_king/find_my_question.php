<?php
$db = new PDO("sqlite:/Users/gray/Sites/junior_high_king/quiz.db");

// 1. 先列出所有資料表，看看有沒有我們不知道的表
$tables = $db->query("SELECT name FROM sqlite_master WHERE type='table'")->fetchAll(PDO::FETCH_COLUMN);
echo "--- 📊 目前資料庫中的資料表: " . implode(", ", $tables) . " ---\n\n";

// 2. 在每個資料表裡搜尋這題
$search_keyword = "x+y="; // 用更短、更穩的關鍵字搜尋

foreach ($tables as $table) {
    // 先檢查這個表有沒有 question 欄位
    $cols = $db->query("PRAGMA table_info($table)")->fetchAll(PDO::FETCH_COLUMN, 1);
    if (!in_array('question', $cols)) continue;

    $stmt = $db->prepare("SELECT * FROM $table WHERE question LIKE ? LIMIT 1");
    $stmt->execute(["%$search_keyword%"]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($row) {
        echo "🎯 在資料表 [$table] 找到了！\n";
        echo "ID: " . $row['id'] . "\n";
        echo "題幹: " . $row['question'] . "\n";
        echo "A欄位: [" . ($row['option_a'] ?? '無此欄位') . "]\n";
        echo "Options欄位: " . ($row['options'] ?? '無此欄位') . "\n";
        echo "------------------------------------------\n";
        exit;
    }
}
echo "❌ 即使翻遍全表，還是找不到包含 '$search_keyword' 的題目。\n";
