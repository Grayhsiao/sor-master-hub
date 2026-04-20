<?php
$db = new PDO("sqlite:/Users/gray/Sites/junior_high_king/quiz.db");

// 搜尋包含數學特徵（x, y, z, =, {）且 A 選項看起來是空的題目
$sql = "SELECT id, question, option_a, options, explanation FROM questions 
        WHERE (question LIKE '%x%' OR question LIKE '%y%' OR question LIKE '%=%' OR question LIKE '%{%')
        AND (option_a = '' OR option_a IS NULL OR option_a = '無內容')
        LIMIT 20";

$rows = $db->query($sql)->fetchAll(PDO::FETCH_ASSOC);

if (!$rows) {
    echo "✅ 找不到『無內容』的數學題。這代表問題可能在前端顯示，或題目在別張表。\n";
} else {
    echo "--- 🚨 發現以下數學題『選項缺失』 ---\n";
    foreach ($rows as $r) {
        echo "【ID】: " . $r['id'] . "\n";
        echo "【題幹】: " . mb_substr(strip_tags($r['question']), 0, 50) . "...\n";
        echo "【A 欄位】: [" . $r['option_a'] . "]\n";
        echo "【Options JSON】: " . $r['options'] . "\n";
        echo "【解析是否有內容】: " . (empty($r['explanation']) ? "❌ 否" : "✅ 是") . "\n";
        echo "------------------------------------------\n";
    }
}
