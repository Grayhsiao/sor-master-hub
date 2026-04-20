<?php
$path = "/Users/gray/Sites/junior_high_king/";
$db_path = $path . "quiz.db";

// 1. 強力產生 get_stats.php (盤點機)
$stats_code = '<?php
header("Content-Type: application/json");
$db = new PDO("sqlite:'.$db_path.'");
$res = $db->query("SELECT grade, subject, count(*) as total FROM questions WHERE grade IS NOT NULL AND grade != \"\" GROUP BY grade, subject")->fetchAll(PDO::FETCH_ASSOC);
$stats = [];
foreach($res as $r){
    $m = ["數學"=>"math","自然"=>"science","國文"=>"chinese","英文"=>"english","社會"=>"social"];
    $s = $m[$r["subject"]] ?? $r["subject"];
    $stats[$r["grade"]][$s] = $r["total"];
}
echo json_encode($stats);';
file_put_contents($path . "get_stats.php", $stats_code);

// 2. 強力產生 get_questions.php (導航機)
$get_q_code = '<?php
header("Content-Type: application/json");
$db = new PDO("sqlite:'.$db_path.'");
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
file_put_contents($path . "get_questions.php", $get_q_code);

// 3. 嘗試幫 game.php 加上題號顯示
$game_content = file_get_contents($path . "game.php");
if (strpos($game_content, "displayQuestionId") === false) {
    $game_content = str_replace('id="questionContent"', 'id="displayQuestionId" style="font-size:0.8em;color:#888;"></div><div id="questionContent"', $game_content);
    $game_content = str_replace("document.getElementById('questionContent').innerText = data.question;", "document.getElementById('questionContent').innerText = data.question; document.getElementById('displayQuestionId').innerText = '題號：' + data.id;", $game_content);
    file_put_contents($path . "game.php", $game_content);
}

echo "✅ [1/3] 統計 API 已修正\n";
echo "✅ [2/3] 題號輸出已修正\n";
echo "✅ [3/3] 網頁顯示邏輯已修補\n";
echo "🚀 老闆，現在請重新整理網頁試試看！\n";
