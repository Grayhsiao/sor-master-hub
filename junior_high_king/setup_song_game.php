<?php
// setup_song_game.php - Gray's Lab 自動化部署工具
header('Content-Type: text/html; charset=utf-8');

try {
    // 1. 初始化資料庫
    $db = new PDO("sqlite:quiz.db");
    $db->exec("CREATE TABLE IF NOT EXISTS entertainment_songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        artist TEXT NOT NULL,
        song_name TEXT NOT NULL,
        yt_id TEXT NOT NULL,
        start_sec INTEGER DEFAULT 60,
        options TEXT
    )");
    echo "✅ 資料庫表結構已就緒...<br>";

    // --- 檔案內容定義 ---

    // A. index.php (動態歌手按鈕版)
    $index_content = <<<'EOD'
<?php session_start(); ?>
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智慧教育平台 - 遊戲大廳</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root { --primary: #6c5ce7; --secondary: #00b894; --accent: #fdcb6e; --bg: #f0f2f5; }
        body { font-family: 'PingFang TC', sans-serif; background: var(--bg); margin: 0; padding-bottom: 50px; }
        .top-nav { background: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); }
        .user-chip { display: flex; align-items: center; gap: 8px; background: #eee; padding: 5px 15px; border-radius: 50px; }
        .container { max-width: 600px; margin: 20px auto; padding: 0 15px; }
        .tab-group { display: flex; background: #dfe6e9; padding: 5px; border-radius: 15px; margin-bottom: 20px; }
        .tab-btn { flex: 1; padding: 12px; border: none; border-radius: 12px; cursor: pointer; font-weight: bold; transition: 0.3s; background: none; color: #636e72; }
        .tab-btn.active { background: white; color: var(--primary); box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1); }
        .section-content { display: none; }
        .section-content.active { display: block; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .big-btn { background: white; border: 2px solid #eee; border-radius: 20px; padding: 25px 10px; font-size: 18px; font-weight: bold; cursor: pointer; transition: 0.3s; display: flex; flex-direction: column; align-items: center; gap: 10px; }
        .big-btn:hover { border-color: var(--primary); transform: translateY(-3px); }
        .big-btn i { font-size: 30px; color: var(--primary); }
        .difficulty-badge { font-size: 11px; padding: 2px 8px; border-radius: 5px; background: #e3fcef; color: #00b894; }
    </style>
</head>
<body>
    <div class="top-nav">
        <div style="font-weight: bold; font-size: 20px; color: var(--primary);">智慧教育王</div>
        <?php if (isset($_SESSION['user_id'])): ?>
            <div class="user-chip"><img src="<?= $_SESSION['user_pic'] ?>" style="width:30px;border-radius:50%"> <span><?= $_SESSION['user_name'] ?></span></div>
        <?php else: ?>
            <button onclick="location.href='login.php'" style="background:#00B900; color:white; border:none; padding:8px 15px; border-radius:10px;">LINE 登入</button>
        <?php endif; ?>
    </div>
    <div class="container">
        <div class="tab-group">
            <button class="tab-btn active" onclick="switchTab(event, 'quiz')">國中學科</button>
            <button class="tab-btn" onclick="switchTab(event, 'fun')">娛樂模式</button>
        </div>
        <div id="quiz" class="section-content active">
            <div class="grid">
                <button class="big-btn" onclick="location.href='game.php?subject=國文'"><i class="fas fa-book"></i>國文</button>
                <button class="big-btn" onclick="location.href='game.php?subject=數學'"><i class="fas fa-calculator"></i>數學</button>
            </div>
        </div>
        <div id="fun" class="section-content">
            <div class="grid">
                <button class="big-btn" onclick="location.href='game_song.php?artist=all'">
                    <i class="fas fa-random" style="color:var(--accent);"></i>綜合大亂鬥<span class="difficulty-badge">全歌手隨機</span>
                </button>
                <?php
                $db = new PDO("sqlite:quiz.db");
                $artists = $db->query("SELECT DISTINCT artist FROM entertainment_songs")->fetchAll(PDO::FETCH_COLUMN);
                foreach ($artists as $a): ?>
                    <button class="big-btn" onclick="location.href='game_song.php?artist=<?= urlencode($a) ?>'">
                        <i class="fas fa-microphone-alt"></i><?= $a ?><span class="difficulty-badge">歌手專場</span>
                    </button>
                <?php endforeach; ?>
            </div>
            <div style="margin-top:20px; text-align:center;">
                <button onclick="location.href='admin_yt_tool.php'" style="padding:10px; border-radius:10px; border:1px solid #ddd; cursor:pointer;">+ 新增歌曲</button>
                <button onclick="location.href='admin_list.php'" style="padding:10px; border-radius:10px; border:1px solid #ddd; cursor:pointer; margin-left:10px;">管理庫存</button>
            </div>
        </div>
    </div>
    <script>
        function switchTab(evt, tabId) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.section-content').forEach(s => s.classList.remove('active'));
            evt.currentTarget.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        }
    </script>
</body>
</html>
EOD;

    // B. game_song.php (UI 播放按鈕優化版)
    $game_song_content = <<<'EOD'
<?php 
session_start();
$db = new PDO("sqlite:quiz.db");
$artist = $_GET['artist'] ?? 'all';
if ($artist === 'all') {
    $song = $db->query("SELECT * FROM entertainment_songs ORDER BY RANDOM() LIMIT 1")->fetch(PDO::FETCH_ASSOC);
} else {
    $stmt = $db->prepare("SELECT * FROM entertainment_songs WHERE artist = ? ORDER BY RANDOM() LIMIT 1");
    $stmt->execute([$artist]);
    $song = $stmt->fetch(PDO::FETCH_ASSOC);
}
if (!$song) die("題庫空空的，快去採集歌曲吧！");
?>
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>猜歌挑戰</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root { --primary: #6c5ce7; --bg: #f0f2f5; }
        body { font-family: sans-serif; background: var(--bg); text-align: center; padding: 20px; }
        .card { background: white; border-radius: 20px; padding: 30px; max-width: 450px; margin: auto; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .timer-display { font-size: 40px; font-weight: bold; color: var(--primary); margin: 20px 0; }
        input { width: 85%; padding: 15px; border-radius: 12px; border: 2px solid #ddd; font-size: 18px; margin-bottom: 20px; text-align: center; }
        .btn { padding: 15px 25px; border-radius: 12px; border: none; cursor: pointer; font-weight: bold; width: 100%; margin-bottom: 10px; }
        #player { position: absolute; left: -9999px; }
        .options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; display: none; }
    </style>
</head>
<body>
    <div class="card">
        <h3><?= $song['artist'] ?> 猜歌挑戰</h3>
        <div id="player"></div>
        <div class="timer-display" id="displayTime">3s</div>
        <button id="playBtn" class="btn" style="background:var(--primary); color:white; font-size:20px;" onclick="playMusic()">
            <i class="fas fa-play"></i> 點我開始聽歌
        </button>
        <input type="text" id="ansIn" placeholder="輸入歌名...">
        <div style="display:flex; gap:10px;">
            <button class="btn" style="background:#fdcb6e;" onclick="addTime()">+3 秒</button>
            <button class="btn" style="background:#00b894; color:white;" onclick="showOptions()">給選項</button>
        </div>
        <div id="optGrid" class="options-grid"></div>
        <button class="btn" style="background:#ddd; margin-top:20px;" onclick="location.href='index.php'">回大廳</button>
    </div>
    <script src="https://www.youtube.com/iframe_api"></script>
    <script>
        let player, duration = 3, isPlaying = false;
        const songData = <?= json_encode($song) ?>;
        function onYouTubeIframeAPIReady() {
            player = new YT.Player('player', { videoId: songData.yt_id });
        }
        function playMusic() {
            if(isPlaying) return;
            isPlaying = true;
            document.getElementById('playBtn').innerHTML = '<i class="fas fa-volume-up"></i> 播放中...';
            player.seekTo(songData.start_sec);
            player.playVideo();
            let left = duration;
            const timer = setInterval(() => {
                left--;
                document.getElementById('displayTime').innerText = left + "s";
                if(left <= 0) {
                    clearInterval(timer);
                    player.pauseVideo();
                    isPlaying = false;
                    document.getElementById('playBtn').innerHTML = '<i class="fas fa-redo"></i> 再聽一次';
                }
            }, 1000);
        }
        function addTime() { duration += 3; playMusic(); }
        function showOptions() {
            const grid = document.getElementById('optGrid');
            grid.style.display = 'grid';
            const all = (songData.options + ',' + songData.song_name).split(',').sort(() => Math.random() - 0.5);
            grid.innerHTML = all.map(o => `<button class="btn" style="background:#eee" onclick="check('${o}')">${o}</button>`).join('');
        }
        function check(v) {
            const user = v || document.getElementById('ansIn').value;
            if (user.includes(songData.song_name)) { alert("答對了！"); location.reload(); }
            else alert("不對喔！");
        }
    </script>
</body>
</html>
EOD;

    // C. admin_yt_tool.php (真實採集優化版)
    $admin_yt_content = <<<'EOD'
<?php
session_start();
require_once 'configgem.php';
$msg = ""; $db = new PDO("sqlite:quiz.db");
function cleanTitle($t, $a) {
    $p = ["/$a/i","/Official/i","/Video/i","/MV/i","/HD/i","/\(.*\)/","/\[.*\]/","/【.*】/","/-/","/\s+/"];
    return trim(preg_replace($p, ' ', $t));
}
if (isset($_POST['action'])) {
    $artist = $_POST['artist']; $count = (int)$_POST['count'];
    $url = "https://www.googleapis.com/youtube/v3/search?".http_build_query(['part'=>'snippet','q'=>$artist." 歌曲",'type'=>'video','maxResults'=>$count,'order'=>'viewCount','key'=>YT_API_KEY]);
    $data = json_decode(file_get_contents($url), true);
    if (isset($data['items'])) {
        $added = 0;
        foreach ($data['items'] as $item) {
            $name = cleanTitle($item['snippet']['title'], $artist);
            $ins = $db->prepare("INSERT INTO entertainment_songs (artist, song_name, yt_id, start_sec, options) VALUES (?, ?, ?, ?, ?)");
            $ins->execute([$artist, $name, $item['id']['videoId'], rand(60, 100), "暫無選項"]);
            $added++;
        }
        $msg = "✅ 成功匯入 $added 首 $artist 的歌曲！";
    } else { $msg = "❌ API 錯誤，請檢查 Key。"; }
}
?>
<!DOCTYPE html>
<html lang="zh-TW"><head><meta charset="UTF-8"><title>採集器</title><style>body{font-family:sans-serif;text-align:center;padding:50px;background:#f0f2f5;}.box{background:white;padding:30px;border-radius:20px;max-width:400px;margin:auto;box-shadow:0 10px 20px rgba(0,0,0,0.1);}input{width:100%;padding:10px;margin:10px 0;box-sizing:border-box;}button{width:100%;padding:10px;background:#6c5ce7;color:white;border:none;border-radius:10px;cursor:pointer;}</style></head>
<body><div class="box"><h2>🚀 歌手歌曲採集</h2><form method="POST"><input type="hidden" name="action" value="1"><input type="text" name="artist" placeholder="歌手姓名" required><input type="number" name="count" value="10"><button type="submit">開始全自動進補</button></form><p><?=$msg?></p><a href="index.php">回大廳</a></div></body></html>
EOD;

    // D. admin_list.php (管理清單)
    $admin_list_content = <<<'EOD'
<?php
$db = new PDO("sqlite:quiz.db");
if (isset($_GET['del'])) { $db->prepare("DELETE FROM entertainment_songs WHERE id=?")->execute([$_GET['del']]); header("Location:admin_list.php"); }
$songs = $db->query("SELECT * FROM entertainment_songs ORDER BY id DESC")->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html lang="zh-TW"><head><meta charset="UTF-8"><title>管理題庫</title></head>
<body style="font-family:sans-serif;padding:20px;">
    <h2>題庫管理 (共 <?=count($songs)?> 首)</h2>
    <table border="1" style="width:100%; border-collapse:collapse; text-align:center;">
        <tr><th>歌手</th><th>歌名</th><th>操作</th></tr>
        <?php foreach($songs as $s): ?>
        <tr><td><?=$s['artist']?></td><td><?=$s['song_name']?></td><td><a href="?del=<?=$s['id']?>">刪除</a></td></tr>
        <?php endforeach; ?>
    </table>
    <br><a href="index.php">回首頁</a>
</body></html>
EOD;

    // 2. 寫入所有檔案
    file_put_contents('index.php', $index_content);
    file_put_contents('game_song.php', $game_song_content);
    file_put_contents('admin_yt_tool.php', $admin_yt_content);
    file_put_contents('admin_list.php', $admin_list_content);

    echo "✅ index.php 已更新...<br>";
    echo "✅ game_song.php 已部署...<br>";
    echo "✅ admin_yt_tool.php 已部署...<br>";
    echo "✅ admin_list.php 已部署...<br>";
    echo "<h2>🎉 全部搞定！請點擊 <a href='index.php'>回到大廳</a> 開始採集並遊玩。</h2>";

} catch (Exception $e) {
    echo "❌ 發生錯誤：" . $e->getMessage();
}