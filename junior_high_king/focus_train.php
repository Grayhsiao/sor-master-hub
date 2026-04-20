<?php
session_start();
if (!isset($_SESSION['user'])) {
    header("Location: index.php");
    exit();
}
$db = new PDO('sqlite:education.db');
$stmt = $db->prepare("SELECT subject FROM study_logs WHERE user_id = ? AND is_correct = 0 GROUP BY subject ORDER BY COUNT(*) DESC LIMIT 1");
$stmt->execute([$_SESSION['user']['id']]);
$weak = $stmt->fetchColumn() ?: "綜合練習";
?>
<!DOCTYPE html>
<html lang="zh-TW">

<head>
    <meta charset="UTF-8">
    <title>弱點特訓</title>
    <style>
        body {
            font-family: sans-serif;
            background: #fff5f5;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }

        .card {
            background: white;
            padding: 40px;
            border-radius: 30px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(255, 118, 117, 0.2);
        }

        .btn {
            background: #ff7675;
            color: white;
            padding: 15px 30px;
            border-radius: 20px;
            text-decoration: none;
            display: inline-block;
            font-weight: bold;
            margin-top: 20px;
        }
    </style>
</head>

<body>
    <div class="card">
        <h2 style="color:#ff7675;">🚀 補強計畫啟動</h2>
        <p>我們來把 <b>「<?= $weak ?>」</b> 練到會！</p>
        <a href="math_game.php" class="btn">開始練習</a><br><br>
        <a href="index.php" style="color:#ccc; text-decoration:none;">回大廳</a>
    </div>
</body>

</html>