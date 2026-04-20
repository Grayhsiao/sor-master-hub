<?php
$db = new PDO('sqlite:education.db');
echo "<h2>目前的題庫內容盤點：</h2>";

// 抓取所有科目名稱與題數
$stmt = $db->query("SELECT subject, grade, COUNT(*) as count FROM questions GROUP BY subject, grade");
$rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

if (!$rows) {
    echo "<p style='color:red;'>資料表裡面目前完全沒有題目喔！</p>";
} else {
    echo "<table border='1' style='border-collapse:collapse; width:100%; text-align:center;'>
            <tr style='background:#eee;'><th>資料庫內的科目名稱</th><th>年級</th><th>總題數</th></tr>";
    foreach ($rows as $r) {
        echo "<tr><td><b>{$r['subject']}</b></td><td>{$r['grade']}</td><td>{$r['count']}</td></tr>";
    }
    echo "</table>";
}
?>
<p><a href="quiz_lobby.php">回學科大廳</a></p>