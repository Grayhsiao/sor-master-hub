<?php
header('Content-Type: application/json; charset=utf-8');
$db = new PDO("sqlite:quiz.db");
$sql = "SELECT grade, subject, semester, count(*) as total FROM questions GROUP BY grade, subject, semester";
$res = $db->query($sql)->fetchAll(PDO::FETCH_ASSOC);
$stats = [];
foreach ($res as $row) {
    $stats[$row['grade']][$row['subject']][$row['semester']] = (int)$row['total'];
}
echo json_encode($stats);