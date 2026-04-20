<?php
$db = new PDO("sqlite:quiz.db");
// 處理修改歌名
if (isset($_POST['update_id'])) {
    $stmt = $db->prepare("UPDATE entertainment_songs SET song_name = ? WHERE id = ?");
    $stmt->execute([$_POST['new_name'], $_POST['update_id']]);
}
// 處理刪除與清空
if (isset($_GET['del'])) { $db->prepare("DELETE FROM entertainment_songs WHERE id=?")->execute([$_GET['del']]); }
if (isset($_POST['clear_all'])) { $db->exec("DELETE FROM entertainment_songs"); }

$songs = $db->query("SELECT * FROM entertainment_songs ORDER BY id DESC")->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>題庫管理</title><style>body{font-family:sans-serif;padding:20px;background:#f0f2f5;}table{width:100%;background:white;border-collapse:collapse;border-radius:15px;overflow:hidden;box-shadow:0 5px 15px rgba(0,0,0,0.05);}th,td{padding:12px;border-bottom:1px solid #eee;text-align:center;}tr:hover{background:#f9f9f9;}input{padding:5px;border:1px solid #ddd;border-radius:5px;width:80%;}</style></head>
<body>
    <h2>題庫管理 (共 <?=count($songs)?> 首)</h2>
    <form method="POST" onsubmit="return confirm('確定清空？')"><button name="clear_all" style="background:#ff7675;color:white;border:none;padding:10px;border-radius:8px;cursor:pointer;">🔥 全部清空</button></form><br>
    <table>
        <tr style="background:#6c5ce7;color:white;"><th>歌手</th><th>歌名 (點擊文字可修改)</th><th>操作</th></tr>
        <?php foreach($songs as $s): ?>
        <tr>
            <td><?=$s['artist']?></td>
            <td>
                <form method="POST" style="display:flex;gap:5px;">
                    <input type="hidden" name="update_id" value="<?=$s['id']?>">
                    <input type="text" name="new_name" value="<?=$s['song_name']?>">
                    <button type="submit" style="background:#00b894;color:white;border:none;padding:5px 10px;border-radius:5px;cursor:pointer;">改</button>
                </form>
            </td>
            <td><a href="?del=<?=$s['id']?>" style="color:#ff7675;text-decoration:none;">[刪除]</a></td>
        </tr>
        <?php endforeach; ?>
    </table>
    <br><a href="index.php">← 回大廳</a>
</body></html>