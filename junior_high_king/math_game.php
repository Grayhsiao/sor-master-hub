<?php
session_start();
$conf = $_SESSION['math_config'] ?? ['ops' => ['+'], 'ranges' => ['10'], 'total_q' => 10, 'timer' => 60];
?>
<!DOCTYPE html>
<html lang="zh-TW">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>語音心算王 - 終極修復</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            font-family: sans-serif;
            background: #000;
            color: white;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            overflow: hidden;
        }

        #equation {
            font-size: 110px;
            font-weight: 900;
            margin: 20px 0;
            min-height: 180px;
            display: flex;
            align-items: center;
            text-align: center;
            color: #fff;
        }

        #msg {
            color: #6c5ce7;
            font-weight: bold;
            font-size: 26px;
            min-height: 45px;
            background: rgba(255, 255, 255, 0.05);
            padding: 8px 25px;
            border-radius: 20px;
            border: 1px solid rgba(108, 92, 231, 0.3);
        }

        .hud {
            position: fixed;
            top: 30px;
            width: 85%;
            display: flex;
            justify-content: space-between;
            font-size: 24px;
            font-weight: bold;
        }

        #overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: #000;
            z-index: 3000;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            cursor: pointer;
        }
    </style>
</head>

<body>

    <div id="overlay" onclick="startApp()">
        <i class="fas fa-microphone-alt" style="font-size: 80px; color: #6c5ce7; margin-bottom: 20px;"></i>
        <h2>點擊開始搶答</h2>
    </div>

    <div class="hud">
        <div style="color: #ff7675;">⏳ <span id="timer"><?= $conf['timer'] ?></span></div>
        <div style="color: #6c5ce7;">🎯 <span id="idx">0</span>/<?= $conf['total_q'] ?></div>
    </div>

    <div id="equation">---</div>
    <div id="msg">準備中...</div>

    <script>
        let config = <?= json_encode($conf) ?>;
        let currentAns = "", count = 0, timeLeft = config.timer, timerInt;
        let recognition, synth = window.speechSynthesis;
        let isListening = false;

        function smartParse(rawStr) {
            if (!rawStr) return "";
            // 🚩 核心：只抓取最後一個空格後的字串 (解決 30 30 30)
            let parts = rawStr.trim().split(/[\s,]+/);
            let str = parts[parts.length - 1];

            str = str.replace(/[是|正是|等於|答案是|個|喔|啦|的|了|阿|我想想|應該是]/g, "").replace(/點/g, ".");
            let isNeg = /負|減|欠|-/.test(str); str = str.replace(/[負減欠-]/g, "");

            const dict = { "零": 0, "一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "久": 9, "十": 10, "百": 100 };

            let numMatch = str.match(/\d+(\.\d+)?/g);
            if (numMatch) return (isNeg ? "-" : "") + numMatch[numMatch.length - 1];

            // 🚩 國字拼接 (五四 = 54)
            let s = "";
            for (let char of str) { if (dict[char] !== undefined) s += dict[char].toString(); }
            if (s === "") return "";
            let finalNum = parseInt(s);
            if (s.startsWith("10") && s.length > 2) finalNum = 10 + parseInt(s.substring(2));
            return (isNeg ? "-" : "") + finalNum;
        }

        function startApp() {
            document.getElementById('overlay').style.display = 'none';
            initSpeech();
            timerInt = setInterval(() => {
                timeLeft--; document.getElementById('timer').innerText = timeLeft;
                if (timeLeft <= 0) end("挑戰結束！");
            }, 1000);
            next();
        }

        function initSpeech() {
            const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new Speech(); recognition.lang = 'zh-TW'; recognition.continuous = true; recognition.interimResults = true;
            recognition.onresult = (e) => {
                if (!isListening) return;
                let transcript = "";
                for (let i = e.resultIndex; i < e.results.length; i++) transcript = e.results[i][0].transcript;
                if (!transcript) return;
                document.getElementById('msg').innerText = transcript;
                if (smartParse(transcript) == currentAns) { isListening = false; synth.cancel(); win(); }
            };
            recognition.onend = () => { if (timeLeft > 0) try { recognition.start(); } catch (e) { } };
            recognition.start();
        }

        function next() {
            if (count >= config.total_q) return end("通關！");
            count++; document.getElementById('idx').innerText = count;
            let ops = config.ops, op = ops[Math.floor(Math.random() * ops.length)];
            let max = config.ranges.includes('100') ? 100 : 10;
            let allowNeg = config.ranges.includes('neg');
            let n1 = Math.floor(Math.random() * max) + 1, n2 = Math.floor(Math.random() * max) + 1;
            if (allowNeg) {
                let m = Math.floor(Math.random() * 3);
                if (m === 0) n1 *= -1; else if (m === 1) n2 *= -1; else { n1 *= -1; n2 *= -1; }
            }
            let tts = "", html = "";
            if (op === '+') { currentAns = n1 + n2; html = `${n1} + ${n2}`; tts = `${n1}加${n2}`; }
            else if (op === '-') { currentAns = n1 - n2; html = `${n1} - ${n2}`; tts = `${n1}減${n2}`; }
            else if (op === '*') { currentAns = n1 * n2; html = `${n1} × ${n2}`; tts = `${n1}乘${n2}`; }
            else if (op === '/') { n2 = Math.floor(Math.random() * 9) + 1; currentAns = Math.floor(Math.random() * max / 10) + 1; n1 = n2 * currentAns; html = `${n1} ÷ ${n2}`; tts = `${n1}除以${n2}`; }

            isListening = false;
            document.getElementById('equation').innerText = html;
            synth.cancel();
            let u = new SpeechSynthesisUtterance(tts.toString().replace(/-/g, "負"));
            u.lang = 'zh-TW'; u.rate = 1.6; synth.speak(u);
            setTimeout(() => { isListening = true; }, 50);
        }

        function win() {
            document.getElementById('equation').style.color = "#00b894";
            setTimeout(() => { document.getElementById('equation').style.color = "white"; next(); }, 300);
        }

        function end(m) { clearInterval(timerInt); alert(m); location.href = 'index.php'; }
    </script>
</body>

</html>