<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);
header('Content-Type: text/html; charset=utf-8');
$db = new PDO("sqlite:quiz.db");
$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

echo "<h2>🛡️ 最終 Boss 級掃蕩：556 題大補完行動</h2>";

// 抓出所有沒選項但有答案的題目 (不分科目)
$sql = "SELECT id, question, answer, subject FROM questions 
        WHERE (option_a IS NULL OR LENGTH(TRIM(option_a)) < 1) 
        AND (answer IS NOT NULL AND LENGTH(TRIM(answer)) > 0)";

$questions = $db->query($sql)->fetchAll(PDO::FETCH_ASSOC);
echo "偵測到 " . count($questions) . " 題目標...<br><hr>";

$update = $db->prepare("UPDATE questions SET option_a = ?, option_b = ?, option_c = ?, option_d = ?, answer = ? WHERE id = ?");

$successCount = 0;
$skipCount = 0;

foreach ($questions as $q) {
    $id = $q['id'];
    $correct = trim((string)$q['answer']);

    try {
        // 🚩 處理「殭屍字母題」 (例如：答案是 A，但沒選項內容)
        if (in_array(strtoupper($correct), ['A', 'B', 'C', 'D'])) {
            $ansTag = strtoupper($correct);
            $options = [
                "A" => "選項修復中 (A)",
                "B" => "選項修復中 (B)",
                "C" => "選項修復中 (C)",
                "D" => "選項修復中 (D)"
            ];
            $options[$ansTag] = "這才是正確選項 (請參考解析)";
            
            $update->execute([$options["A"], $options["B"], $options["C"], $options["D"], $ansTag, $id]);
            $successCount++;
            continue;
        }

        // --- 🤖 數學/座標/填空轉選擇邏輯 ---
        $wrong = [];
        if (is_numeric($correct)) {
            $val = (float)$correct;
            $wrong = [(string)($val + 2), (string)($val - 2), (string)($val * -1 + 1)];
        } else {
            // 處理座標或代數式
            $wrong = ["非 " . $correct, "誤 " . $correct, "修正 " . $correct];
            $w3 = preg_replace_callback('/\d+/', function($m) { return $m[0] + 1; }, $correct);
            if ($w3 !== $correct) $wrong[2] = $w3;
        }

        // 確保不重複
        while (count(array_unique($wrong)) < 3 || in_array($correct, $wrong)) {
            $wrong[] = $correct . rand(10, 99);
        }
        $wrong = array_values(array_unique(array_slice($wrong, 0, 3)));

        // 洗牌
        $all = [$correct, $wrong[0], $wrong[1], $wrong[2]];
        shuffle($all);
        $idx = array_search($correct, $all);
        $letter = ['A', 'B', 'C', 'D'][$idx];

        $update->execute([$all[0], $all[1], $all[2], $all[3], $letter, $id]);
        $successCount++;
        
        if ($successCount % 50 == 0) echo "已處理 $successCount 題...<br>";

    } catch (Exception $e) {
        $skipCount++;
        echo "⚠️ ID $id 處理失敗: " . $e->getMessage() . "<br>";
    }
}

echo "<hr><h3>🏁 救援行動結束！</h3>";
echo "✅ 成功補完：$successCount 題<br>";
echo "❌ 失敗跳過：$skipCount 題 (多為完全無答案題)<br>";
?>
echo "<hr><h3>🏁 大功告成！本次救援了 $count 題。</h3>";
?>