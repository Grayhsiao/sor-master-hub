<?php
try {
    $db = new PDO('sqlite:quiz.db');
    $db->exec("ALTER TABLE entertainment_songs ADD COLUMN thumbnail TEXT;");
    echo "✅ 資料庫已成功新增 thumbnail 欄位。";
} catch (Exception $e) {
    echo "ℹ️ 欄位可能已存在或發生錯誤：" . $e->getMessage();
}
?>