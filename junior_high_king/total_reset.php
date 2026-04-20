<?php
header('Content-Type: text/html; charset=utf-8');
$db = new PDO("sqlite:quiz.db");
$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

echo "<h2>🚀 執行全系統資料重組 (數學選項強力修復版)...</h2>";

try {
    $db->exec("DELETE FROM questions");
    $stmt = $db->query("SELECT data_content FROM imported_json");
    $insert = $db->prepare("INSERT INTO questions (question, option_a, option_b, option_c, option_d, answer, analysis, grade, subject, semester) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");

    $count = 0;
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $data = json_decode($row['data_content'], true);
        if (!$data)
            continue;

        $clean = function ($val) {
            if (is_array($val))
                return json_encode($val, JSON_UNESCAPED_UNICODE);
            return trim((string)$val);
        };

        $qText = $clean($data['question']);
        $sub = trim($clean($data['subject'] ?? '未分類'));

        // 1. 抓取選項 (萬能抓取邏輯)
        $opts = [];
        if (isset($data['options']) && is_array($data['options']))
            $opts = $data['options'];
        elseif (isset($data['choices']) && is_array($data['choices']))
            $opts = $data['choices'];
        elseif (isset($data['A']))
            $opts = [$data['A'], $data['B'], $data['C'], $data['D']];

        // 2. 八大科目細分邏輯 (維持我們之前的成果)
        if (!in_array($sub, ['數學', '國文', '英文'])) {
            if ($sub == '自然' || $sub == '理化' || $sub == '生物') {
                if (preg_match('/細胞|器官|植物|動物|遺傳|生態|生物|呼吸|消化|循環/', $qText))
                    $sub = '生物';
                else if (preg_match('/原子|分子|化學|元素|速度|加速度|力|光|熱|壓|電|溶解/', $qText))
                    $sub = '理化';
                else
                    $sub = '生物';
            }
            else if ($sub == '社會' || $sub == '地理' || $sub == '歷史' || $sub == '公民') {
                if (preg_match('/朝代|皇帝|戰爭|西元|民國|清代|日治|考古/', $qText))
                    $sub = '歷史';
                else if (preg_match('/法律|權利|政府|民主|投票|市場|貨幣/', $qText))
                    $sub = '公民';
                else if (preg_match('/經度|緯度|地形|氣候|地圖|位置|河川|洋流/', $qText))
                    $sub = '地理';
                else
                    $sub = '地理';
            }
        }

        // 3. 處理段考
        $exam = 1;
        $rawExam = $clean($data['exam_type'] ?? '');
        if (strpos($rawExam, '2') !== false)
            $exam = 2;
        if (strpos($rawExam, '3') !== false)
            $exam = 3;

        // 4. 寫入 (確保 A, B, C, D 都有對齊)
        $insert->execute([
            $qText,
            $clean($opts[0] ?? ''),
            $clean($opts[1] ?? ''),
            $clean($opts[2] ?? ''),
            $clean($opts[3] ?? ''),
            $clean($data['answer']),
            $clean($data['analysis'] ?? '無解析'),
            $clean($data['grade'] ?? '七年級'),
            $sub,
            $exam
        ]);
        $count++;
    }
    echo "✅ 成功重新匯入 <b>$count</b> 題！<br>";
    $stats = $db->query("SELECT subject, count(*) as c FROM questions GROUP BY subject ORDER BY c DESC")->fetchAll(PDO::FETCH_ASSOC);
    foreach ($stats as $s)
        echo " - {$s['subject']}: {$s['c']} 題<br>";

}
catch (Exception $e) {
    echo "❌ 錯誤：" . $e->getMessage();
}
?>