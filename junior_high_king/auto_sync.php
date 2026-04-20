<?php
try {
    $db = new PDO('sqlite:quiz.db');
    // 🚩 核心：自動抓取資料庫裡所有的資料表名稱
    $tables = $db->query("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")->fetchAll(PDO::FETCH_COLUMN);

    echo "<h2>🔍 題庫自動偵測報告</h2>";

    if (empty($tables)) {
        die("<p style='color:red;'>❌ 錯誤：quiz.db 是空的，裡面沒有任何資料表！</p>");
    }

    foreach ($tables as $tableName) {
        echo "<div style='background:#eee; padding:15px; margin-bottom:20px; border-radius:10px;'>";
        echo "<h3>📍 找到資料表：<span style='color:blue;'>$tableName</span></h3>";

        // 抓取這個表裡面的科目
        $cols = $db->query("PRAGMA table_info($tableName)")->fetchAll(PDO::FETCH_ASSOC);
        $colNames = array_column($cols, 'name');

        echo "<b>欄位清單：</b> " . implode(', ', $colNames) . "<br><br>";

        // 嘗試分析有哪些科目
        if (in_array('subject', $colNames)) {
            $subjects = $db->query("SELECT subject, COUNT(*) as count FROM $tableName GROUP BY subject")->fetchAll(PDO::FETCH_ASSOC);
            echo "<b>偵測到科目：</b><br><ul>";
            foreach ($subjects as $s) {
                echo "<li>{$s['subject']} ({$s['count']} 題)</li>";
            }
            echo "</ul>";
        } else {
            echo "<p style='color:orange;'>⚠️ 此表沒有 'subject' 欄位，請確認科目資訊存在哪個欄位。</p>";
        }
        echo "</div>";
    }
} catch (Exception $e) {
    echo "❌ 連線失敗：" . $e->getMessage();
}
?>