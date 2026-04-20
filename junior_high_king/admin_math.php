<?php
session_start();
// 🚩 核心修復：直接在頁面頂部處理存檔，保證 Session 100% 更新
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $_SESSION['math_config'] = [
        'ops' => explode(',', $_POST['ops']),
        'ranges' => explode(',', $_POST['ranges']),
        'total_q' => (int) $_POST['total_q'],
        'timer' => (int) $_POST['timer']
    ];
    header("Location: index.php"); // 存完直接回大廳
    exit();
}
$conf = $_SESSION['math_config'] ?? ['ops' => ['+'], 'ranges' => ['10'], 'total_q' => 10, 'timer' => 60];
?>
<!DOCTYPE html>
<html lang="zh-TW">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>特訓設定</title>
    <style>
        body {
            font-family: sans-serif;
            background: #f0f2f5;
            padding: 20px;
        }

        .card {
            max-width: 500px;
            margin: auto;
            background: white;
            padding: 30px;
            border-radius: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
            margin: 15px 0;
        }

        .btn-opt {
            background: #f8f9fa;
            padding: 18px 5px;
            border-radius: 15px;
            text-align: center;
            cursor: pointer;
            font-weight: bold;
            border: 2px solid transparent;
        }

        .btn-opt.active {
            background: #6c5ce7;
            color: white;
            border-color: #6c5ce7;
        }

        .input-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 15px;
            margin-top: 10px;
            font-weight: bold;
        }

        input {
            width: 60px;
            border: none;
            background: #fff;
            padding: 5px;
            border-radius: 8px;
            text-align: center;
            font-size: 18px;
            color: #6c5ce7;
            font-weight: bold;
        }

        .save-btn {
            width: 100%;
            padding: 20px;
            background: #00b894;
            color: white;
            border: none;
            border-radius: 20px;
            font-size: 22px;
            font-weight: bold;
            margin-top: 30px;
            cursor: pointer;
        }
    </style>
</head>

<body>
    <div class="card">
        <h2 style="margin:0 0 20px; text-align:center;">⚙️ 特訓參數設定</h2>
        <form method="POST" id="configForm">
            <input type="hidden" name="ops" id="ops_input">
            <input type="hidden" name="ranges" id="ranges_input">

            <div style="color:#6c5ce7; font-weight:bold;">1. 運算項目</div>
            <div class="grid" id="ops-grid">
                <div class="btn-opt" data-val="+">加法</div>
                <div class="btn-opt" data-val="-">減法</div>
                <div class="btn-opt" data-val="*">乘法</div>
                <div class="btn-opt" data-val="/">除法</div>
                <div class="btn-opt" data-val="frac">分數</div>
                <div class="btn-opt" data-val="dec">小數</div>
            </div>

            <div style="color:#6c5ce7; font-weight:bold;">2. 數值範圍</div>
            <div class="grid" id="range-grid">
                <div class="btn-opt" data-val="10">10內</div>
                <div class="btn-opt" data-val="100">100內</div>
                <div class="btn-opt" data-val="neg">負數</div>
            </div>

            <div class="input-row"><span>總題數</span><input type="number" name="total_q" value="<?= $conf['total_q'] ?>">
            </div>
            <div class="input-row"><span>限時(秒)</span><input type="number" name="timer" value="<?= $conf['timer'] ?>">
            </div>

            <button type="button" class="save-btn" onclick="submitForm()">儲存設定並回大廳</button>
        </form>
    </div>
    <script>
        let current = <?= json_encode($conf) ?>;
        function render() {
            document.querySelectorAll('.btn-opt').forEach(el => {
                const val = el.dataset.val;
                const isOp = el.parentElement.id === 'ops-grid';
                el.classList.toggle('active', isOp ? current.ops.includes(val) : current.ranges.includes(val));
                el.onclick = () => {
                    let list = isOp ? current.ops : current.ranges;
                    let idx = list.indexOf(val);
                    if (idx > -1) { if (list.length > 1) list.splice(idx, 1); } else { list.push(val); }
                    render();
                }
            });
        }
        function submitForm() {
            document.getElementById('ops_input').value = current.ops.join(',');
            document.getElementById('ranges_input').value = current.ranges.join(',');
            document.getElementById('configForm').submit();
        }
        render();
    </script>
</body>

</html>