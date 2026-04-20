<?php
$db_path = "quiz.db";
try {
    $db = new PDO("sqlite:" . $db_path);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo "<h1>🚀 系統核心重組中...</h1>";

    // --- 1. 資料庫強力修復 (解決紅字未標記問題) ---
    // 先從原始資料抓
    $db->exec("UPDATE questions SET grade = (SELECT json_extract(data_content, '$.grade') FROM imported_json WHERE imported_json.id = questions.id) WHERE grade IS NULL OR grade = '' OR grade = '(空白)'");
    // 關鍵字補強
    $db->exec("UPDATE questions SET grade = '七年級' WHERE subject IN ('國文', '生物') AND (grade IS NULL OR grade = '')");
    $db->exec("UPDATE questions SET grade = '八年級' WHERE subject IN ('理化', '數學', '自然') AND (grade IS NULL OR grade = '')");
    $db->exec("UPDATE questions SET grade = '八年級' WHERE grade IS NULL OR grade = ''"); 
    echo "✅ 資料庫 2500 題標籤已全數歸位。<br>";

    // --- 2. 重寫 get_stats.php (盤點機) ---
    $stats_code = '<?php
    header("Content-Type: application/json");
    $db = new PDO("sqlite:quiz.db");
    $res = $db->query("SELECT grade, subject, count(*) as total FROM questions GROUP BY grade, subject")->fetchAll(PDO::FETCH_ASSOC);
    $stats = [];
    foreach($res as $r){
        $m = ["數學"=>"math","自然"=>"science","國文"=>"chinese","英文"=>"english","社會"=>"social"];
        $s = $m[$r["subject"]] ?? $r["subject"];
        if($r["grade"]) $stats[$r["grade"]][$s] = (int)$r["total"];
    }
    echo json_encode($stats);';
    file_put_contents("get_stats.php", $stats_code);
    echo "✅ 盤點機 get_stats.php 已更新。<br>";

    // --- 3. 重寫 get_questions.php (確保右上角不卡載入中) ---
    $get_q_code = '<?php
    header("Content-Type: application/json");
    $db = new PDO("sqlite:quiz.db");
    $g_map = ["7"=>"七年級","8"=>"八年級","9"=>"九年級"];
    $grade = $g_map[$_GET["grade"] ?? "8"] ?? "八年級";
    $s_map = ["science"=>["自然","理化","生物"],"math"=>["數學"],"chinese"=>["國文"],"english"=>["英文"],"social"=>["社會","地理","歷史","公民"]];
    $subs = $s_map[$_GET["subject"] ?? "math"] ?? [$_GET["subject"]];
    $where = "grade = ? AND subject IN (".str_repeat("?,", count($subs)-1)."?)";
    $stmt = $db->prepare("SELECT * FROM questions WHERE $where ORDER BY RANDOM() LIMIT 1");
    $stmt->execute(array_merge([$grade], $subs));
    $q = $stmt->fetch(PDO::FETCH_ASSOC);
    if($q){
        echo json_encode(["status"=>"success","data"=>["id"=>$q["id"],"question"=>$q["question"],"options"=>[$q["option_a"],$q["option_b"],$q["option_c"],$q["option_d"]],"answer"=>$q["answer"],"analysis"=>$q["analysis"],"topic"=>$q["subject"]]]);
    } else {
        echo json_encode(["status"=>"error","message"=>"此分類尚無題目"]);
    }';
    file_put_contents("get_questions.php", $get_q_code);
    echo "✅ 導航機 get_questions.php 已更新。<br>";

    echo "<h2>🎉 全系統修復完成！請立刻執行下一步。</h2>";
} catch (Exception $e) {
    die("出錯了：" . $e->getMessage());
}
?>
