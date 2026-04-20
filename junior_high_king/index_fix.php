<?php
$file = "index.php";
if (!file_exists($file)) { die("找不到 index.php，請確認路徑！"); }
$content = file_get_contents($file);

$script = '
<script>
function syncMenu() {
    fetch("get_stats.php")
        .then(r => r.json())
        .then(stats => {
            const gradeEl = document.getElementById("gradeSelect");
            if (!gradeEl) return;
            const grade = gradeEl.options[gradeEl.selectedIndex].text;

            // 抓取所有科目按鈕 (假設 class 是 subject-btn)
            document.querySelectorAll(".subject-btn").forEach(btn => {
                const sub = btn.getAttribute("data-subject");
                const count = (stats[grade] && stats[grade][sub]) ? stats[grade][sub] : 0;
                
                if (!btn.dataset.orig) btn.dataset.orig = btn.innerText.split(" ")[0];

                if (count > 0) {
                    btn.disabled = false;
                    btn.style.opacity = "1";
                    btn.innerHTML = `${btn.dataset.orig} (${count})`;
                } else {
                    btn.disabled = true;
                    btn.style.opacity = "0.3";
                    btn.innerHTML = `${btn.dataset.orig} (無題)`;
                }
            });
        });
}
document.getElementById("gradeSelect")?.addEventListener("change", syncMenu);
window.addEventListener("load", syncMenu);
</script>
';

// 注入到 index.php
if (strpos($content, "syncMenu") === false) {
    file_put_contents($file, $content . $script);
    echo "✅ index.php 選單鎖定邏輯已同步！\n";
} else {
    echo "ℹ️ index.php 邏輯已存在。\n";
}
?>
