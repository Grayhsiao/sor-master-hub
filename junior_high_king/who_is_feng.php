<?php
$dbs = [
    "OpenClaw 工作目錄" => "/Users/gray/openclaw/quiz.db",
    "網頁執行目錄" => "/Users/gray/Sites/junior_high_king/quiz.db",
    "桌面備份目錄" => "/Users/gray/Desktop/openclaw_backup/full_dot_openclaw/workspace/quiz.db"
];

foreach ($dbs as $name => $path) {
    if (!file_exists($path)) continue;
    
    $db = new PDO("sqlite:$path");
    // 這次我們只搜阿鳳，不搜媽媽！
    $stmt = $db->prepare("SELECT id, question FROM questions WHERE question LIKE '%阿鳳%' LIMIT 1");
    $stmt->execute();
    $r = $stmt->fetch(PDO::FETCH_ASSOC);
    
    echo "🔎 檢查 $name:\n";
    if ($r) {
        echo "   🎯 【抓到了！】阿鳳就在這裡！ ID: " . $r['id'] . "\n";
        echo "   📍 路徑: $path\n";
        exit; // 抓到了就停
    } else {
        echo "   ❌ 這裡沒有阿鳳。\n";
    }
    echo "------------------------------------------\n";
}
echo "💀 絕望了！全機都沒有阿鳳，難道她是從雲端來的？\n";
