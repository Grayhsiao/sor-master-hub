<?php
$db_path = "/Users/gray/Sites/junior_high_king/quiz.db";
$db = new PDO("sqlite:$db_path");
$tables = ['questions', 'questions_non_mcq', 'imported_json', 'questions_with_images'];

echo "--- 🕵️ 正在網頁資料庫搜尋『阿鳳』的蹤跡 ---\n";

foreach ($tables as $table) {
    // 檢查表是否存在
    $check = $db->query("SELECT name FROM sqlite_master WHERE type='table' AND name='$table'")->fetch();
    if (!$check) continue;

    // 模糊搜尋整個內容
    $sql = "SELECT id, question FROM $table WHERE (question LIKE '%阿鳳%' OR question LIKE '%媽媽%') LIMIT 1";
    $r = $db->query($sql)->fetch(PDO::FETCH_ASSOC);

    if ($r) {
        echo "🎯 抓到了！躲在資料表 【$table】 | ID: " . $r['id'] . "\n";
        echo "題幹內容: " . mb_substr($r['question'], 0, 50) . "...\n";
        
        // 如果在非選擇題表，看看有沒有解析
        $cols = $db->query("PRAGMA table_info($table)")->fetchAll(PDO::FETCH_COLUMN, 1);
        if (in_array('analysis', $cols)) {
            echo "💡 此表包含 analysis 欄位。\n";
        }
        exit;
    }
}
echo "❌ 依然全軍覆沒。網頁執行版資料庫裡『真的沒有』這題。\n";
echo "👉 這證明了 game.php 讀取的絕對不是 $db_path\n";
