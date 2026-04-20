<?php
session_start();
require_once 'configgem.php';
$msg = "";
$db = new PDO("sqlite:quiz.db");

// --- 【V8 官方資料校正器】 ---
function getOfficialName($rawTitle, $artist)
{
    // 1. 先做初步清理
    $clean = trim(preg_replace("/$artist/i", '', $rawTitle));
    $clean = trim(preg_replace("/Official|MV|Video|Music|Video|【|】|\(|\)|\[|\]/i", '', $clean));

    // 2. 請求 iTunes API (官方音樂庫)
    $search_url = "https://itunes.apple.com/search?" . http_build_query([
        'term' => $artist . " " . $clean,
        'limit' => 1,
        'media' => 'music',
        'country' => 'TW'
    ]);

    $res = @file_get_contents($search_url);
    if ($res) {
        $json = json_decode($res, true);
        if (!empty($json['results'])) {
            // 只要 iTunes 找到對應的歌，我們就用官方定義的 trackName
            return $json['results'][0]['trackName'];
        }
    }

    // 3. 如果官方庫找不到，才退而求其次用我們之前的過濾邏輯
    if (preg_match('/^[^\x{00}-\x{7F}\s]+/u', $clean, $match)) {
        return $match[0];
    }
    return $clean ?: "好聽的歌";
}

if (isset($_POST['action'])) {
    $artist = $_POST['artist'];
    $url_input = $_POST['playlist_url'];
    $count = (int) $_POST['count'];

    parse_str(parse_url($url_input, PHP_URL_QUERY), $query);
    $playlistId = $query['list'] ?? '';

    // 取得 API URL (Playlist 或 Search)
    if ($playlistId) {
        $api_url = "https://www.googleapis.com/youtube/v3/playlistItems?" . http_build_query([
            'part' => 'snippet',
            'playlistId' => $playlistId,
            'maxResults' => 50,
            'key' => YT_API_KEY
        ]);
    } else {
        $api_url = "https://www.googleapis.com/youtube/v3/search?" . http_build_query([
            'part' => 'snippet',
            'q' => $artist . " MV",
            'type' => 'video',
            'videoCategoryId' => '10',
            'maxResults' => $count,
            'key' => YT_API_KEY
        ]);
    }

    $data = json_decode(file_get_contents($api_url), true);

    if (isset($data['items'])) {
        $added = 0;
        foreach ($data['items'] as $item) {
            $snippet = $item['snippet'];
            $rawTitle = $snippet['title'];
            if (in_array($rawTitle, ['Deleted video', 'Private video']))
                continue;

            // --- 核心改進：使用官方校正 ---
            $cleanName = getOfficialName($rawTitle, $artist);

            $ytId = ($playlistId) ? $snippet['resourceId']['videoId'] : $item['id']['videoId'];
            $thumb = $snippet['thumbnails']['default']['url'] ?? '';

            $db->prepare("INSERT INTO entertainment_songs (artist, song_name, yt_id, thumbnail) VALUES (?, ?, ?, ?)")
                ->execute([$artist, $cleanName, $ytId, $thumb]);
            $added++;
        }
        $msg = "✅ 匯入成功！已透過 iTunes 官方庫校正歌名。";
    }
}
?>
<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8">
    <title>V8 官方校正採集器</title>
    <style>
        body {
            font-family: sans-serif;
            background: #f0f2f5;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }

        .box {
            background: white;
            padding: 30px;
            border-radius: 24px;
            max-width: 450px;
            width: 90%;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            text-align: center;
        }

        input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border-radius: 12px;
            border: 2px solid #eee;
            box-sizing: border-box;
        }

        button {
            background: #6c5ce7;
            color: white;
            border: none;
            padding: 15px;
            border-radius: 12px;
            cursor: pointer;
            font-weight: bold;
            width: 100%;
        }
    </style>
</head>

<body>
    <div class="box">
        <h2>🚀 官方校正採集 V8</h2>
        <form method="POST">
            <input type="hidden" name="action" value="1">
            <input type="text" name="artist" placeholder="歌手 (如: 周杰倫)" required>
            <input type="text" name="playlist_url" placeholder="貼上播放清單網址 (選填)">
            <input type="number" name="count" value="20">
            <button type="submit">開始智慧採集</button>
        </form>
        <p style="color:#00b894; font-weight:bold;"><?= $msg ?></p>
        <a href="admin_list.php">檢查結果</a> | <a href="index.php">回大廳</a>
    </div>
</body>

</html>