<?php
header('Content-Type: application/json');

$response = ['status' => 'error', 'message' => 'Invalid request'];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = file_get_contents('php://input');
    $data = json_decode($input, true);

    if (json_last_error() !== JSON_ERROR_NONE) {
        $response['message'] = 'Invalid JSON input.';
        echo json_encode($response);
        exit;
    }

    $userId = $data['user_id'] ?? null;
    $questionId = $data['question_id'] ?? null;
    $isCorrect = $data['is_correct'] ?? null;
    $answerChosen = $data['answer_chosen'] ?? null;

    if ($userId === null || $questionId === null || $isCorrect === null || $answerChosen === null) {
        $response['message'] = 'Missing required log data.';
        echo json_encode($response);
        exit;
    }

    $dbPath = __DIR__ . '/quiz.db'; // Adjust path if necessary
    try {
        $db = new PDO('sqlite:' . $dbPath);
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        $stmt = $db->prepare('INSERT INTO study_logs (user_id, question_id, is_correct, answer_chosen) VALUES (:user_id, :question_id, :is_correct, :answer_chosen)');
        $stmt->bindValue(':user_id', $userId, PDO::PARAM_INT);
        $stmt->bindValue(':question_id', $questionId, PDO::PARAM_STR);
        $stmt->bindValue(':is_correct', $isCorrect ? 1 : 0, PDO::PARAM_INT); // SQLite stores BOOLEAN as INTEGER (0 or 1)
        $stmt->bindValue(':answer_chosen', $answerChosen, PDO::PARAM_STR);

        $stmt->execute();
        $response = ['status' => 'success', 'message' => 'Log saved successfully.'];

    } catch (PDOException $e) {
        $response['message'] = 'Database error: ' . $e->getMessage();
    }
}

echo json_encode($response);
?>