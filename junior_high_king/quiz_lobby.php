<?php session_start();
$db = new PDO('sqlite:quiz.db');
$subjects = $db->query("SELECT subject, COUNT(*) as total FROM questions GROUP BY subject")->fetchAll(PDO::FETCH_ASSOC); ?>
<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>學科大廳</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            font-family: sans-serif;
            background: #f0f2f5;
            margin: 0;
            padding: 20px;
            text-align: center;
        }

        .nav-btns {
            display: flex;
            justify-content: flex-start;
            margin-bottom: 20px;
        }

        .nav-btns a {
            color: #6c5ce7;
            text-decoration: none;
            font-weight: bold;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            max-width: 500px;
            margin: auto;
        }

        .btn {
            background: white;
            padding: 30px 10px;
            border-radius: 25px;
            text-decoration: none;
            color: #333;
            font-weight: bold;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
            display: flex;
            flex-direction: column;
            align-items: center;
        }
    </style>
</head>

<body>
    <div class="nav-btns"><a href="index.php"><i class="fas fa-home"></i> 回主廳首頁</a></div>
    <h1>📚 學科題庫</h1>
    <div class="grid">
        <?php foreach ($subjects as $s): ?>
            <a href="game.php?subject=<?= urlencode($s['subject']) ?>" class="btn"><i class="fas fa-book"
                    style="color:#6c5ce7;font-size:30px;margin-bottom:10px;"></i><?= $s['subject'] ?></a>
        <?php endforeach; ?>
    </div>
</body>

</html>