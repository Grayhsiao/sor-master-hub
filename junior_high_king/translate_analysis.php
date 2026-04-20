<?php
// --- 設定區 ---
$apiKey = 'AIzaSyB-27zLWavBkoHF-eWgZeIZTMoF5AlQMZo'; // 🚩 貼上後請確認頭尾沒有空格
$subject = '英文'; 
// -------------

set_time_limit(0);
header('Content-Type: text/html; charset=utf-8');

$apiKey = trim($apiKey); // 預防性去除空格

try {
    $db = new PDO("sqlite:quiz.db");
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // 抓取 5 題先測試
    $stmt = $db->query("SELECT id, analysis FROM questions WHERE subject = '$subject' AND analysis NOT LIKE '%【中文翻譯】%' ");
    $questions = $stmt->fetchAll(PDO::FETCH_ASSOC);

    if (empty($questions)) {
        die("沒有需要翻譯的題目了！");
    }

    echo "<h2>🛡️ 強效翻譯模式啟動...</h2>";

    foreach ($questions as $q) {
        $id = $q['id'];
        $originalAnalysis = $q['analysis'];

        // 1. 準備 API 請求
        // 改用 v1 穩定版介面
        $url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=" . $apiKey;
        
        $prompt = "請將以下英文解析翻譯成流暢的繁體中文，保留專業術語，只回傳翻譯內容：\n\n" . $originalAnalysis;
        
        $data = [
            "contents" => [
                [
                    "parts" => [
                        ["text" => $prompt]
                    ]
                ]
            ]
        ];

        $jsonPayload = json_encode($data, JSON_UNESCAPED_UNICODE);

        // 2. 執行 CURL
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $jsonPayload);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        // 3. 處理結果
        if ($httpCode === 200) {
            $result = json_decode($response, true);
            $translatedText = $result['candidates'][0]['content']['parts'][0]['text'] ?? null;

            if ($translatedText) {
                $newAnalysis = $originalAnalysis . "\n\n【中文翻譯】\n" . trim($translatedText);
                $update = $db->prepare("UPDATE questions SET analysis = ? WHERE id = ?");
                $update->execute([$newAnalysis, $id]);
                echo "✅ ID $id 成功！<br>";
            }
        } else {
            echo "❌ ID $id 失敗！代碼：$httpCode <br>";
            echo "📝 伺服器回傳：<pre>" . htmlspecialchars($response) . "</pre><hr>";
            break; // 只要失敗一次就停止，方便偵錯
        }

        usleep(500000); // 休息 0.5 秒避免被限速
    }

} catch (Exception $e) {
    echo "💥 錯誤：" . $e->getMessage();
}
?>