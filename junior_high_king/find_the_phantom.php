<?php
$db = new PDO("sqlite:/Users/gray/Sites/junior_high_king/quiz.db");
$tables = ['questions', 'questions_non_mcq', 'questions_with_images', 'questions_pending_images'];

// 這次我們用解析裡的關鍵數據去搜，因為那是 AI 算出來的
$search_analysis = '%x=2%y=3%'; 

foreach ($tables as $table) {
    echo "🔍 正在檢查資料表: [$table]...\n";
    
    // 檢查有沒有 analysis 欄位
    $cols = $db->query("PRAGMA table_info($table)")->fetchAll(PDO::FETCH_COLUMN, 1);
    $target_col = in_array('analysis', $cols) ? 'analysis' : (in_array('options', $cols) ? 'options' : 'question');

    $stmt = $db->prepare("SELECT * FROM $table WHERE $target_col LIKE ? OR question LIKE '%2x%3y%' LIMIT 1");
    $stmt->execute([$search_analysis]);
    $r = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($r) {
        echo "\n🎯 【抓到了！】 躲在資料表: [$table]\n";
        echo "ID: " . $r['id'] . "\n";
        echo "題幹: " . $r['question'] . "\n";
        echo "A 欄位: [" . ($r['option_a'] ?? '無此欄位') . "]\n";
        echo "Options: " . ($r['options'] ?? '無資料') . "\n";
        echo "解析: " . mb_substr($r['analysis'] ?? $r['options'], 0, 50) . "...\n";
        echo "------------------------------------------\n";
        exit;
    }
}
echo "❌ 依然全軍覆沒。老闆，請執行 ls -l /Users/gray/Sites/junior_high_king/quiz.db 看看檔案最後修改時間，會不會我們改錯檔案了？\n";
