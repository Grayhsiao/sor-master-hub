<?php
try {
    $db = new PDO('sqlite:quiz.db');
    // 檢查是否有 thumbnail 欄位
    $check = $db->query("PRAGMA table_info(entertainment_songs)")->fetchAll(PDO::FETCH_ASSOC);
    $exists = false;
    foreach ($check as $col) {
        if ($col['name'] === 'thumbnail') {
            $exists = true;
            break;
        }
    }

    if (!$exists) {
        $db->exec("ALTER TABLE entertainment_songs ADD COLUMN thumbnail TEXT;");
        echo "✅ 已成功新增 thumbnail 欄位。";
    } else {
        echo "ℹ️ thumbnail 欄位已存在，無需更新。";
    }
} catch (Exception $e) {
    echo "❌ 發生錯誤：" . $e->getMessage();
}
?>