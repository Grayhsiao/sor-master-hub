<?php
// get_questions.php
header('Content-Type: application/json; charset=utf-8');
error_reporting(0); 

try {
    $db = new PDO("sqlite:quiz.db");
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    $subject  = $_GET['subject'] ?? '';
    $grade_in = $_GET['grade'] ?? '';
    $semester = $_GET['semester'] ?? '';
    $exam     = $_GET['exam'] ?? '';

    if (empty($subject)) die(json_encode(['status'=>'error', 'message'=>'未指定科目']));

    // 年級轉換
    $grade_map = ['7'=>'七年級', '8'=>'八年級', '9'=>'九年級'];
    $target_grade = $grade_map[$grade_in] ?? $grade_in;

    /**
     * 🚩 超強過濾網：
     * 1. 排除含有 <img> 標籤的題目 (HTML 圖片)
     * 2. 排除題目文字中包含「圖」字的題目 (如圖、下圖、附圖)
     */
    $filter_sql = " AND question NOT LIKE '%<img%' 
                    AND question NOT LIKE '%圖%' 
                    AND option_a NOT LIKE '%<img%' 
                    AND option_b NOT LIKE '%<img%' 
                    AND option_c NOT LIKE '%<img%' 
                    AND option_d NOT LIKE '%<img%'";

    // 1. 嘗試精確查詢 (年級+學期+段考+無圖)
    $sql = "SELECT * FROM questions WHERE subject LIKE ? AND grade = ? AND semester = ? AND exam = ? $filter_sql ORDER BY RANDOM() LIMIT 1";
    $stmt = $db->prepare($sql);
    $stmt->execute(["%$subject%", $target_grade, $semester, $exam]);
    $q = $stmt->fetch(PDO::FETCH_ASSOC);

    // 2. 如果該範圍沒純文字題，則只抓該科目的純文字題 (保底)
    if (!$q) {
        $sql = "SELECT * FROM questions WHERE subject LIKE ? $filter_sql ORDER BY RANDOM() LIMIT 1";
        $stmt = $db->prepare($sql);
        $stmt->execute(["%$subject%"]);
        $q = $stmt->fetch(PDO::FETCH_ASSOC);
    }

    if ($q) {
        function clean($s) { return preg_replace('/[\x00-\x1F\x7F]/u', '', $s ?? ''); }
        echo json_encode([
            'status' => 'success',
            'data' => [
                'id' => $q['id'],
                'topic' => clean($q['subject']),
                'grade' => clean($q['grade']),
                'semester' => clean($q['semester']),
                'exam' => clean($q['exam']),
                'question' => clean($q['question']),
                'options' => [clean($q['option_a']), clean($q['option_b']), clean($q['option_c']), clean($q['option_d'])],
                'answer' => trim($q['answer']),
                'analysis' => clean($q['analysis'])
            ]
        ], JSON_UNESCAPED_UNICODE);
    } else {
        echo json_encode(['status'=>'error', 'message'=>'抱歉，目前找不到適合的純文字題目。']);
    }
} catch (Exception $e) {
    echo json_encode(['status'=>'error', 'message'=>$e->getMessage()]);
}