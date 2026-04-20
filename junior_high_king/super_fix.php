<?php
$db_path = "quiz.db";
$db = new PDO("sqlite:" . $db_path);

// --- 1. 資料庫強力修復 ---
echo "清理資料庫標籤...\n";
// 恢復原始年級
$db->exec("UPDATE questions SET grade = (SELECT json_extract(data_content, '$.grade') FROM imported_json WHERE imported_json.id = questions.id) WHERE grade IS NULL OR grade = '' OR grade = '(空白)'");
// 強制分類：國文/生物 -> 七年級；理化/數學 -> 八年級
$db->exec("UPDATE questions SET grade = '七年級' WHERE subject IN ('國文', '生物') AND (grade IS NULL OR grade = '')");
$db->exec("UPDATE questions SET grade = '八年級' WHERE (subject IN ('理化', '數學', '自然') OR question LIKE '%反應%') AND (grade IS NULL OR grade = '')");
$db->exec("UPDATE questions SET grade = '八年級' WHERE grade IS NULL OR grade = ''"); // 剩下的通通塞八年級

// --- 2. 重寫 get_stats.php ---
$stats_code = '<?php
header("Content-Type: application/json");
$db = new PDO("sqlite:quiz.db");
$res = $db->query("SELECT grade, subject, count(*) as total FROM questions GROUP BY grade, subject")->fetchAll(PDO::FETCH_ASSOC);
$stats = [];
foreach($res as $r){
    $m = ["數學"=>"math","自然"=>"science","國文"=>"chinese","英文"=>"english","社會"=>"social"];
    $s = $m[$r["subject"]] ?? $r["subject"];
    $stats[$r["grade"]][$s] = (int)$r["total"];
}
echo json_encode($stats);';
file_put_contents("get_stats.php", $stats_code);

// --- 3. 修改 game.php 注入新邏輯 ---
$game_file = "game.php";
$game_html = file_get_contents($game_file);

// 注入顯示 ID 的位置 (放在題目前面)
if (strpos($game_html, "id=\"displayQuestionId\"") === false) {
    $game_html = str_replace('id="questionContent"', 'id="displayQuestionId" style="font-size:12px;color:#aaa;"></div><div id="questionContent"', $game_html);
}

// 注入 JS 邏輯 (更新題號 + 鎖定按鈕)
$js_powerup = '
<script>
// 每當載入題目後，更新顯示
function onQuestionLoaded(data) {
    if(data.id) document.getElementById("displayQuestionId").innerText = "題目 ID：" + data.id;
    const loadingEl = document.evaluate("//div[contains(text(), \"載入中...\")]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
    if(loadingEl) loadingEl.innerText = data.topic || "已載入";
}

// 自動統計與鎖定按鈕
function refreshButtons() {
    fetch("get_stats.php").then(r => r.json()).then(stats => {
        const gradeEl = document.getElementById("gradeSelect");
        if(!gradeEl) return;
        const grade = gradeEl.options[gradeEl.selectedIndex].text;
        document.querySelectorAll(".subject-btn").forEach(btn => {
            const sub = btn.getAttribute("data-subject");
            const count = (stats[grade] && stats[grade][sub]) ? stats[grade][sub] : 0;
            if(!btn.dataset.name) btn.dataset.name = btn.innerText.split(" ")[0];
            btn.innerHTML = `${btn.dataset.name} (${count})`;
            btn.disabled = (count === 0);
            btn.style.opacity = (count === 0 ? "0.3" : "1");
        });
    });
}
document.getElementById("gradeSelect")?.addEventListener("change", refreshButtons);
window.addEventListener("load", refreshButtons);

// 攔截原本的 fetch 邏輯來觸發更新
const originalFetch = window.fetch;
window.fetch = function() {
    return originalFetch.apply(this, arguments).then(async (response) => {
        if (arguments[0].includes("get_questions.php")) {
            const clone = response.clone();
            const json = await clone.json();
            if(json.status === "success") setTimeout(() => onQuestionLoaded(json.data), 100);
        }
        return response;
    });
};
</script>';

if (strpos($game_html, "onQuestionLoaded") === false) {
    $game_html = str_replace("</body>", $js_powerup . "</body>", $game_html);
}
file_put_contents($game_file, $game_html);

echo "✅ 資料庫標籤已全數修正！\n";
echo "✅ 後端 API 已同步更新！\n";
echo "✅ 前端 UI 邏輯已強制注入！\n";
