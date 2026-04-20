<?php
// login.php
session_start();

// 🚩 這裡已經換成你截圖上的正確 ID
$client_id     = '2009384989'; 
$redirect_uri  = 'https://phrasally-abolitionary-modesta.ngrok-free.dev/callback.php';

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