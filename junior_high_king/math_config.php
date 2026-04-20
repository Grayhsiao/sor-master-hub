<?php
// 這是預設值，後台改了會存到這
$config = [
    'digits' => 100,      // 位數 (10, 100, 1000)
    'totalQ' => 10,       // 總題數
    'timeLimit' => 10,    // 每題秒數
    'ops' => ['+']        // 運算符號
];
// 如果有本地設定檔就讀取
if (file_exists('math_settings.json')) {
    $config = json_decode(file_get_contents('math_settings.json'), true);
}
?>