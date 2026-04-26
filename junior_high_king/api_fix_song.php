<?php
session_start();
$db = new PDO("sqlite:" . __DIR__ . "/quiz.db");

$id = $_POST['id'] ?? '';
$name = $_POST['name'] ?? '';
$action = $_POST['action'] ?? 'fix';

if (!$id) die("Missing ID");

if ($action === 'mark') {
    // 🚩 標記為有問題
    $stmt = $db->prepare("UPDATE entertainment_songs SET is_buggy = 1 WHERE id = ?");
    $stmt->execute([$id]);
    echo "Marked as buggy";
} else {
    // 🔧 修正歌名
    if ($name) {
        $stmt = $db->prepare("UPDATE entertainment_songs SET song_name = ?, is_buggy = 0 WHERE id = ?");
        $stmt->execute([$name, $id]);
        echo "Fixed name";
    }
}
?>
