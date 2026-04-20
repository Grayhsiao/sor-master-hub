<?php
// fix_database.php
header('Content-Type: text/html; charset=utf-8');
try {
    $db = new PDO("sqlite:quiz.db");
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // 1. 檢查並增加 exam 欄位 (如果還沒有的話)
    $db->exec("ALTER TABLE questions ADD COLUMN exam TEXT");
    echo "✅ 已建立『段考 (exam)』欄位<br>";
} catch (Exception $e) {
    echo "ℹ️ 段考欄位可能已存在，跳過建立。<br>";
}

try {
    // 2. 把目前資料庫裡的所有題目，統一修正為：下學期 (2)、第一次月考 (1)
    // 根據您的說明，目前匯入的都是這批資料
    $stmt = $db->prepare("UPDATE questions SET semester = '2', exam = '1'");
    $stmt->execute();
    $count = $stmt->rowCount();

    echo "✅ 成功校正 $count 題資料！<br>";
    echo "🚩 目前狀態：所有題目已標記為【下學期】、【第一次月考】<br>";

    // 3. 驗證一下
    $check = $db->query("SELECT subject, grade, semester, exam FROM questions LIMIT 1")->fetch(PDO::FETCH_ASSOC);
    echo "<h3>📊 抽樣檢查結果：</h3>";
    echo "<pre>"; print_r($check); echo "</pre>";

} catch (Exception $e) {
    echo "❌ 修正失敗：" . $e->getMessage();
}
?>