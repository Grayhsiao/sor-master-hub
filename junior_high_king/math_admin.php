<?php
session_start();

// 🚩 密碼保護 (1234)
if (!isset($_SESSION['admin_auth'])) {
    if (isset($_POST['admin_pw']) && $_POST['admin_pw'] === '1234') {
        $_SESSION['admin_auth'] = true;
    } else {
        die('
        <div style="text-align:center; padding-top:100px; font-family:sans-serif;">
            <h2>🔐 進入管理後台</h2>
            <form method="POST">
                <input type="password" name="admin_pw" placeholder="輸入密碼" style="padding:10px; border-radius:8px; border:1px solid #ccc;">
                <button type="submit" style="padding:10px 20px; border-radius:8px; background:#6c5ce7; color:white; border:none; cursor:pointer;">登入</button>
            </form>
            <p><a href="index.php" style="color:#888; text-decoration:none;">← 返回首頁</a></p>
        </div>');
    }
}

$config_file = 'math_settings.json';

// 預設值
$default_config = [
    'ops' => ['+', '-'],
    'ranges' => ['100'],
    'total_q' => 10,
    'timer' => 60,
    'allow_neg' => false
];

// 讀取現有設定
if (file_exists($config_file)) {
    $current_config = json_decode(file_get_contents($config_file), true);
} else {
    $current_config = $default_config;
}

// 處理儲存
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $new_config = [
        'ops' => $_POST['ops'] ?? ['+'],
        'ranges' => $_POST['ranges'] ?? ['100'],
        'total_q' => (int)($_POST['total_q'] ?? 10),
        'timer' => (int)($_POST['timer'] ?? 60),
        'allow_neg' => isset($_POST['allow_neg'])
    ];
    
    file_put_contents($config_file, json_encode($new_config));
    $current_config = $new_config;
    $message = "✅ 設定已成功套用於全系統！";
}
?>
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>心算命題中心 - 後台控制台</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { font-family: 'Noto Sans TC', sans-serif; background: #f0f2f5; padding: 20px; }
        .admin-box { max-width: 600px; background: white; padding: 40px; border-radius: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin: 20px auto; }
        h2 { color: #6c5ce7; margin-bottom: 30px; display: flex; align-items: center; gap: 10px; }
        .form-group { margin-bottom: 25px; border-bottom: 1px solid #eee; padding-bottom: 20px; }
        label { display: block; font-weight: bold; margin-bottom: 10px; color: #444; }
        .check-group { display: flex; gap: 15px; flex-wrap: wrap; }
        .check-item { display: flex; align-items: center; gap: 5px; background: #f8f9fa; padding: 10px 15px; border-radius: 12px; cursor: pointer; }
        input[type="number"] { width: 100px; padding: 10px; border-radius: 8px; border: 1px solid #ddd; }
        .save-btn { background: #6c5ce7; color: white; border: none; padding: 18px; width: 100%; border-radius: 15px; font-size: 18px; font-weight: bold; cursor: pointer; transition: 0.3s; }
        .save-btn:hover { background: #5649c0; transform: translateY(-2px); }
        .msg { background: #d1f7e6; color: #008744; padding: 15px; border-radius: 12px; margin-bottom: 20px; text-align: center; font-weight: bold; }
    </style>
</head>
<body>
    <div class="admin-box">
        <h2><i class="fas fa-cog"></i> 心算命題中心</h2>
        
        <?php if(isset($message)) echo "<div class='msg'>$message</div>"; ?>

        <form method="POST">
            <div class="form-group">
                <label>1. 運算符號 (Operators)</label>
                <div class="check-group">
                    <label class="check-item"><input type="checkbox" name="ops[]" value="+" <?php echo in_array('+', $current_config['ops']) ? 'checked' : ''; ?>> 加法 (+)</label>
                    <label class="check-item"><input type="checkbox" name="ops[]" value="-" <?php echo in_array('-', $current_config['ops']) ? 'checked' : ''; ?>> 減法 (-)</label>
                    <label class="check-item"><input type="checkbox" name="ops[]" value="*" <?php echo in_array('*', $current_config['ops']) ? 'checked' : ''; ?>> 乘法 (×)</label>
                    <label class="check-item"><input type="checkbox" name="ops[]" value="/" <?php echo in_array('/', $current_config['ops']) ? 'checked' : ''; ?>> 除法 (÷)</label>
                </div>
            </div>

            <div class="form-group">
                <label>2. 數字範圍 (Digits)</label>
                <div class="check-group">
                    <label class="check-item"><input type="radio" name="ranges[]" value="10" <?php echo in_array('10', $current_config['ranges']) ? 'checked' : ''; ?>> 個位數 (1-10)</label>
                    <label class="check-item"><input type="radio" name="ranges[]" value="100" <?php echo in_array('100', $current_config['ranges']) ? 'checked' : ''; ?>> 十位數 (10-99)</label>
                    <label class="check-item"><input type="radio" name="ranges[]" value="1000" <?php echo in_array('1000', $current_config['ranges']) ? 'checked' : ''; ?>> 百位數 (100-999)</label>
                </div>
            </div>

            <div class="form-group">
                <label>3. 負數開關 (Negative Numbers)</label>
                <label class="check-item"><input type="checkbox" name="allow_neg" <?php echo ($current_config['allow_neg'] ?? false) ? 'checked' : ''; ?>> 允許負數 (如 5 - 10 = -5)</label>
            </div>

            <div class="form-group" style="display:flex; gap:30px;">
                <div>
                    <label>4. 總題數 (Total Q)</label>
                    <input type="number" name="total_q" value="<?php echo $current_config['total_q']; ?>" min="1" max="50">
                </div>
                <div>
                    <label>5. 限制時間 (Timer sec)</label>
                    <input type="number" name="timer" value="<?php echo $current_config['timer']; ?>" min="10" max="300">
                </div>
            </div>

            <button type="submit" class="save-btn">儲存並立即套用</button>
        </form>
        
        <p style="text-align:center; margin-top:20px;">
            <a href="index.php" style="color:#888; text-decoration:none;"><i class="fas fa-chevron-left"></i> 返回主廳</a>
        </p>
    </div>
</body>
</html>