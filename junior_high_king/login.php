<?php
// login.php
session_start();

// 🚩 自動偵測環境
$is_local = (strpos($_SERVER['HTTP_HOST'], 'localhost') !== false || strpos($_SERVER['HTTP_HOST'], '127.0.0.1') !== false || strpos($_SERVER['HTTP_HOST'], '.dev') !== false);

$client_id = '2009384989'; 

if ($is_local) {
    // 本地測試網址 (需配合你的 ngrok 網域)
    $redirect_uri = 'https://phrasally-abolitionary-modesta.ngrok-free.dev/callback.php';
} else {
    // 正式伺服器網址
    $redirect_uri = 'https://sor14.duckdns.org/king/callback.php';
}

$state = bin2hex(random_bytes(16));
$_SESSION['line_state'] = $state;

$params = [
    'response_type' => 'code',
    'client_id'     => $client_id,
    'redirect_uri'  => $redirect_uri,
    'state'         => $state,
    'scope'         => 'profile openid email'
];

$url = "https://access.line.me/oauth2/v2.1/authorize?" . http_build_query($params);

header("Location: " . $url);
exit;