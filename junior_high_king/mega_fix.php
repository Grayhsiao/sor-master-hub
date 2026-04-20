<?php
$db = new PDO("sqlite:/Users/gray/Sites/junior_high_king/quiz.db");
$rows = $db->query("SELECT id, options, option_a FROM questions")->fetchAll(PDO::FETCH_ASSOC);

$fixed = 0;
foreach($rows as $r) {
    // 檢查是否需要修復 (A是空的, 或等於無內容)
    $valA = trim($r['option_a']);
    if ($valA === "" || $valA === "無內容" || $valA === "null") {
        
        $raw = $r['options'];
        $data = json_decode($raw, true);
        
        // 處理雙重 JSON 封裝的情況
        if (is_string($data)) {
            $data = json_decode($data, true);
        }

        if (is_array($data) && count($data) >= 4) {
            $stmt = $db->prepare("UPDATE questions SET option_a=?, option_b=?, option_c=?, option_d=? WHERE id=?");
            $stmt->execute([
                (string)$data[0], 
                (string)$data[1], 
                (string)$data[2], 
                (string)$data[3], 
                $r['id']
            ]);
            $fixed++;
        }
    }
}
echo "✅ 總共強行修復了 $fixed 題！快去重新整理網頁！\n";
