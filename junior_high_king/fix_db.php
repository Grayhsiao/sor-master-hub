<?php
$db = new PDO("sqlite:quiz.db");
// 確保音樂表存在且有 thumbnail
$db->exec("CREATE TABLE IF NOT EXISTS entertainment_songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist TEXT, song_name TEXT, yt_id TEXT, thumbnail TEXT,
    start_sec INTEGER DEFAULT 60
)");
$res = $db->query("PRAGMA table_info(entertainment_songs)")->fetchAll();
$hasThumb = false;
foreach ($res as $col) {
    if ($col['name'] == 'thumbnail')
        $hasThumb = true;
}
if (!$hasThumb)
    $db->exec("ALTER TABLE entertainment_songs ADD COLUMN thumbnail TEXT");
echo "✅ 音樂資料表已準備就緒。";
?>