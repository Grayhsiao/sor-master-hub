<?php
session_start();
if (isset($_POST['json'])) {
    $_SESSION['math_config'] = json_decode($_POST['json'], true);
    echo "ok";
}
?>