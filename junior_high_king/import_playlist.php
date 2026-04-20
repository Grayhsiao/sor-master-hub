<?php
session_start();
require_once 'configgem.php';
$db = new PDO("sqlite:quiz.db");
$msg = "";

// 【終極水瀑布過濾邏輯】
function smarterClean($t, $artist) {
    if (trim($t) == $artist) return "未知歌曲";
    $found = "";

    // 模式 1: 提取 【 】 或 「 」 或 『 』
    if (preg_match('/[【「『](.*?)[】」』]/u', $t, $m)) {
        $found = $m[1];
    } 
    // 模式 2: 提取 ( ) 內的中文內容
    elseif (preg_match('/\(([\x{4e00}-\x{9fa5}]+.*?)\)/u', $t, $m)) {
        $found = $m[1];
    }
    // 模式 3: 尋找分隔符號 - 或 :
    elseif (strpos($t, '-') !== false || strpos($t, ':') !== false) {
        $sep = (strpos($t, '-') !== false) ? '-' : ':';
        $parts = explode($sep, $t);
        $found = (count($parts) > 1) ? $parts[1] : $parts[0];
    } 
    else { $found = $t; }

    // --- 二次精煉：刪除殘留垃圾 ---
    $garbage = ["/$artist/i", "/Jay Chou/i", "/Official/i", "/Video/i", "/MV/i", "/HD/i", "/歌詞/u", "/Lyrics/i", "/完整版/u"];
    $found = preg_replace($garbage, '', $found);

    // 關鍵步：如果是 "說了再見 Say Goodbye"，只抓中文部分
    if (preg_match('/^[^\x{00}-\x{7F}\s]+/u', trim($found), $match)) {
        return $match[0];
    }
    return trim($found) ?: "好聽的歌";
}

if (isset($_POST['playlist_url'])) {
    parse_str(parse_url($_POST['playlist_url'], PHP_URL_QUERY), $query);
    $playlistId = $query['list'] ?? '';
    $artist = $_POST['artist'] ?: '周杰倫';

    if ($playlistId) {
        $url = "https://www.googleapis.com/youtube/v3/playlistItems?" . http_build_query([
            'part' => 'snippet', 'playlistId' => $playlistId, 'maxResults' => 50, 'key' => YT_API_KEY
        ]);
        $data = json_decode(file_get_contents($url), true);
        if (isset($data['items'])) {
            $db->prepare("DELETE FROM entertainment_songs WHERE artist = ?")->execute([$artist]);
            $count = 0;
            foreach ($data['items'] as $item) {
                $rawTitle = $item['snippet']['title'];
                if (in_array($rawTitle, ['Deleted video', 'Private video'])) continue;
                
                $cleanName = smarterClean($rawTitle, $artist);
                $ytId = $item['snippet']['resourceId']['videoId'];
                $thumb = $item['snippet']['thumbnails']['default']['url'] ?? '';

                $db->prepare("INSERT INTO entertainment_songs (artist, song_name, yt_id, thumbnail) VALUES (?, ?, ?, ?)")
                   ->execute([$artist, $cleanName, $ytId, $thumb]);
                $count++;
            }
            $msg = "✅ 成功！已精準匯入 $count 首 $artist 的歌曲。";
        }
    }
}
?>
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>V6 精準採集</title>
<style>body{font-family:sans-serif;text-align:center;padding:50px;background:#f0f2f5;}
.box{background:white;padding:30px;border-radius:20px;max-width:500px;margin:auto;box-shadow:0 10px 20px rgba(0,0,0,0.1);}
input{width:90%;padding:12px;margin:10px 0;border-radius:10px;border:1px solid #ddd;}</style></head>
<body><div class="box"><h2>🎵 Playlist【精準模式】V6</h2>
<form method="POST">
    <input type="text" name="artist" value="周杰倫">
    <input type="text" name="playlist_url" placeholder="貼上播放清單網址" required>
    <button type="submit" style="width:95%;padding:12px;background:#6c5ce7;color:white;border:none;border-radius:10px;cursor:pointer;">開始精準匯入</button>
</form>
<p style="color:green;font-weight:bold;"><?=$msg?></p>
<a href="admin_list.php">前往管理頁面檢查</a> | <a href="index.php">回大廳</a></div></body></html>