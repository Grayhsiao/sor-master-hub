<?php
// 這裡是簡單的處理邏輯，實務上可以存入資料庫
if ($_POST) {
    // 這裡可以寫入資料庫
    echo "<script>alert('設定已更新！');</script>";
}
?>
<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8">
    <title>心算命題中心</title>
    <style>
        body {
            font-family: sans-serif;
            background: #f4f7f6;
            padding: 40px;
        }

        .admin-box {
            max-width: 500px;
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            margin: auto;
        }

        label {
            display: block;
            margin-top: 15px;
            font-weight: bold;
        }

        input,
        select {
            width: 100%;
            padding: 10px;
            margin-top: 5px;
            border-radius: 8px;
            border: 1px solid #ddd;
        }

        .save-btn {
            background: #6c5ce7;
            color: white;
            border: none;
            padding: 15px;
            width: 100%;
            margin-top: 25px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 18px;
        }
    </style>
</head>

<body>

    <div class="admin-box">
        <h2>⚙️ 心算命題中心</h2>
        <form method="POST">
            <label>難易度 (位數)</label>
            <select name="digits">
                <option value="10">個位數 (1-10)</option>
                <option value="100" selected>十位數 (10-99)</option>
                <option value="1000">百位數 (100-999)</option>
            </select>

            <label>總題數</label>
            <input type="number" name="totalQ" value="10">

            <label>每題答題時間 (秒)</label>
            <input type="number" name="timeLimit" value="10">

            <label>運算類型</label>
            <input type="checkbox" checked> 加法
            <input type="checkbox"> 減法
            <input type="checkbox"> 乘法

            <button type="submit" class="save-btn">儲存設定並套用</button>
        </form>
    </div>

</body>

</html>