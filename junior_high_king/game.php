<?php
session_start();
$subj = $_GET['subject'] ?? '國文';
$db = new PDO('sqlite:quiz.db');
$stmt = $db->prepare("SELECT * FROM questions WHERE subject = ? ORDER BY RANDOM() LIMIT 10");
$stmt->execute([$subj]);
$qs = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            font-family: sans-serif;
            background: #f0f2f5;
            margin: 0;
            padding: 20px;
            text-align: center;
        }

        .nav-top {
            display: flex;
            justify-content: space-between;
            max-width: 500px;
            margin: 0 auto 20px;
        }

        .nav-top a {
            text-decoration: none;
            color: #6c5ce7;
            font-weight: bold;
            font-size: 14px;
            background: white;
            padding: 8px 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        }

        .card {
            background: white;
            padding: 30px;
            border-radius: 30px;
            max-width: 500px;
            margin: auto;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
        }

        .opt-btn {
            width: 100%;
            padding: 20px;
            margin: 10px 0;
            border-radius: 15px;
            border: 2px solid #eee;
            background: white;
            font-size: 20px;
            font-weight: bold;
            text-align: left;
        }

        .correct {
            background: #55efc4 !important;
            border-color: #00b894 !important;
        }

        .wrong {
            background: #fab1a0 !important;
            border-color: #ff7675 !important;
        }

        #ana-box {
            display: none;
            margin-top: 20px;
            padding: 20px;
            background: #fff9db;
            border-radius: 20px;
            text-align: left;
            border-left: 5px solid #f1c40f;
        }
    </style>
</head>

<body>
    <div class="nav-top">
        <a href="quiz_lobby.php"><i class="fas fa-chevron-left"></i> 回題庫</a>
        <a href="index.php"><i class="fas fa-home"></i> 回主大廳</a>
    </div>
    <div class="card">
        <div id="q-text" style="font-size:24px;font-weight:bold;margin-bottom:20px;text-align:left;"></div>
        <div id="opt-area"></div>
        <div id="ana-box">
            <b>💡 解析說明：</b>
            <div id="ana-text" style="margin:10px 0;line-height:1.6;"></div>
            <button onclick="nextQ()"
                style="width:100%;padding:18px;background:#6c5ce7;color:white;border:none;border-radius:15px;font-weight:bold;font-size:18px;">下一題</button>
        </div>
    </div>
    <script>
        const qs = <?= json_encode($qs) ?>; let idx = 0;
        function load() {
            const q = qs[idx]; document.getElementById('q-text').innerText = (idx + 1) + ". " + q.question;
            const area = document.getElementById('opt-area'); area.innerHTML = '';
            document.getElementById('ana-box').style.display = 'none';
            ['a', 'b', 'c', 'd'].forEach(k => {
                const b = document.createElement('button'); b.className = 'opt-btn'; b.id = 'btn-' + k;
                b.innerText = k.toUpperCase() + ". " + q['option_' + k];
                b.onclick = () => {
                    document.querySelectorAll('.opt-btn').forEach(btn => btn.onclick = null);
                    document.getElementById('btn-' + q.answer.toLowerCase()).classList.add('correct');
                    if (k.toUpperCase() !== q.answer.toUpperCase()) document.getElementById('btn-' + k).classList.add('wrong');
                    document.getElementById('ana-text').innerText = q.analysis || "記好正確答案喔！";
                    document.getElementById('ana-box').style.display = 'block';
                };
                area.appendChild(b);
            });
        }
        function nextQ() { idx++; if (idx < qs.length) load(); else location.href = 'quiz_lobby.php'; }
        load();
    </script>
</body>

</html>