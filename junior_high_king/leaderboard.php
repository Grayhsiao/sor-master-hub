<?php
session_start();
$db = new PDO('sqlite:education.db');

// 🚩 抓取心算王前 10 名 (以答對總數排序)
$ranks = $db->query("
    SELECT u.name, u.pic, COUNT(s.id) as total 
    FROM users u
    JOIN study_logs s ON u.user_id = s.user_id
    WHERE s.is_correct = 1
    GROUP BY u.user_id
    ORDER BY total DESC
    LIMIT 10
")->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html lang="zh-TW">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>榮譽排行榜</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary: #6c5ce7;
            --gold: #f1c40f;
            --silver: #bdc3c7;
            --bronze: #e67e22;
        }

        body {
            font-family: sans-serif;
            background: #f1f0ff;
            margin: 0;
            padding-bottom: 50px;
        }

        .header {
            background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
            color: white;
            padding: 50px 20px;
            text-align: center;
            border-radius: 0 0 40px 40px;
        }

        .container {
            max-width: 500px;
            margin: -30px auto 0;
            padding: 0 20px;
        }

        .rank-card {
            background: white;
            border-radius: 25px;
            padding: 15px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
        }

        .rank-item {
            display: flex;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #f8f8f8;
        }

        .rank-num {
            width: 40px;
            font-weight: 900;
            font-size: 20px;
            color: #ccc;
        }

        .rank-item:nth-child(1) .rank-num {
            color: var(--gold);
        }

        .rank-item:nth-child(2) .rank-num {
            color: var(--silver);
        }

        .rank-item:nth-child(3) .rank-num {
            color: var(--bronze);
        }

        .avatar {
            width: 45px;
            height: 45px;
            border-radius: 50%;
            margin-right: 15px;
            border: 2px solid #eee;
        }

        .user-name {
            flex: 1;
            font-weight: bold;
            color: #333;
        }

        .user-score {
            font-weight: 900;
            color: var(--primary);
            font-size: 18px;
        }

        .user-score small {
            font-size: 12px;
            color: #999;
            font-weight: normal;
            margin-left: 3px;
        }

        .back-btn {
            display: block;
            text-align: center;
            margin-top: 30px;
            color: var(--primary);
            text-decoration: none;
            font-weight: bold;
        }
    </style>
</head>

<body>

    <div class="header">
        <i class="fas fa-crown"
            style="font-size: 50px; color: rgba(255,255,255,0.3); position: absolute; top: 20px; right: 30px;"></i>
        <h1 style="margin:0;">榮譽排行榜</h1>
        <p>看看誰才是最強學霸！</p>
    </div>

    <div class="container">
        <div class="rank-card">
            <?php if (empty($ranks)): ?>
                <p style="text-align:center; color:#999; padding: 40px 0;">目前尚無數據，快去練習成為第一名！</p>
            <?php else: ?>
                <?php foreach ($ranks as $i => $r): ?>
                    <div class="rank-item">
                        <div class="rank-num"><?= $i + 1 ?></div>
                        <img src="<?= $r['pic'] ?: 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png' ?>" class="avatar">
                        <div class="user-name"><?= $r['name'] ?></div>
                        <div class="user-score"><?= $r['total'] ?><small>題</small></div>
                    </div>
                <?php endforeach; ?>
            <?php endif; ?>
        </div>

        <a href="index.php" class="back-btn"><i class="fas fa-home"></i> 返回學習大廳</a>
    </div>

</body>

</html>