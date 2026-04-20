<?php
$db_file = 'education.db';
echo "<h2>🩺 資料庫醫生檢查中...</h2>";

if (!file_exists($db_file)) {
    die("<p style='color:red;'>❌ 找不到 $db_file 檔案！請確認檔案是否在 /Users/gray/Sites/junior_high_king/ 資料夾下。</p>");
}

$db = new PDO("sqlite:$db_file");
echo "<p>✅ 成功連線到資料庫檔案：<b>" . realpath($db_file) . "</b></p>";

// 🚩 核心：列出資料庫裡所有的資料表
echo "<h3>1. 偵測到的資料表清單：</h3>";
$tables = $db->query("SELECT name FROM sqlite_master WHERE type='table'")->fetchAll(PDO::FETCH_COLUMN);

if (empty($tables)) {
    echo "<p style='color:red;'>⚠️ 警告：這個資料庫檔案是空的！裡面沒有任何資料表。</p>";
} else {
    echo "<ul>";
    foreach ($tables as $t) {
        if ($t == 'sqlite_sequence')
            continue;
        echo "<li>資料表名稱：<b>$t</b></li>";
    }
    echo "</ul>";
}

// 🚩 檢查 questions 表的結構
if (in_array('questions', $tables)) {
    echo "<h3>2. questions 表格結構：</h3>";
    $cols = $db->query("PRAGMA table_info(questions)")->fetchAll(PDO::FETCH_ASSOC);
    echo "<pre>";
    print_r($cols);
    echo "</pre>";
}
?>
<hr>
<p><a href="index.php">回首頁</a></p>