<?php
session_start();
if (!isset($_SESSION['user']))
    exit;
$db = new PDO('sqlite:education.db');
$stmt = $db->prepare("INSERT INTO study_logs (user_id, category, subject, is_correct) VALUES (?, ?, ?, ?)");
$stmt->execute([$_SESSION['user']['id'], $_POST['category'] ?? 'math', $_POST['subject'] ?? '心算', $_POST['is_correct'] ?? 1]);