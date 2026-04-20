<?php
// clean_all.php
try {
    $db = new PDO("sqlite:quiz.db");
    // 清空所有歌曲資料
    $db->exec("DELETE FROM entertainment_songs");
    // 重置自動遞增的 ID，讓它從 1 開始
    $db->exec("DELETE FROM sqlite_sequence WHERE name='entertainment_songs'");

    echo "<h2>清空成功！</h2>";
    echo "<p>現在您的題庫已經空了，請回到 <a href='admin_yt_tool.php'>採集器</a> 重新匯入純淨的歌單。</p>";
} catch (Exception $e) {
    echo "錯誤：" . $e->getMessage();
}