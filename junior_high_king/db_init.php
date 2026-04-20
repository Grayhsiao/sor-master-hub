<?php
// db_init.php - 執行完請刪除
try {
    $db = new PDO("sqlite:quiz.db");
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // 建立表格
    $db->exec("CREATE TABLE IF NOT EXISTS entertainment_songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        song_name TEXT NOT NULL,
        yt_id TEXT NOT NULL,
        start_sec INTEGER DEFAULT 60,
        options TEXT
    )");

    // 插入周杰倫經典 Top 5 作為初始資料
    $songs = [
        ['七里香', 'Bbp9ZaJD_eA', 135, '聽媽媽的話,可愛女人,星晴'],
        ['晴天', 'DYzADQC0S60', 78, '楓,退後,彩虹'],
        ['告白氣球', 'bu7nU9Mhpyo', 55, '不該,算什麼男人,等你下課'],
        ['稻香', 's-96rOIKB3k', 60, '牛仔很忙,陽光宅男,跨時代'],
        ['龍拳', '2E0ZpZ_6-T0', 45, '雙截棍,本草綱目,霍元甲']
    ];

    $stmt = $db->prepare("INSERT INTO entertainment_songs (song_name, yt_id, start_sec, options) VALUES (?, ?, ?, ?)");
    foreach ($songs as $s) {
        $stmt->execute($s);
    }

    echo "✅ 資料庫更新成功！您可以關閉此頁面了。";
} catch (Exception $e) {
    echo "❌ 錯誤：" . $e->getMessage();
}