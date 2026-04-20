<?php
$file = "game.php";
$content = file_get_contents($file);

// 準備最強大的前端邏輯
$script = '
<script>
function refreshButtons() {
    console.log("正在盤點題庫...");
    // 確保路徑對準 localhost:8000/get_stats.php
    fetch("/get_stats.php")
        .then(r => r.json())
        .then(stats => {
            const gradeSelect = document.getElementById("gradeSelect");
            if (!gradeSelect) return;
            const currentGrade = gradeSelect.options[gradeSelect.selectedIndex].text;
            console.log("當前年級：" + currentGrade);

            // 科目對照表
            const sMap = {"數學":"math", "自然":"science", "理化":"science", "生物":"science", "國文":"chinese", "英文":"english", "社會":"social", "地理":"social", "歷史":"social", "公民":"social"};

            // 抓取頁面上所有的按鈕
            document.querySelectorAll("button").forEach(btn => {
                const btnText = btn.innerText.trim();
                let subKey = btn.getAttribute("data-subject");
                
                // 如果按鈕沒寫 data-subject，我們用文字來猜
                if(!subKey) {
                    for(let key in sMap) {
                        if(btnText.includes(key)) { subKey = sMap[key]; break; }
                    }
                }

                if (subKey) {
                    const count = (stats[currentGrade] && stats[currentGrade][subKey]) ? stats[currentGrade][subKey] : 0;
                    
                    // 備份原始文字 (避免重複疊加括號)
                    if (!btn.dataset.orig) btn.dataset.orig = btnText.split(" ")[0].split("(")[0];

                    if (count > 0) {
                        btn.disabled = false;
                        btn.style.opacity = "1";
                        btn.style.cursor = "pointer";
                        btn.innerHTML = `${btn.dataset.orig} <span style="font-size:0.8em;color:#FFD700;">(${count})</span>`;
                    } else {
                        btn.disabled = true;
                        btn.style.opacity = "0.3";
                        btn.style.cursor = "not-allowed";
                        btn.innerHTML = `${btn.dataset.orig} <span style="font-size:0.8em;">(無題)</span>`;
                    }
                }
            });
        }).catch(err => console.error("抓取統計失敗:", err));
}

// 監聽年級切換
document.getElementById("gradeSelect").addEventListener("change", refreshButtons);
// 進入頁面後立刻執行一次
window.onload = refreshButtons;
// 每 10 秒自動盤點一次 (當 OC 在搬家時會自動更新數字)
setInterval(refreshButtons, 10000);
</script>
';

// 刪除舊的邏輯防止衝突，並在 </body> 前插入新的
$content = preg_replace('/<script>.*?refreshButtons.*?<\/script>/s', '', $content);
$content = str_replace('</body>', $script . '</body>', $content);
file_put_contents($file, $content);

echo "✅ [前端鎖定] 邏輯已強力注入！\n";
echo "💡 請現在回到瀏覽器按 Cmd+Shift+R 重新整理。\n";
?>
