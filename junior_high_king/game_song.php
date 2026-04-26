<?php
session_start();
$db = new PDO("sqlite:" . __DIR__ . "/quiz.db");
$artist = $_GET['artist'] ?? 'all';
$interval = 5;
if ($artist === 'all') {
    $song = $db->query("SELECT * FROM entertainment_songs ORDER BY RANDOM() LIMIT 1")->fetch(PDO::FETCH_ASSOC);
} else {
    $stmt = $db->prepare("SELECT * FROM entertainment_songs WHERE artist LIKE ? ORDER BY RANDOM() LIMIT 1");
    $stmt->execute(["%$artist%"]);
    $song = $stmt->fetch(PDO::FETCH_ASSOC);
}
if (!$song)
    die("題庫為空");

$mode = $_GET['mode'] ?? 'default';
$start_sec = (int)($song['start_sec'] ?? 60);

if ($mode === 'intro') {
    $start_sec = 0;
} elseif ($mode === 'random') {
    // 隨機跳轉到 10 到 150 秒之間
    $start_sec = rand(10, 150);
}

// 🚩 清洗 ID
$yt_id = trim($song['yt_id']);
if (preg_match('%(?:youtube(?:-nocookie)?\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^"&?/ ]{11})%i', $yt_id, $m)) {
    $yt_id = $m[1];
} else {
    $yt_id = substr($yt_id, 0, 11);
}

// 選項補齊
$optStmt = $db->prepare("SELECT song_name FROM entertainment_songs WHERE artist LIKE ? AND song_name != ? AND song_name != '暫無' ORDER BY RANDOM() LIMIT 3");
$optStmt->execute(["%" . $song['artist'] . "%", $song['song_name']]);
$opts = $optStmt->fetchAll(PDO::FETCH_COLUMN);
if (count($opts) < 3) {
    $fill = $db->prepare("SELECT song_name FROM entertainment_songs WHERE song_name != ? ORDER BY RANDOM() LIMIT " . (3 - count($opts)));
    $fill->execute([$song['song_name']]);
    $opts = array_merge($opts, $fill->fetchAll(PDO::FETCH_COLUMN));
}
$allOpts = $opts;
$allOpts[] = $song['song_name'];
shuffle($allOpts);
$allOpts[] = "以上皆非 (修正)";
?>
<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <style>
        body {
            font-family: -apple-system, sans-serif;
            background: #000;
            color: white;
            text-align: center;
            margin: 0;
            padding: 10px;
            overflow: hidden;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
        }

        .img-container {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 55vh;
            z-index: 1;
            background: #111;
            overflow: hidden;
        }

        .artist-bg {
            width: 100%;
            height: 100%;
            object-fit: cover;
            opacity: 0.6;
            mask-image: linear-gradient(to bottom, #000 70%, transparent 100%);
            -webkit-mask-image: linear-gradient(to bottom, #000 70%, transparent 100%);
        }

        .nav-top {
            display: flex;
            justify-content: space-between;
            z-index: 500;
            position: relative;
            padding: 5px 10px;
        }

        .nav-top a {
            color: #fff;
            text-decoration: none;
            font-size: 14px;
            background: rgba(0, 0, 0, 0.6);
            padding: 8px 15px;
            border-radius: 10px;
            font-weight: bold;
        }

        .main-disc {
            width: 130px;
            height: 130px;
            border-radius: 50%;
            background: #6c5ce7;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 50px rgba(108, 92, 231, 0.8);
            cursor: pointer;
            z-index: 100;
            margin: 10px auto;
        }

        #speechBubble {
            background: rgba(0, 0, 0, 0.9);
            color: #55efc4;
            padding: 15px;
            border-radius: 20px;
            min-height: 60px;
            width: 90%;
            margin: 10px auto;
            border: 3px solid #444;
            font-size: 26px;
            font-weight: 900;
            z-index: 100;
            position: relative;
            visibility: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .listening {
            border-color: #55efc4 !important;
            box-shadow: 0 0 20px rgba(85, 239, 196, 0.5);
        }

        .opt-btn {
            padding: 18px;
            border-radius: 18px;
            border: none;
            width: 100%;
            margin-bottom: 10px;
            font-weight: bold;
            font-size: 20px;
            cursor: pointer;
            background: rgba(26, 26, 26, 0.95);
            color: white;
            border: 1px solid #444;
        }

        #fb-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: none;
            z-index: 2000;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            background: rgba(0, 0, 0, 0.9);
        }

        /* 🚩 修正彈窗樣式 */
        .modal-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.85); display: none; z-index: 3000;
            align-items: center; justify-content: center;
        }
        .modal-box {
            background: #222; padding: 30px; border-radius: 25px; width: 85%; max-width: 400px;
            border: 2px solid #6c5ce7; text-align: center;
        }
        .modal-input {
            width: 90%; padding: 15px; border-radius: 12px; border: 1px solid #444;
            background: #111; color: white; font-size: 18px; margin: 20px 0;
        }
        .modal-btn {
            padding: 12px 20px; border-radius: 10px; border: none; font-weight: bold; cursor: pointer; margin: 5px;
        }
        .debug-info {
            color: #888;
            font-size: 11px;
            margin-top: 5px;
            font-family: monospace;
        }
    </style>
</head>

<body>

    <div id="fb-overlay"><i id="fb-icon" style="font-size:120px;"></i>
        <div id="fb-text" style="font-size:32px;font-weight:900;margin-top:20px;"></div>
    </div>

    <!-- 🚩 修正彈窗 -->
    <div id="fixModal" class="modal-overlay">
        <div class="modal-box">
            <h3 style="margin:0;">🔧 修正題目內容</h3>
            <p style="font-size:12px;color:#aaa;">ID: <?= $song['id'] ?></p>
            <input type="text" id="fixNameInput" class="modal-input" placeholder="請輸入正確歌名">
            <div style="display:flex; flex-direction:column; gap:10px;">
                <button class="modal-btn" style="background:#00b894;color:white;" onclick="submitFix()">確定修正</button>
                <button class="modal-btn" style="background:#0984e3;color:white;" onclick="aiFindTitle()">🤖 AI 幫我找答案</button>
                <button class="modal-btn" style="background:#444;color:white;" onclick="closeModal()">取消</button>
            </div>
        </div>
    </div>

    <div class="img-container">
        <img id="bg-img" src="https://i.ytimg.com/vi/<?= $yt_id ?>/hqdefault.jpg" class="artist-bg"
            onerror="this.src='https://i.ytimg.com/vi/<?= $yt_id ?>/mqdefault.jpg'">
    </div>

    <div class="nav-top">
        <a href="song_lobby.php">回大廳</a>
        <div style="font-size:16px;font-weight:bold;">得分：<span id="scoreText" style="color:#fdcb6e;">100</span></div>
        <a href="index.php">回主廳</a>
    </div>

    <div class="play-zone" style="z-index:100;">
        <div class="main-disc" id="playBtn" onclick="handleChallenge()">
            <i class="fas fa-play" id="mainIcon" style="font-size:55px;"></i>
            <div style="font-size:14px;font-weight:bold;" id="mainLabel">開始挑戰</div>
        </div>

        <div style="font-weight:bold; color:#ddd; margin-top:5px;"><?= $song['artist'] ?></div>
        <div class="debug-info">
            DB_ID: <?= $song['id'] ?> | YT: <?= $yt_id ?>
        </div>
        <div style="color:#aaa; font-size:11px;">已聽：<span id="timeDisplay">0</span>s</div>
    </div>

    <div id="speechBubble">...</div>

    <div id="optGrid">
        <div style="display:flex;gap:10px;margin-bottom:10px;">
            <button class="opt-btn" style="background:#0984e3;border:none;font-size:16px;"
                onclick="playFull()">聽整首</button>
            <button id="yieldBtn" class="opt-btn" style="background:#444;border:none;font-size:16px;"
                onclick="revealOptions()">看選項</button>
            <button class="opt-btn" style="background:#e17055;border:none;font-size:16px;width:120px;"
                onclick="reportBug()"><i class="fas fa-exclamation-triangle"></i> 回報</button>
        </div>
        <div id="realOptions" style="display:none;">
            <?php foreach ($allOpts as $o): ?><button class="opt-btn"
                    onclick="check('<?= addslashes($o) ?>')"><?= $o ?></button><?php endforeach; ?>
        </div>
    </div>

    <div id="player" style="position:absolute;left:-9999px;"></div>

    <script src="https://www.youtube.com/iframe_api"></script>
    <script>
        let player, listenCount = 0, score = 100, isPlaying = false, isWakedUp = false;
        let recognition;
        let isCorrectAnswered = false;
        const correct = "<?= addslashes($song['song_name']) ?>";

        function initSpeech() {
            const SDK = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SDK) return;
            recognition = new SDK();
            recognition.lang = 'zh-TW';
            recognition.interimResults = true;
            recognition.continuous = true;

            recognition.onresult = (e) => {
                if (isPlaying) return;

                let transcript = "";
                for (let i = e.resultIndex; i < e.results.length; i++) {
                    transcript += e.results[i][0].transcript;
                }

                const bubble = document.getElementById('speechBubble');
                bubble.innerText = transcript;
                bubble.style.visibility = 'visible';
                bubble.classList.add('listening');

                if (fuzzyMatch(transcript, correct)) {
                    isCorrectAnswered = true;
                    recognition.stop();
                    check(correct);
                }
            };
        }

        function onYouTubeIframeAPIReady() {
            player = new YT.Player('player', { videoId: '<?= $yt_id ?>', playerVars: { 'autoplay': 0, 'controls': 0, 'mute': 0, 'playsinline': 1 } });
            initSpeech();
        }

        function handleChallenge() {
            if (isPlaying || listenCount >= 5) return;
            try { recognition.start(); } catch (e) { }

            isPlaying = true;
            document.getElementById('mainIcon').className = "fas fa-music";
            document.getElementById('mainLabel').innerText = "播放中...";

            if (!isWakedUp) { player.playVideo(); player.setVolume(100); isWakedUp = true; }
            player.seekTo(<?= $start_sec ?> + (listenCount * 5), true);
            player.playVideo();

            listenCount++;
            if (listenCount > 1) score -= 20;
            document.getElementById('scoreText').innerText = score;
            document.getElementById('timeDisplay').innerText = listenCount * 5;

            document.getElementById('speechBubble').style.visibility = 'hidden';

            setTimeout(() => {
                player.pauseVideo();
                isPlaying = false;
                document.getElementById('mainIcon').className = "fas fa-microphone-alt";
                document.getElementById('mainLabel').innerText = "🎙️ 現在請說！";
                document.getElementById('mainIcon').style.color = "#55efc4";
                document.getElementById('speechBubble').innerText = "🎙️ 正在聽...";
                document.getElementById('speechBubble').style.visibility = 'visible';
            }, 5000);
        }

        function fuzzyMatch(spoken, target) {
            const clean = (s) => s.toString().replace(/[^\w\u4E00-\u9FA5]/g, "").toLowerCase();
            const s = clean(spoken);
            const t = clean(target);
            if (!s || !t) return false;
            return s.includes(t) || t.includes(s);
        }

        function revealOptions() { document.getElementById('realOptions').style.display = 'block'; document.getElementById('yieldBtn').style.display = 'none'; }

        function reportBug() {
            if (confirm("⚠️ 確定要將這首歌標記為「題目與答案不符」嗎？\n管理員之後會進行檢查。")) {
                fetch('api_fix_song.php', { method: 'POST', body: new URLSearchParams({ id: '<?= $song['id'] ?>', action: 'mark' }) })
                    .then(() => { alert('已回報！謝謝你的幫助。'); location.reload(); });
            }
        }

        function closeModal() { document.getElementById('fixModal').style.display = 'none'; }
        
        function submitFix() {
            let n = document.getElementById('fixNameInput').value.trim();
            if (n === "") {
                reportBug();
            } else {
                fetch('api_fix_song.php', { method: 'POST', body: new URLSearchParams({ id: '<?= $song['id'] ?>', name: n, action: 'fix' }) })
                    .then(() => { alert('已修正為：' + n); location.reload(); });
            }
        }

        function aiFindTitle() {
            const btn = event.target;
            btn.innerText = "🔍 AI 搜尋中...";
            btn.disabled = true;
            
            fetch('api_ai_song.php?yt_id=<?= $yt_id ?>')
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('fixNameInput').value = data.clean_title;
                        alert("🤖 AI 找到可能的歌名：\n" + data.title + "\n\n已為您填入清洗後的名稱。");
                    } else {
                        alert("❌ AI 找不到這首歌的資訊。");
                    }
                })
                .finally(() => {
                    btn.innerText = "🤖 AI 幫我找答案";
                    btn.disabled = false;
                });
        }

        function check(ans) {
            if (ans.includes("以上皆非")) {
                document.getElementById('fixModal').style.display = 'flex';
                return;
            }

            const ov = document.getElementById('fb-overlay');
            ov.style.display = 'flex';

            if (fuzzyMatch(ans, correct)) {
                isCorrectAnswered = true;
                document.getElementById('fb-icon').className = "fas fa-check-circle";
                document.getElementById('fb-icon').style.color = "#00b894";
                document.getElementById('fb-text').innerText = "答對了！ +" + score + "分";
                confetti({ particleCount: 200, spread: 100, origin: { y: 0.6 } });
                setTimeout(() => { location.href = "game_song.php?artist=<?= urlencode($artist) ?>&r=" + Math.random(); }, 1500);
            } else {
                document.getElementById('fb-icon').className = "fas fa-times-circle";
                document.getElementById('fb-icon').style.color = "#ff7675";
                document.getElementById('fb-text').innerText = "不對喔！";
                setTimeout(() => { ov.style.display = 'none'; }, 800);
            }
        }
        function playFull() { player.setVolume(100); player.playVideo(); }
    </script>
</body>

</html>