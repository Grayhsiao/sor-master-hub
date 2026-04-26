<?php
session_start();
$db = new PDO("sqlite:" . __DIR__ . "/quiz.db");
$artists = $db->query("SELECT artist, COUNT(*) as count FROM entertainment_songs GROUP BY artist")->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>猜歌模式</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            font-family: sans-serif;
            background: #121212;
            color: white;
            text-align: center;
            padding: 20px;
        }

        .mode-selector {
            background: #1e1e1e; padding: 10px; border-radius: 15px;
            display: inline-flex; gap: 5px; margin-bottom: 20px;
            border: 1px solid #333;
        }
        .mode-btn {
            padding: 8px 15px; border-radius: 10px; text-decoration: none;
            color: #888; font-size: 14px; font-weight: bold;
        }
        .mode-btn.active {
            background: #6c5ce7; color: white;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            max-width: 500px;
            margin: 30px auto;
        }

        .btn {
            background: #1e1e1e;
            padding: 25px;
            border-radius: 25px;
            text-decoration: none;
            color: white;
            border: 1px solid #333;
            font-weight: bold;
            font-size: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .brawl {
            grid-column: span 2;
            background: linear-gradient(135deg, #6c5ce7, #a29bfe);
            padding: 40px;
            font-size: 26px;
        }

        .admin-cog {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: #333;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            text-decoration: none;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5);
        }
    </style>
</head>

<body>
    <h1>🎵 猜歌挑戰大廳</h1>

    <?php $curr_mode = $_GET['mode'] ?? 'default'; ?>
    <div class="mode-selector">
        <a href="?mode=default" class="mode-btn <?= $curr_mode == 'default' ? 'active' : '' ?>">預設 (副歌)</a>
        <a href="?mode=intro" class="mode-btn <?= $curr_mode == 'intro' ? 'active' : '' ?>">挑戰 (前奏)</a>
        <a href="?mode=random" class="mode-btn <?= $curr_mode == 'random' ? 'active' : '' ?>">隨機 (地獄)</a>
    </div>

    <div class="grid">
        <a href="game_song.php?artist=all&mode=<?= $curr_mode ?>" class="btn brawl"><i class="fas fa-fire"></i> 猜歌大亂鬥</a>
        <?php foreach ($artists as $a):
            if (!$a['artist'])
                continue; ?>
            <a href="game_song.php?artist=<?= urlencode($a['artist']) ?>&mode=<?= $curr_mode ?>" class="btn">
                <i class="fas fa-microphone-alt" style="color:#6c5ce7;margin-bottom:10px;"></i>
                <?= $a['artist'] ?><br><span style="font-size:14px;color:#666;"><?= $a['count'] ?> 首歌</span>
            </a>
        <?php endforeach; ?>
    </div>
    <a href="admin_list_song.php" class="admin-cog"><i class="fas fa-cog"></i></a>
</body>

</html>