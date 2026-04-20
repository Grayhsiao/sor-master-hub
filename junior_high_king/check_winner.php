<?php
$dbs = [
    "OpenClaw版" => "/Users/gray/openclaw/quiz.db",
    "網頁執行版" => "/Users/gray/Sites/junior_high_king/quiz.db"
];

foreach ($dbs as $name => $path) {
    echo "🔎 檢查 $name...\n";
    if (!file_exists($path)) { echo "   ❌ 檔案不存在。\n\n"; continue; }
    
    $db = new PDO("sqlite:$path");
    $r = $db->query("SELECT option_a FROM questions WHERE question LIKE '%阿鳳%' LIMIT 1")->fetch();
    
    if ($r) {
        $content = $r[0];
        if ($content == "無內容" || empty($content)) {
            echo "   ⚠️  這顆也是「無內容」的空殼。\n";
        } else {
            echo "   ✅ 這顆是【有料】的！選項內容是: [" . $content . "]\n";
        }
    } else {
        echo "   ❌ 裡面根本沒有阿鳳這題。\n";
    }
    echo "\n";
}
