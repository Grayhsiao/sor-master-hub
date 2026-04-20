<?php
$db = new PDO("sqlite:/Users/gray/Sites/junior_high_king/quiz.db");
$rows = $db->query("SELECT id, options, option_a FROM questions")->fetchAll(PDO::FETCH_ASSOC);

$fixed_sync = 0;
$fixed_clean = 0;

foreach($rows as $r) {
    $data = json_decode($r['options'], true);
    if (is_string($data)) { $data = json_decode($data, true); }

    if (is_array($data) && count($data) >= 4) {
        // 1. 強力同步：把 options JSON 塞進 option_a~d 欄位
        $stmt = $db->prepare("UPDATE questions SET option_a=?, option_b=?, option_c=?, option_d=? WHERE id=?");
        
        // 2. 格式清理：去掉選項裡的 "A. ", "B. " 等字眼，只留純答案
        $clean_opts = array_map(function($item) {
            return preg_replace('/^[A-D]\.\s*/i', '', (string)$item);
        }, $data);

        $stmt->execute([$clean_opts[0], $clean_opts[1], $clean_opts[2], $clean_opts[3], $r['id']]);
        $fixed_sync++;
    }
}

// 3. 最後掃除：把所有還是「無內容」字眼的格子直接清空或補預設
$db->exec("UPDATE questions SET option_a='選項A' WHERE option_a='無內容' OR option_a IS NULL");

echo "✅ 同步並清理了 $fixed_sync 題的選項格式！\n";
echo "👉 老闆，現在去重新整理網頁，看看按鈕是不是變正常了？\n";
