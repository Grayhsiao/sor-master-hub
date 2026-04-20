<?php
// setup_v4.php - Gray's Lab 終極管理強化版
header('Content-Type: text/html; charset=utf-8');
require_once 'configgem.php';

try {
    $db = new PDO("sqlite:quiz.db");

    // --- 1. 強化採集器 (admin_yt_tool.php)：更暴力的關鍵字過濾 ---
    $yt_tool_code = <<<'EOD'
<?php
session_start();
require_once 'configgem.php';
$msg = ""; $db = new PDO("sqlite:quiz.db");
function cleanTitle($t, $a) {
    // V4 強化版：增加更多垃圾字眼過濾
    $p = ["/$a/i", "/Music/i", "/Topic/i", "/Official/i", "/Video/i", "/MV/i", "/\d+K/i", "/\(.*\)/", "/\[.*\]/", "/【.*】/", "/-/", "/Check out/i", "/Netflix/i", "/發燒影片/i", "/\s+/"];
    $c = trim(preg_replace($p, ' ', $t));
    // 如果過濾完剩不到 2 個字，很可能是抓到純頻道名，補個「未命名」
    return (mb_strlen($c) < 2) ? "待修正歌曲" : $c;
}
if (isset($_POST['action'])) {
    $artist = $_POST['artist']; $count = (int)$_POST['count'];
    $url = "https://www.googleapis.com/youtube/v3/search?".http_build_query(['part'=>'snippet','q'=>$artist." 歌曲",'type'=>'video','videoCategoryId'=>'10','maxResults'=>$count,'key'=>YT_API_KEY]);
    $data = json_decode(file_get_contents($url), true);
    if (isset($data['items'])) {
        foreach ($data['items'] as $item) {
            $name = cleanTitle($item['snippet']['title'], $artist);
            $db->prepare("INSERT INTO entertainment_songs (artist, song_name, yt_id) VALUES (?, ?, ?)")
               ->execute([$artist, $name, $item['id']['videoId']]);
        }
        $msg = "✅ 採集完成！請去管理頁面微調歌名。";
    }
}
?>
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>採集器 V4</title><style>body{font-family:sans-serif;text-align:center;padding:50px;background:#f0f2f5;}.box{background:white;padding:30px;border-radius:20px;max-width:400px;margin:auto;box-shadow:0 10px 20px rgba(0,0,0,0.1);}input{width:100%;padding:10px;margin:10px 0;box-sizing:border-box;}button{width:100%;padding:10px;background:#6c5ce7;color:white;border:none;border-radius:10px;cursor:pointer;}</style></head>
<body><div class="box"><h2>🚀 歌手歌曲採集 V4</h2><form method="POST"><input type="hidden" name="action" value="1"><input type="text" name="artist" placeholder="歌手姓名" required><input type="number" name="count" value="20"><button type="submit">開始採集</button></form><p><?=$msg?></p><a href="admin_list.php">前往管理頁面修改歌名</a></div></body></html>
EOD;

    // --- 2. 強化管理頁面 (admin_list.php)：增加「直接修改」功能 ---
    $admin_list_code = <<<'EOD'
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
EOD;

    file_put_contents('admin_yt_tool.php', $yt_tool_code);
    file_put_contents('admin_list.php', $admin_list_code);
    echo "<h2>🎉 V4 強化版部署完成！</h2>";
    echo "1. <b>過濾器升級</b>：會自動刪除 Netflix、Check out 等無關字眼。<br>";
    echo "2. <b>後台秒改</b>：在管理頁面，您可以直接在輸入框改好歌名，按「改」就生效。<br>";
    echo "請先 <a href='admin_list.php'>點我清空舊資料</a>，再重新採集！";

} catch (Exception $e) {
    echo "❌ 錯誤：" . $e->getMessage();
}