<?php
session_start();

// 🚩 獲取 User ID，如果沒登入則使用測試帳號 (方便在地端開發)
$user_id = $_SESSION['user_id'] ?? ($_SESSION['user']['id'] ?? 'GUEST_TEST');

$db = new PDO('sqlite:education.db');
$stmt = $db->prepare("INSERT INTO study_logs (user_id, category, subject, is_correct) VALUES (?, ?, ?, ?)");
$stmt->execute([
    $user_id, 
    $_POST['category'] ?? 'math', 
    $_POST['subject'] ?? '心算', 
    $_POST['is_correct'] ?? 1
]);

// 如果是測試帳號，順便確保 users 表格有這筆資料
if ($user_id === 'GUEST_TEST') {
    $db->prepare("INSERT OR IGNORE INTO users (user_id, name, pic, login_type) VALUES ('GUEST_TEST', '測試員', 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png', 'test')")->execute();
}

echo json_encode(['status' => 'success', 'user_id' => $user_id]);