<?php
// check_counts.php
header('Content-Type: application/json; charset=utf-8');
try {
    $db = new PDO("sqlite:quiz.db");
    $g_raw = $_GET['grade'] ?? '7';
    $s     = $_GET['semester'] ?? '2';
    $e     = $_GET['exam'] ?? '1';

    $grade_map = ['7'=>'七年級', '8'=>'八年級', '9'=>'九年級'];
    $target_grade = $grade_map[$g_raw] ?? $g_raw;

    // 🚩 題數統計也要排除含「圖」的題目
    $sql = "SELECT subject, COUNT(*) as count FROM questions 
            WHERE grade = ? AND semester = ? AND exam = ? 
            AND question NOT LIKE '%<img%'
            AND question NOT LIKE '%圖%'
            AND option_a NOT LIKE '%<img%'
            AND option_b NOT LIKE '%<img%'
            AND option_c NOT LIKE '%<img%'
            AND option_d NOT LIKE '%<img%'
            GROUP BY subject";
    
    $stmt = $db->prepare($sql);
    $stmt->execute([$target_grade, $s, $e]);
    $results = $stmt->fetchAll(PDO::FETCH_KEY_PAIR); 

    echo json_encode($results ?: new stdClass(), JSON_UNESCAPED_UNICODE);
} catch (Exception $err) {
    echo json_encode([]);
}