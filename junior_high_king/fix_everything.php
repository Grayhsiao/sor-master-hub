<?php
$db_path = "/Users/gray/Sites/junior_high_king/quiz.db";
$db = new PDO("sqlite:" . $db_path);
$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

echo "<h2>🚀 國中智慧王 - 系統全自動修復中...</h2>";

// 1. 強制同步年級標籤 (從原始資料抓取)
$res1 = $db->exec("UPDATE questions SET grade = (SELECT json_extract(data_content, '$.grade') FROM imported_json WHERE imported_json.id = questions.id) WHERE grade IS NULL OR grade = '' OR grade = '(空白)'");
echo "✅ 成功恢復 $res1 題的正確年級標籤。<br>";

// 2. 針對沒標到的，進行科目關鍵字自動歸類
$db->exec("UPDATE questions SET grade = '七年級' WHERE subject IN ('國文', '生物') AND (grade IS NULL OR grade = '')");
$db->exec("UPDATE questions SET grade = '八年級' WHERE subject IN ('理化', '數學') AND (grade IS NULL OR grade = '')");
$db->exec("UPDATE questions SET grade = '八年級' WHERE grade IS NULL OR grade = ''"); // 最後保底全變八年級
echo "✅ 剩餘無標籤題目已完成保底歸類。<br>";

// 3. 修正理化誤標為數學的問題
$db->exec("UPDATE questions SET subject = '自然' WHERE subject = '數學' AND (question LIKE '%原子%' OR question LIKE '%化學%' OR question LIKE '%反應式%')");
$db->exec("UPDATE questions SET subject = '自然' WHERE subject IN ('理化', '生物')");
echo "✅ 理化/數學分類修正完畢。<br>";

// 4. 重寫 get_questions.php (確保支援 topic 與 id)
$code = '<?php
header("Content-Type: application/json");
$db = new PDO("sqlite:'.$db_path.'");
$g_map = ["7"=>"七年級", "8"=>"八年級", "9"=>"九年級"];
$grade = $g_map[$_GET["grade"] ?? "8"] ?? "八年級";
$s_map = ["science"=>["自然","理化","生物"], "math"=>["數學"], "chinese"=>["國文"], "english"=>["英文"], "social"=>["社會","地理","歷史","公民"]];
$subs = $s_map[$_GET["subject"] ?? "math"] ?? [$_GET["subject"]];
$where = "grade = ? AND subject IN (".str_repeat("?,", count($subs)-1)."?)";
$stmt = $db->prepare("SELECT * FROM questions WHERE $where ORDER BY RANDOM() LIMIT 1");
$stmt->execute(array_merge([$grade], $subs));
$q = $stmt->fetch(PDO::FETCH_ASSOC);
if($q){
    echo json_encode(["status"=>"success","data"=>["id"=>$q["id"],"question"=>$q["question"],"options"=>[$q["option_a"],$q["option_b"],$q["option_c"],$q["option_d"]],"answer"=>$q["answer"],"analysis"=>$q["analysis"],"topic"=>$q["subject"]]]);
} else {
    echo json_encode(["status"=>"error","message"=>"此分類暫無題目"]);
}';
file_put_contents("get_questions.php", $code);
echo "✅ get_questions.php 已重寫完成。<br>";

echo "<h3>🎉 修復完成！請重新整理遊戲畫面。</h3>";
?>
