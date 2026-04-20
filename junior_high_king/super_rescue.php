<?php
header('Content-Type: text/html; charset=utf-8');
$db = new PDO("sqlite:quiz.db");
$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

echo "<h2>🧪 國中智慧王 - 深度數據修復中...</h2>";

try {
    // 1. 強力救回「解析 (analysis)」
    // 從原始 imported_json 表格中提取 analysis 欄位並更新回 questions 表
    $res1 = $db->exec("UPDATE questions SET analysis = (
        SELECT json_extract(data_content, '$.analysis') 
        FROM imported_json 
        WHERE imported_json.id = questions.id
    )");
    echo "✅ 成功從原始資料救回 <b>$res1</b> 題的解析內容。<br>";

    // 2. 修正「學期 (semester)」資訊
    $res2 = $db->exec("UPDATE questions SET semester = (
        SELECT json_extract(data_content, '$.semester') 
        FROM imported_json 
        WHERE imported_json.id = questions.id
    )");
    echo "✅ 成功校正了 <b>$res2</b> 題的學期資訊。<br>";

    // 3. 確保年級標籤全部正確 (國文、生物去七年級；理化、數學去八年級)
    $db->exec("UPDATE questions SET grade = '七年級' WHERE subject IN ('國文', '生物')");
    $db->exec("UPDATE questions SET grade = '八年級' WHERE subject IN ('理化', '數學', '自然')");
    echo "✅ 年級標籤已根據科目重新校對。<br>";

    // 4. 檢查現在有多少題是有解析的
    $count = $db->query("SELECT count(*) FROM questions WHERE analysis IS NOT NULL AND analysis != ''")->fetchColumn();
    echo "<br><b>📊 目前進度報告：</b><br>";
    echo "資料庫中現在共有 <b>$count</b> 題具備詳細解析。<br>";

} catch (Exception $e) {
    echo "❌ 出錯了：" . $e->getMessage();
}

echo "<br><h3>🎉 修復完成！請執行以下動作：</h3>";
echo "1. 關閉此分頁。<br>";
echo "2. 回到遊戲頁面，按 <b>Cmd + Shift + R</b> (強制重整)。";
?>
