<?php
session_start();
if (isset($_POST['student_name'])) {
    $name = trim($_POST['student_name']);
    $user_id = 'LOCAL_' . substr(md5($name), 0, 8);
    $db = new PDO('sqlite:education.db');
    $stmt = $db->prepare("SELECT * FROM users WHERE user_id = ?");
    $stmt->execute([$user_id]);
    if (!$stmt->fetch()) {
        $stmt = $db->prepare("INSERT INTO users (user_id, name, pic, login_type) VALUES (?, ?, ?, ?)");
        $stmt->execute([$user_id, $name, 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png', 'LOCAL']);
    }
    $_SESSION['user'] = ['id' => $user_id, 'name' => $name, 'pic' => 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'];
    header("Location: index.php");
}