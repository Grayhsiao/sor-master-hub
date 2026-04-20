<?php
$db_path = 'quiz.db';
$message = '';

function getSetting($db, $name, $default = null) {
    $stmt = $db->prepare('SELECT setting_value FROM system_settings WHERE setting_name = ?');
    $stmt->execute([$name]);
    $result = $stmt->fetch(PDO::FETCH_ASSOC);
    return $result ? $result['setting_value'] : $default;
}

function updateSetting($db, $name, $value) {
    $stmt = $db->prepare('UPDATE system_settings SET setting_value = ? WHERE setting_name = ?');
    return $stmt->execute([$value, $name]);
}

try {
    $db = new PDO("sqlite:$db_path");
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $total_questions = filter_var($_POST['total_questions'], FILTER_VALIDATE_INT);
        $voice_timeout = filter_var($_POST['voice_timeout'], FILTER_VALIDATE_INT);
        $mc_timeout = filter_var($_POST['mc_timeout'], FILTER_VALIDATE_INT);

        if ($total_questions === false || $total_questions < 1) {
            $message = "<div class=\"alert error\">題目總數必須是正整數。</div>";
        } elseif ($voice_timeout === false || $voice_timeout < 1) {
            $message = "<div class=\"alert error\">語音倒數時間必須是正整數。</div>";
        } elseif ($mc_timeout === false || $mc_timeout < 1) {
            $message = "<div class=\"alert error\">選擇題倒數時間必須是正整數。</div>";
        } else {
            updateSetting($db, 'total_questions', $total_questions);
            updateSetting($db, 'voice_timeout', $voice_timeout);
            updateSetting($db, 'mc_timeout', $mc_timeout);
            $message = "<div class=\"alert success\">設定已成功更新！</div>";
        }
    }

    // 讀取當前設定
    $current_total_questions = getSetting($db, 'total_questions', 20);
    $current_voice_timeout = getSetting($db, 'voice_timeout', 5);
    $current_mc_timeout = getSetting($db, 'mc_timeout', 15);

} catch (Exception $e) {
    $message = "<div class=\"alert error\">資料庫錯誤: " . $e->getMessage() . "</div>";
    // 為防止未定義變數錯誤，設置預設值
    $current_total_questions = 20;
    $current_voice_timeout = 5;
    $current_mc_timeout = 15;
}
?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>國中智慧王 - 系統設定</title>
    <style>
        body { font-family: "PingFang TC", sans-serif; background: #f4f7f9; padding: 20px; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 30px auto; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
        h1 { color: #1a73e8; text-align: center; margin-bottom: 25px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: bold; color: #555; }
        input[type="number"] {
            width: calc(100% - 20px); /* Adjust for padding */
            padding: 12px 10px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            box-sizing: border-box;
            transition: border-color 0.2s;
        }
        input[type="number"]:focus { border-color: #1a73e8; outline: none; }
        button { 
            background: #34a853;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            font-size: 18px;
            cursor: pointer;
            transition: background-color 0.2s, transform 0.2s;
            display: block;
            width: 100%;
            font-weight: bold;
        }
        button:hover { background-color: #2e8b4e; transform: translateY(-1px); }
        .alert { padding: 15px; border-radius: 8px; margin-bottom: 20px; font-weight: bold; }
        .alert.success { background-color: #e6ffed; color: #1b5e20; border: 1px solid #a3e9a4; }
        .alert.error { background-color: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
        .back-link { display: block; text-align: center; margin-top: 20px; color: #1a73e8; text-decoration: none; font-weight: bold; }
        .back-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚙️ 系統設定</h1>
        <?php echo $message; // 顯示訊息 ?>
        <form method="POST">
            <div class="form-group">
                <label for="total_questions">題目總數:</label>
                <input type="number" id="total_questions" name="total_questions" value="<?php echo htmlspecialchars($current_total_questions); ?>" min="1" required>
            </div>
            <div class="form-group">
                <label for="voice_timeout">語音倒數時間 (秒):</label>
                <input type="number" id="voice_timeout" name="voice_timeout" value="<?php echo htmlspecialchars($current_voice_timeout); ?>" min="1" required>
            </div>
            <div class="form-group">
                <label for="mc_timeout">選擇題倒數時間 (秒):</label>
                <input type="number" id="mc_timeout" name="mc_timeout" value="<?php echo htmlspecialchars($current_mc_timeout); ?>" min="1" required>
            </div>
            <button type="submit">儲存設定</button>
        </form>
        <a href="admin.php" class="back-link">← 返回後台</a>
    </div>
</body>
</html>
