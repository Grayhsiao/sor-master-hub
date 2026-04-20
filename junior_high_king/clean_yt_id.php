<?php
// clean_yt_id.php
$db = new PDO("sqlite:quiz.db");
$songs = $db->query("SELECT id, yt_id FROM entertainment_songs")->fetchAll(PDO::FETCH_ASSOC);

foreach ($songs as $s) {
    $rawId = $s['yt_id'];
    $cleanId = "";

    // 判斷是否為網址，提取 ID
    if (preg_match('%(?:youtube(?:-nocookie)?\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^"&?/ ]{11})%i', $rawId, $match)) {
        $cleanId = $match[1];
    } else {
        $cleanId = trim($rawId); // 如果本來就是 ID，去空格
    }

    if ($cleanId && strlen($cleanId) == 11) {
        $stmt = $db->prepare("UPDATE entertainment_songs SET yt_id = ? WHERE id = ?");
        $stmt->execute([$cleanId, $s['id']]);
    }
}
echo "✅ 已完成 " . count($songs) . " 首歌的 ID 清洗！現在圖片應該都會出來了。";
?>