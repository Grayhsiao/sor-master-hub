<?php
session_start();
$db = new PDO("sqlite:" . __DIR__ . "/quiz.db");
// 批量更新開始時間與挑戰間隔
if (isset($_POST['batch_update'])) {
    $ids = implode(',', array_map('intval', $_POST['selected_ids']));
    $sec = intval($_POST['batch_sec']);
    $db->exec("UPDATE entertainment_songs SET start_sec = $sec WHERE id IN ($ids)");
}
$songs = $db->query("SELECT * FROM entertainment_songs ORDER BY id DESC")->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8">
    <title>管理歌曲庫</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            font-family: sans-serif;
            background: #f4f7f6;
            padding: 20px;
        }

        .batch-bar {
            background: #6c5ce7;
            color: white;
            padding: 20px;
            border-radius: 20px;
            max-width: 800px;
            margin: 0 auto 20px;
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .row {
            background: white;
            padding: 15px;
            border-radius: 15px;
            max-width: 800px;
            margin: 10px auto;
            display: flex;
            align-items: center;
            gap: 15px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
        }

        .btn-white {
            background: white;
            color: #6c5ce7;
            border: none;
            padding: 10px 20px;
            border-radius: 10px;
            font-weight: bold;
            cursor: pointer;
        }
    </style>
</head>

<body>
    <form method="POST">
        <div class="batch-bar">
            <input type="checkbox"
                onclick="document.querySelectorAll('.item-check').forEach(c=>c.checked=this.checked)"> 全選
            <span>設定選中歌曲開始秒數：</span>
            <input type="number" name="batch_sec" value="60" style="width:60px;">
            <button name="batch_update" class="btn-white">批量儲存</button>
            <a href="song_lobby.php" style="color:white;text-decoration:none;margin-left:auto;">回大廳</a>
        </div>

        <?php foreach ($songs as $s): ?>
            <div class="row">
                <input type="checkbox" name="selected_ids[]" value="<?= $s['id'] ?>" class="item-check">
                <img src="<?= $s['thumbnail'] ?>" style="width:50px;height:50px;border-radius:8px;">
                <div style="flex-grow:1;">
                    <b><?= $s['artist'] ?></b> - <?= $s['song_name'] ?>
                    <?php if ($s['is_buggy']): ?>
                        <span
                            style="background:#ff7675;color:white;padding:2px 8px;border-radius:5px;font-size:12px;margin-left:10px;">⚠️
                            有人回報有誤</span>
                    <?php endif; ?>
                    <div style="color:#888;font-size:12px;">目前開始：<?= $s['start_sec'] ?>s</div>
                </div>
            </div>
        <?php endforeach; ?>
    </form>
</body>

</html>