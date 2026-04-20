<?php
// 🚩 核心：偵測 LINE 並強迫跳出到外部瀏覽器
$ua = $_SERVER['HTTP_USER_AGENT'];
if (strpos($ua, 'Line') !== false) {
    // 檢查網址是否已經帶有跳轉參數，避免無限循環
    if (!isset($_GET['openExternalBrowser'])) {
        $url = (isset($_SERVER['HTTPS']) ? "https" : "http") . "://$_SERVER[HTTP_HOST]$_SERVER[REQUEST_URI]";
        $separator = (parse_url($url, PHP_URL_QUERY) == NULL) ? '?' : '&';
        header('Location: ' . $url . $separator . 'openExternalBrowser=1');
        exit;
    }
}
?>
<!DOCTYPE html>
<html lang="zh-TW">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>JUNIOR HIGH KING - 主廳</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            font-family: sans-serif;
            background: #f0f2f5;
            margin: 0;
            padding: 20px;
            text-align: center;
        }

        .hero {
            background: linear-gradient(135deg, #6c5ce7, #a29bfe);
            color: white;
            padding: 40px 20px;
            border-radius: 0 0 40px 40px;
            margin: -20px -20px 30px;
        }

        .nav-card {
            background: white;
            border-radius: 25px;
            padding: 25px;
            margin: 15px auto;
            max-width: 450px;
            display: flex;
            align-items: center;
            text-decoration: none;
            color: #333;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
        }

        .icon {
            width: 65px;
            height: 65px;
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            margin-right: 20px;
            font-size: 28px;
        }
    </style>
</head>

<body>
    <div class="hero">
        <h1>🚀 JUNIOR HIGH KING</h1>
    </div>

    <a href="math_game.php" class="nav-card">
        <div class="icon" style="background:#6c5ce7;"><i class="fas fa-calculator"></i></div>
        <div style="text-align:left;">
            <h3>語音心算挑戰</h3>
            <p style="margin:5px 0 0; color:#888; font-size:14px;">麥克風權限：已啟用</p>
        </div>
    </a>
    <a href="song_lobby.php" class="nav-card">
        <div class="icon" style="background:#ff7675;"><i class="fas fa-music"></i></div>
        <div style="text-align:left;">
            <h3>猜歌特訓 V26</h3>
            <p style="margin:5px 0 0; color:#888; font-size:14px;">支援自動跳題、高清圖片</p>
        </div>
    </a>
    <a href="quiz_lobby.php" class="nav-card">
        <div class="icon" style="background:#00b894;"><i class="fas fa-book"></i></div>
        <div style="text-align:left;">
            <h3>全科學科挑戰</h3>
            <p style="margin:5px 0 0; color:#888; font-size:14px;">不論對錯必出解析</p>
        </div>
    </a>
</body>

</html>