<?php
// fix_db_data.php
$db = new PDO("sqlite:quiz.db");

// 1. 去除所有歌手名稱和歌名的前後空格
$db->exec("UPDATE entertainment_songs SET artist = TRIM(artist), song_name = TRIM(song_name)");

// 2. 移除歌名裡面的引號（避免 JS 報錯）
$db->exec("UPDATE entertainment_songs SET song_name = REPLACE(song_name, '\"', '')");
$db->exec("UPDATE entertainment_songs SET song_name = REPLACE(song_name, \"'\", \"\")");

echo "✅ 資料庫已完成「去空格」與「字元修正」。現在周杰倫的 45 首歌應該可以互相抓到了！";
?>