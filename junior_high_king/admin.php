<?php
// admin.php
try {
    $db = new PDO("sqlite:quiz.db");
    $sql = "SELECT id, subject, grade, question, answer FROM questions ORDER BY id DESC LIMIT 50";
    $stmt = $db->query($sql);
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
} catch (Exception $e) {
    die($e->getMessage());
}
?>
<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8">
    <title>題目管理後台</title>
    <style>
        body {
            font-family: sans-serif;
            padding: 20px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        th,
        td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }

        th {
            background: #6c5ce7;
            color: white;
        }

        tr:nth-child(even) {
            background: #f9f9f9;
        }

        .del-btn {
            color: red;
            cursor: pointer;
            text-decoration: underline;
        }
    </style>
</head>

<body>
    <h1>🛠️ 題目管理後台 (最近50筆)</h1>
    <p>目前資料庫總量：隨時掌握數據動態</p>

    <table>
        <tr>
            <th>ID</th>
            <th>科目/年級</th>
            <th>題目內容</th>
            <th>答案</th>
            <th>操作</th>
        </tr>
        <?php foreach ($rows as $r): ?>
            <tr>
                <td>
                    <?php echo $r['id']; ?>
                </td>
                <td>
                    <?php echo $r['subject'] . ' / ' . $r['grade']; ?>
                </td>
                <td>
                    <?php echo mb_strimwidth($r['question'], 0, 50, "..."); ?>
                </td>
                <td>
                    <?php echo $r['answer']; ?>
                </td>
                <td><span class="del-btn" onclick="deleteItem(<?php echo $r['id']; ?>)">刪除</span></td>
            </tr>
        <?php endforeach; ?>
    </table>

    <script>
        function deleteItem(id) {
            if (confirm('確定要刪除 ID: ' + id + ' 嗎？這無法復原喔！')) {
                // 這裡之後可以串接刪除 API
                alert('刪除功能待實作 (ID: ' + id + ')');
            }
        }
    </script>
</body>

</html>