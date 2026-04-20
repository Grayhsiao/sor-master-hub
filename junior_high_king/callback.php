<?php
// callback.php
session_start();

// 🚩 ID 必須跟 login.php 完全一樣
$client_id     = '2009384989'; 
$client_secret = '4cc167f9d4f40daae0f9abf88c9a5168';
$redirect_uri  = 'https://phrasally-abolitionary-modesta.ngrok-free.dev/callback.php';

$code = $_GET['code'] ?? '';
$state = $_GET['state'] ?? '';

if ($state !== ($_SESSION['line_state'] ?? '')) {
    die("驗證錯誤 (State Mismatch)，請回首頁重試。");
}

// 1. 換取 Access Token
$ch = curl_init("https://api.line.me/oauth2/v2.1/token");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query([
    'grant_type'    => 'authorization_code',
    'code'          => $code,
    'redirect_uri'  => $redirect_uri,
    'client_id'     => $client_id,
    'client_secret' => $client_secret
]));
$response = json_decode(curl_exec($ch), true);
curl_close($ch);

if (isset($response['access_token'])) {
    // 2. 換取用戶 Profile
    $ch = curl_init("https://api.line.me/v2/profile");
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, ["Authorization: Bearer " . $response['access_token']]);
    $profile = json_decode(curl_exec($ch), true);
    curl_close($ch);

    $_SESSION['user_id']   = $profile['userId'];
    $_SESSION['user_name'] = $profile['displayName'];
    $_SESSION['user_pic']  = $profile['pictureUrl'];

    header("Location: index.php");
    exit;
} else {
    echo "<h1>LINE 登入失敗</h1>";
    echo "<pre>" . json_encode($response, JSON_PRETTY_PRINT) . "</pre>";
    echo "<a href='index.php'>回首頁重新嘗試</a>";
}