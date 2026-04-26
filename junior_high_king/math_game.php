<?php
session_start();
$config_file = 'math_settings.json';
if (file_exists($config_file)) {
    $conf = json_decode(file_get_contents($config_file), true);
} else {
    $conf = ['ops' => ['+', '-'], 'ranges' => ['100'], 'total_q' => 10, 'timer' => 60, 'allow_neg' => false];
}
?>
<!DOCTYPE html>
<html lang="zh-TW">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>CYBER MATH KING - 語音心算王</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Noto+Sans+TC:wght@400;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --neon-purple: #bc13fe;
            --neon-blue: #00f3ff;
            --neon-green: #39ff14;
            --neon-red: #ff3131;
            --bg-dark: #0a0a12;
        }

        body {
            font-family: 'Orbitron', 'Noto Sans TC', sans-serif;
            background-color: var(--bg-dark);
            background-image: 
                linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%),
                linear-gradient(90deg, rgba(188, 19, 254, 0.05) 1px, transparent 1px),
                linear-gradient(rgba(188, 19, 254, 0.05) 1px, transparent 1px);
            background-size: 100% 4px, 40px 40px, 40px 40px;
            color: white;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            overflow: hidden;
            position: relative;
        }

        /* 掃描線效果 */
        body::after {
            content: " ";
            display: block;
            position: absolute;
            top: 0; left: 0; bottom: 0; right: 0;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.1) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
            z-index: 2;
            background-size: 100% 2px, 3px 100%;
            pointer-events: none;
        }

        #equation {
            font-size: clamp(60px, 15vw, 150px);
            font-weight: 900;
            margin: 20px 0;
            text-shadow: 0 0 10px var(--neon-blue), 0 0 20px var(--neon-blue);
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            z-index: 5;
        }

        #msg {
            font-size: 20px;
            min-height: 50px;
            color: var(--neon-green);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 20px;
            padding: 10px 30px;
            border: 1px solid var(--neon-green);
            border-radius: 5px;
            background: rgba(57, 255, 20, 0.1);
            box-shadow: inset 0 0 10px var(--neon-green);
            z-index: 5;
            text-align: center;
        }

        .hud {
            position: fixed;
            top: 20px;
            width: 90%;
            display: flex;
            justify-content: space-between;
            z-index: 10;
        }

        .hud-item {
            background: rgba(0, 0, 0, 0.8);
            padding: 8px 15px;
            border-left: 4px solid var(--neon-purple);
            font-weight: bold;
            font-size: 18px;
        }

        #overlay {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(10, 10, 18, 0.98);
            z-index: 3000;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            cursor: pointer;
        }

        .btn-start {
            padding: 20px 40px;
            font-size: 24px;
            background: transparent;
            color: var(--neon-purple);
            border: 2px solid var(--neon-purple);
            box-shadow: 0 0 15px var(--neon-purple);
            text-transform: uppercase;
            cursor: pointer;
            font-family: 'Orbitron', sans-serif;
        }

        .combo-badge {
            position: absolute;
            right: 5%;
            top: 80px;
            font-size: 32px;
            font-weight: bold;
            color: var(--neon-red);
            text-shadow: 0 0 10px var(--neon-red);
            animation: pulse 0.5s infinite;
            display: none;
            z-index: 5;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }

        .correct-flash {
            animation: flashGreen 0.4s ease-out;
        }

        @keyframes flashGreen {
            0% { background-color: transparent; }
            50% { background-color: rgba(57, 255, 20, 0.2); }
            100% { background-color: transparent; }
        }
    </style>
</head>

<body class="">

    <div id="overlay" onclick="startApp()">
        <div class="btn-start"><i class="fas fa-microchip"></i> START CORE</div>
        <p style="color: var(--neon-blue); margin-top: 20px; font-size: 14px;">WAKE UP THE SPEECH SYSTEM</p>
    </div>

    <div class="hud">
        <div class="hud-item" style="border-color: var(--neon-red);">T: <span id="timer"><?= $conf['timer'] ?></span></div>
        <div class="hud-item" style="border-color: var(--neon-purple);">S: <span id="scoreDisplay">0</span></div>
        <div class="hud-item" style="border-color: var(--neon-blue);">Q: <span id="idx">0</span>/<?= $conf['total_q'] ?></div>
    </div>

    <div id="combo" class="combo-badge">COMBO X1</div>

    <div id="equation">INIT</div>
    <div id="msg">WAITING FOR COMMAND...</div>

    <script>
        let config = <?= json_encode($conf) ?>;
        let currentAns = "", count = 0, score = 0, combo = 0, timeLeft = config.timer, timerInt;
        let recognition, synth = window.speechSynthesis;
        let isListening = false;

        // 🚩 強化版數字解析：支援多種中文數字表達
        function smartParse(rawStr) {
            if (!rawStr) return "";
            let parts = rawStr.trim().split(/[\s,]+/);
            let str = parts[parts.length - 1];

            str = str.replace(/[是|正是|等於|答案是|個|喔|啦|的|了|阿|我想想|應該是|大概]/g, "").replace(/點/g, ".");
            let isNeg = /負|減|欠|-/.test(str);
            str = str.replace(/[負減欠-]/g, "");

            // 阿拉伯數字優先
            let numMatch = str.match(/\d+(\.\d+)?/g);
            if (numMatch) return (isNeg ? "-" : "") + numMatch[numMatch.length - 1];

            const dict = { "零": 0, "一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10 };
            
            let val = 0;
            if (str.length === 1 && dict[str[0]] !== undefined) {
                val = dict[str[0]];
            } else if (str.length === 2) {
                if (str[0] === "十") val = 10 + dict[str[1]];
                else if (str[1] === "十") val = dict[str[0]] * 10;
                else if (dict[str[0]] !== undefined && dict[str[1]] !== undefined) val = dict[str[0]] * 10 + dict[str[1]]; // 如 "二五"
            } else if (str.length === 3) {
                if (str[1] === "十") val = dict[str[0]] * 10 + dict[str[2]];
            }

            if (val === 0) {
                let s = "";
                for (let char of str) { if (dict[char] !== undefined) s += dict[char].toString(); }
                if (s !== "") val = parseInt(s);
            }

            return val !== 0 ? (isNeg ? "-" : "") + val : "";
        }

        function startApp() {
            document.getElementById('overlay').style.display = 'none';
            initSpeech();
            timerInt = setInterval(() => {
                timeLeft--; 
                document.getElementById('timer').innerText = timeLeft;
                if (timeLeft <= 10) document.getElementById('timer').style.color = 'var(--neon-red)';
                if (timeLeft <= 0) end("SYSTEM TIMEOUT");
            }, 1000);
            next();
        }

        function initSpeech() {
            const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!Speech) { alert("Please use Chrome"); return; }
            
            recognition = new Speech();
            recognition.lang = 'zh-TW';
            recognition.continuous = true;
            recognition.interimResults = true;

            recognition.onresult = (e) => {
                if (!isListening) return;
                let transcript = "";
                for (let i = e.resultIndex; i < e.results.length; i++) transcript = e.results[i][0].transcript;
                if (!transcript) return;
                
                document.getElementById('msg').innerText = ">> " + transcript;
                let parsed = smartParse(transcript);
                
                if (parsed != "" && parsed == currentAns) {
                    isListening = false;
                    win();
                }
            };
            
            recognition.onend = () => { if (timeLeft > 0) try { recognition.start(); } catch (e) { } };
            recognition.start();
        }

        function next() {
            if (count >= config.total_q) return end("MISSION COMPLETE");
            
            count++;
            document.getElementById('idx').innerText = count;
            document.getElementById('msg').innerText = "CALCULATING...";

            let ops = config.ops, op = ops[Math.floor(Math.random() * ops.length)];
            let max = config.ranges.includes('1000') ? 1000 : (config.ranges.includes('100') ? 100 : 10);
            let allowNeg = config.allow_neg;
            
            let n1 = Math.floor(Math.random() * max) + 1, n2 = Math.floor(Math.random() * max) + 1;
            
            let tts = "", html = "";
            if (op === '+') { currentAns = n1 + n2; html = `${n1} + ${n2}`; tts = `${n1}加${n2}`; }
            else if (op === '-') { 
                if (n1 < n2) [n1, n2] = [n2, n1];
                currentAns = n1 - n2; html = `${n1} - ${n2}`; tts = `${n1}減${n2}`; 
            }
            else if (op === '*') { currentAns = n1 * n2; html = `${n1} × ${n2}`; tts = `${n1}乘以${n2}`; }
            else if (op === '/') { 
                n2 = Math.floor(Math.random() * 9) + 1; 
                currentAns = Math.floor(Math.random() * 9) + 1; 
                n1 = n2 * currentAns; 
                html = `${n1} ÷ ${n2}`; tts = `${n1}除以${n2}`; 
            }

            isListening = false;
            document.getElementById('equation').innerText = html;
            document.getElementById('equation').style.color = "white";
            
            synth.cancel();
            let u = new SpeechSynthesisUtterance(tts);
            u.lang = 'zh-TW'; u.rate = 1.3;
            u.onend = () => {
                isListening = true;
                document.getElementById('msg').innerText = "LISTENING...";
            };
            synth.speak(u);
        }

        function win() {
            combo++;
            score += (10 + Math.floor(combo/2));
            document.getElementById('scoreDisplay').innerText = score;
            
            if (combo > 1) {
                let cb = document.getElementById('combo');
                cb.innerText = `COMBO X${combo}`;
                cb.style.display = 'block';
            }

            document.getElementById('equation').style.color = "var(--neon-green)";
            document.body.classList.add('correct-flash');
            
            // 🚩 儲存紀錄
            fetch('save_record.php', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: `category=math&subject=心算&is_correct=1`
            });

            confetti({ particleCount: 40, spread: 50, origin: { y: 0.8 }, colors: ['#bc13fe', '#00f3ff'] });

            setTimeout(() => {
                document.body.classList.remove('correct-flash');
                next();
            }, 800);
        }

        function end(m) {
            clearInterval(timerInt);
            alert(`${m}\nSCORE: ${score}\nCOMBO: ${combo}`);
            location.href = 'index.php';
        }
    </script>
</body>

</html>