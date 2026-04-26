<?php
header('Content-Type: application/json');
$yt_id = $_GET['yt_id'] ?? '';

if (!$yt_id) {
    echo json_encode(['success' => false, 'error' => 'Missing YouTube ID']);
    exit;
}

// 使用 YouTube OEmbed API 獲取資訊
$oembed_url = "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=" . urlencode($yt_id) . "&format=json";

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $oembed_url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 1);
curl_setopt($ch, CURLOPT_TIMEOUT, 5);
$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($http_code === 200) {
    $data = json_decode($response, true);
    $title = $data['title'] ?? '未知歌曲';
    
    // 簡單的 AI 清洗：移除常見的雜訊字眼
    $clean_title = preg_replace('/[\[\(].*?[\]\)]/u', '', $title); // 移除 [Official Video] (Lyrics) 等
    $clean_title = preg_replace('/Official (Music )?Video|Lyrics|HD|1080p|MV|主題曲/iu', '', $clean_title);
    $clean_title = trim($clean_title);
    
    echo json_encode([
        'success' => true,
        'title' => $title,
        'clean_title' => $clean_title,
        'author' => $data['author_name'] ?? ''
    ]);
} else {
    echo json_encode(['success' => false, 'error' => 'Could not fetch YouTube info']);
}
