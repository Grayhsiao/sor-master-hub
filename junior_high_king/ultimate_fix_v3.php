<?php
// ultimate_fix_v3.php - Gray's Lab 產線優化工具
header('Content-Type: text/html; charset=utf-8');
require_once 'configgem.php';

try {
    $db = new PDO("sqlite:quiz.db");

    // 1. 強力清洗：刪除所有名稱有問題的舊資料
    $db->exec("DELETE FROM entertainment_songs");
    $db->exec("DELETE FROM sqlite_sequence WHERE name='entertainment_songs'");

    // 2. 升級版採集器：鎖定「音樂分類」與「精準過濾」
    $yt_tool_code = <<<'EOD'
<?php
session_start();
require_once 'configgem.php';
$msg = ""; $db = new PDO("sqlite:quiz.db");

function cleanTitle($t, $a) {
    // 強化過濾器：徹底刪除歌手名、標點符號、YouTube 垃圾字眼
    $p = ["/$a/i", "/Music/i", "/Topic/i", "/Official/i", "/Video/i", "/MV/i", "/4K/i", "/HD/i", "/\d+K/i", "/\(.*\)/", "/\[.*\]/", "/【.*】/", "/-/", "/\s+/"];
    $c = trim(preg_replace($p, ' ', $t));
    return $c ?: "好聽的歌";
}

if (isset($_POST['action'])) {
    $artist = $_POST['artist']; $count = (int)$_POST['count'];
    // 加上 videoCategoryId=10 (音樂類) 與 type=video (排除頻道)
    $url = "https://www.googleapis.com/youtube/v3/search?".http_build_query([
        'part' => 'snippet', 'q' => $artist . " 歌曲", 'type' => 'video',
        'videoCategoryId' => '10', 'maxResults' => $count, 'order' => 'viewCount', 'key' => YT_API_KEY
    ]);
    $data = json_decode(file_get_contents($url), true);
    if (isset($data['items'])) {
        foreach ($data['items'] as $item) {
            $name = cleanTitle($item['snippet']['title'], $artist);
            $db->prepare("INSERT INTO entertainment_songs (artist, song_name, yt_id) VALUES (?, ?, ?)")
               ->execute([$artist, $name, $item['id']['videoId']]);
        }
        $msg = "✅ 採集完成！已過濾掉垃圾標題。";
    } else { $msg = "❌ API Key 錯誤，請檢查 configgem.php"; }
}
?>
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>採集器</title><style>body{font-family:sans-serif;text-align:center;padding:50px;background:#f0f2f5;}.box{background:white;padding:30px;border-radius:20px;max-width:400px;margin:auto;box-shadow:0 10px 20px rgba(0,0,0,0.1);}input{width:100%;padding:10px;margin:10px 0;box-sizing:border-box;}button{width:100%;padding:10px;background:#6c5ce7;color:white;border:none;border-radius:10px;cursor:pointer;}</style></head>
<body><div class="box"><h2>🚀 歌手歌曲採集 (V3)</h2><form method="POST"><input type="hidden" name="action" value="1"><input type="text" name="artist" placeholder="歌手姓名" required><input type="number" name="count" value="15"><button type="submit">開始採購純淨歌單</button></form><p><?=$msg?></p><a href="index.php">回大廳</a></div></body></html>
EOD;

    // 3. 升級版遊戲頁面：修復「沒選項」與「強制顯示麥克風」
    $game_code = <<<'EOD'
<?php 
session_start();
$db = new PDO("sqlite:quiz.db");
$artist = $_GET['artist'] ?? 'all';
$stmt = ($artist === 'all') ? $db->query("SELECT * FROM entertainment_songs ORDER BY RANDOM() LIMIT 1") : $db->prepare("SELECT * FROM entertainment_songs WHERE artist = ? ORDER BY RANDOM() LIMIT 1");
if($artist !== 'all') $stmt->execute([$artist]);
$song = $stmt->fetch(PDO::FETCH_ASSOC);
if (!$song) die("題庫空了，請先採集！");

// 修復選項：如果該歌手不夠，從「全庫」隨機抓人
$all = $db->query("SELECT song_name FROM entertainment_songs WHERE song_name != '".$song['song_name']."' ORDER BY RANDOM() LIMIT 3")->fetchAll(PDO::FETCH_COLUMN);
// 備用方案：如果還是不夠，補足 4 個
while(count($all) < 3) { $all[] = "聽媽媽的話"; $all[] = "挪威的森林"; } 
$all[] = $song['song_name'];
shuffle($all);
?>
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
<style>
    :root { --primary: #6c5ce7; --bg: #f0f2f5; }
    body { font-family: sans-serif; background: var(--bg); text-align: center; margin: 0; }
    .card { background: white; border-radius: 25px; padding: 25px; max-width: 400px; margin: 20px auto; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
    .mic-btn { background: #ff7675; color: white; width: 80px; height: 80px; border-radius: 50%; margin: 15px auto; display: flex !important; justify-content: center; align-items: center; font-size: 32px; cursor: pointer; border: none; }
    .listening { animation: pulse 1s infinite; background: #d63031; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }
    .btn { padding: 12px; border-radius: 12px; border: none; cursor: pointer; font-weight: bold; width: 100%; margin-bottom: 8px; }
    #feedback { position: fixed; top: 0; left: 0; width: 100%; height: 100%; display: none; justify-content: center; align-items: center; z-index: 100; color: white; font-size: 120px; }
    #player { position: absolute; left: -9999px; }
</style></head>
<body>
    <div id="feedback"></div>
    <div class="card">
        <h3><?= $song['artist'] ?> 猜歌王</h3>
        <div id="player"></div>
        <h1 id="timer">3s</h1>
        <button id="playBtn" class="btn" style="background:var(--primary); color:white; height:60px; font-size:18px;" onclick="playMusic()">▶ 開始聽歌</button>
        
        <button class="mic-btn" id="micBtn" onclick="startVoice()"><i class="fas fa-microphone"></i></button>
        <p style="font-size:12px; color:#aaa;">點擊麥克風說出答案</p>

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <?php foreach($all as $o): ?>
                <button class="btn" style="background:#eee; font-size:13px; height:50px;" onclick="check('<?= addslashes($o) ?>')"><?= $o ?></button>
            <?php endforeach; ?>
        </div>
        <button class="btn" style="background:#ddd; margin-top:15px;" onclick="location.href='index.php'">回大廳</button>
    </div>
    <script src="https://www.youtube.com/iframe_api"></script>
    <script>
        let player, duration = 3, isPlaying = false;
        const songData = <?= json_encode($song) ?>;
        function onYouTubeIframeAPIReady() { player = new YT.Player('player', { videoId: songData.yt_id }); }
        function playMusic() {
            if(isPlaying) return; isPlaying = true;
            document.getElementById('playBtn').innerText = "🎵 播放中...";
            player.seekTo(60); player.playVideo();
            let left = duration;
            const t = setInterval(() => {
                left--; document.getElementById('timer').innerText = left + "s";
                if(left <= 0) { 
                    clearInterval(t); player.pauseVideo(); isPlaying = false; 
                    document.getElementById('playBtn').innerText = "▶ 再聽一次";
                }
            }, 1000);
        }
        function startVoice() {
            const SpeechSDK = window.SpeechRecognition || window.webkitSpeechRecognition;
            if(!SpeechSDK) return alert("您的瀏覽器不支援語音辨識");
            const rec = new SpeechSDK();
            rec.lang = 'zh-TW'; rec.start();
            document.getElementById('micBtn').classList.add('listening');
            rec.onresult = (e) => { check(e.results[0][0].transcript); };
            rec.onend = () => document.getElementById('micBtn').classList.remove('listening');
        }
        function check(input) {
            const fb = document.getElementById('feedback');
            const correct = input.includes(songData.song_name) || songData.song_name.includes(input);
            fb.style.display = 'flex';
            if(correct) {
                fb.style.background = 'rgba(0,184,148,0.95)'; fb.innerHTML = '<i class="fas fa-check"></i>';
                setTimeout(() => location.reload(), 1500);
            } else {
                fb.style.background = 'rgba(214,48,49,0.95)'; fb.innerHTML = '<i class="fas fa-times"></i>';
                setTimeout(() => fb.style.display = 'none', 1000);
            }
        }
    </script>
</body></html>
EOD;

    file_put_contents('admin_yt_tool.php', $yt_tool_code);
    file_put_contents('game_song.php', $game_code);
    echo "<h2>🎉 產線 V3 升級成功！</h2>";
    echo "1. <b>資料庫洗淨</b>：舊的 Jay Chou Music 已清除。<br>";
    echo "2. <b>精準搜尋</b>：現在只會抓「音樂分類」的影片，避開主題頻道。<br>";
    echo "3. <b>选项保險</b>：現在格子絕對不會空掉。<br>";
    echo "4. <b>麥克風強制顯示</b>：優化了 UI 邏輯。<br>";
    echo "請快去 <a href='admin_yt_tool.php'>重新採集</a> 測試！";

} catch (Exception $e) {
    echo "❌ 錯誤：" . $e->getMessage();
}