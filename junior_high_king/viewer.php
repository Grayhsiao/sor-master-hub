<?php
$db_path = "/Users/gray/Sites/junior_high_king/quiz.db";
try {
    $db = new PDO("sqlite:" . $db_path);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $rows = $db->query("SELECT id, subject, grade, question, option_a, option_b, option_c, option_d, answer FROM questions ORDER BY id DESC LIMIT 100")->fetchAll(PDO::FETCH_ASSOC);
} catch (Exception $e) {
    die("資料庫讀取失敗：" . $e->getMessage());
}
?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>成品區檢視器</title>
    <style>
        body { font-family: "Microsoft JhengHei", sans-serif; padding: 20px; background: #f4f7f6; }
        table { width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #2c3e50; color: white; }
        tr:nth-child(even) { background: #f9f9f9; }
        .q-text { font-weight: bold; color: #2c3e50; font-size: 1.1em; max-width: 500px; }
        .label-empty { color: #e74c3c; font-weight: bold; background: #ffe6e6; padding: 2px 5px; border-radius: 3px; }
        .subject-tag { background: #3498db; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>📋 成品區題目檢視器 (最新的 100 題)</h1>
    <p>目前讀取資料庫：<?php echo $db_path; ?></p>
    <table>
        <tr>
            <th>ID</th>
            <th>科目/年級</th>
            <th>題目內容</th>
            <th>選項 (A/B/C/D)</th>
            <th>正確答案</th>
        </tr>
        <?php foreach ($rows as $r): ?>
        <tr>
            <td><?php echo $r['id']; ?></td>
            <td>
                <span class="subject-tag"><?php echo htmlspecialchars($r['subject']); ?></span><br><br>
                <span class="<?php echo $r['grade'] ? '' : 'label-empty'; ?>">
                    <?php echo $r['grade'] ?: '⚠️ 未標記年級'; ?>
                </span>
            </td>
            <td class="q-text"><?php echo nl2br(htmlspecialchars($r['question'])); ?></td>
            <td>
                A: <?php echo htmlspecialchars($r['option_a']); ?><br>
                B: <?php echo htmlspecialchars($r['option_b']); ?><br>
                C: <?php echo htmlspecialchars($r['option_c']); ?><br>
                D: <?php echo htmlspecialchars($r['option_d']); ?>
            </td>
            <td style="text-align:center; font-size: 24px; color: #27ae60; font-weight: bold;"><?php echo $r['answer']; ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
</body>
</html>
