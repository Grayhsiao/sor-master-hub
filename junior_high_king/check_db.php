<?php
header('Content-Type: text/html; charset=utf-8');
try {
    $db = new PDO("sqlite:quiz.db");
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    echo "<h2>🔍 資料庫完整結構掃描</h2>";

    // 1. 檢查表格所有欄位名稱
    echo "<h3>📋 資料表欄位清單：</h3>";
    $columns = $db->query("PRAGMA table_info(questions)")->fetchAll(PDO::FETCH_ASSOC);
    echo "<ul>";
    foreach ($columns as $col) {
        echo "<li><b>{$col['name']}</b> ({$col['type']})</li>";
    }
    echo "</ul>";

    // 2. 抽樣顯示一筆資料（看看解析翻譯進去了沒）
    echo "<h3>示範資料（英文題）：</h3>";
    $sample = $db->query("SELECT * FROM questions WHERE subject='英文' AND analysis LIKE '%中文翻譯%' LIMIT 1")->fetch(PDO::FETCH_ASSOC);
    
    if ($sample) {
        echo "<table border='1' cellpadding='10' style='border-collapse:collapse; width:100%;'>";
        foreach ($sample as $key => $val) {
            echo "<tr><td style='background:#eee; width:150px;'>$key</td><td>" . nl2br(htmlspecialchars($val)) . "</td></tr>";
        }
        echo "</table>";
    } else {
        echo "<p style='color:red;'>找不到含有中文翻譯的英文題，請確認翻譯腳本是否執行成功。</p>";
    }

} catch (Exception $e) {
    echo "錯誤：" . $e->getMessage();
}
?>