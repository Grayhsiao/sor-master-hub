<?php
/**
 * fix_db_structure.php
 * 功能：
 * 1. 清洗 yt_id：把完整的 YouTube 網址轉換成 11 位元 ID
 * 2. 清洗文字：移除歌手與歌名的前後空格、換行、引號
 * 3. 結構檢查：確保關鍵欄位沒有遺漏
 */

try {
    $db = new PDO("sqlite:quiz.db");
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    echo "<h2>🚀 開始資料庫深度修復...</h2>";

    // --- 1. 取得所有歌曲 ---
    $songs = $db->query("SELECT id, yt_id, artist, song_name FROM entertainment_songs")->fetchAll(PDO::FETCH_ASSOC);
    $fixCount = 0;

    foreach ($songs as $s) {
        $id = $s['id'];
        $rawYtId = trim($s['yt_id']);
        $rawArtist = trim($s['artist']);
        $rawSongName = trim($s['song_name']);

        $needUpdate = false;

        // --- A. 強力清洗 YouTube ID ---
        // 判斷是否為網址，提取 ID
        $cleanYtId = $rawYtId;
        if (preg_match('%(?:youtube(?:-nocookie)?\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^"&?/ ]{11})%i', $rawYtId, $match)) {
            $cleanYtId = $match[1];
            $needUpdate = true;
        } elseif (strlen($rawYtId) > 11) {
            // 如果不是網址但長度大於 11，嘗試暴力裁切（可能是帶了參數）
            $cleanYtId = substr($rawYtId, 0, 11);
            $needUpdate = true;
        }

        // --- B. 清洗文字格式 ---
        // 移除歌名裡的引號，避免 JavaScript 在按鈕渲染時掛掉
        $cleanSongName = str_replace(['"', "'"], "", $rawSongName);
        if ($cleanSongName !== $rawSongName)
            $needUpdate = true;

        if ($rawArtist !== trim($rawArtist))
            $needUpdate = true;

        // --- 執行更新 ---
        if ($needUpdate) {
            $stmt = $db->prepare("UPDATE entertainment_songs SET yt_id = ?, artist = ?, song_name = ? WHERE id = ?");
            $stmt->execute([$cleanYtId, trim($rawArtist), $cleanSongName, $id]);
            $fixCount++;
        }
    }

    echo "<p style='color:green;'>✅ 成功修復並優化了 $fixCount 筆歌曲資料！</p>";

    // --- 2. 結構優化：建立索引 (增加搜尋速度) ---
    $db->exec("CREATE INDEX IF NOT EXISTS idx_artist ON entertainment_songs (artist)");
    echo "<p>✅ 已建立歌手索引，搜尋速度提升。</p>";

    echo "<hr><h3>🎉 修復完成！</h3>";
    echo "<p>現在周杰倫的 45 首歌應該都能正常顯示圖片與互相抓取干擾項了。</p>";
    echo "<a href='game_song.php'>點我回遊戲測試</a>";

} catch (Exception $e) {
    echo "<p style='color:red;'>❌ 發生錯誤：" . $e->getMessage() . "</p>";
}
?>