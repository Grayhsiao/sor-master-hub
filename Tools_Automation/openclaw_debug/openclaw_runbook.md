# 🦞 OpenClaw 無腦維護手冊 (防呆防錯版)

這份手冊專門為您量身打造，**您完全不需要使用 `nano` 等文字編輯器**，所有的動作只要「複製、貼上」就能自動完成，絕不出錯！

---

## 🤖 給 AI 助手的系統架構與環境變數 (System Context for AI)

**如果是新的 AI 助手接手這份對話，請務必先閱讀以下環境設定，以免給出錯誤的指令導致崩潰：**
1. **安裝方式：** OpenClaw 是使用 `npm install -g openclaw` 全域安裝在 Ubuntu 伺服器上的。
2. **啟動指令：** **絕對不可以**使用 `npm start` (會找不到 scripts)。必須使用 `npx openclaw gateway --config-path /root/.openclaw/openclaw.json --allow-unconfigured` 來啟動。
3. **設定檔位置：** 真正的設定檔永遠在 `/root/.openclaw/openclaw.json`。
4. **已知 Bug (Origin Not Allowed)：** OpenClaw 2.26 版本的 `gateway.controlUi.allowedOrigins` 如果設定為 `["*"]` 會失效並跳出 1008 Origin Not Allowed 錯誤。必須將 Cloudflare 網址 (如 `https://***.trycloudflare.com`) **明確且完整**地寫入該陣列中。
5. **CLI 執行限制：** 執行 `npx openclaw devices list` 等 CLI 指令時，必須帶上 `OPENCLAW_GATEWAY_MODE=local` 環境變數，不然會報錯 (gateway.remote.url missing)。
6. **重啟標準流程：** 由於背景程序容易卡死，重啟前務必執行 `killall -9 node` 與 `pkill -9 -f openclaw` 徹底清除乾淨。

---

## 🚀 1. 終極一鍵修復與啟動腳本 (2026 最新防當機升級版)

不管什麼時候需要重啟伺服器、或是 LINE 機器人沒反應 (通常是因為 Cloudflare 換了新網址)，您**完全不需要手動修改任何程式碼**。

只要將底下這整段程式碼「**複製，並直接貼上終端機執行**」即可！它會自動幫您：
1. 暴力清除所有卡死的舊程序。
2. 開啟新的隧道並自動抓取網址 (若失敗會跳出提示讓您在終端機輸入)。
3. 更新底層環境變數 (`.env`)。
4. 自動將新網址寫入設定檔白名單，徹底解決 Origin 報錯。
5. 使用安全的背景啟動指令讓機器人滿血復活。

```bash
# ==========================================================
# 🚀 2026 最新！OpenClaw 一鍵修復與啟動神盾腳本
# ==========================================================

echo "🔄 [1/5] 正在暴力清除所有卡死的舊程序..."
killall -9 node 2>/dev/null
pkill -9 -f openclaw 2>/dev/null
sleep 2

echo "🌐 [2/5] 正在啟動 Cloudflare 隧道..."
nohup cloudflared tunnel --url http://127.0.0.1:18789 > /tmp/cloudflare.log 2>&1 &
echo "⏳ 等待 3 秒鐘讓隧道建立連線..."
sleep 3

# 自動擷取網址
NEW_URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com' /tmp/cloudflare.log | tail -1)

if [ -z "$NEW_URL" ]; then
    echo -n "⚠️ 無法自動取得網址！請手動輸入您的 Cloudflare 網址 (包含 https://): "
    read NEW_URL
else
    echo "✅ 成功取得自動網址: $NEW_URL"
fi

echo "💾 [3/5] 正在更新 .env 等底層環境變數..."
cat << EOF > "$HOME/openclaw/.env"
GATEWAY_PUBLIC_URL="${NEW_URL}"
LINE_CHANNEL_SECRET="28d5b01a3e0cb76b30746f04f4a57904"
LINE_CHANNEL_ACCESS_TOKEN="/+99oFfvEJLzTf7pthqA+vMZglDhGQN0dWTRJTwA4aqx7rvXtmpY8SpaX3VVT96+W1Cje1/m6AJeQsSSh4MhDUDBa+DEl4Clqd1iaeMfZlVXO25BSC2UnPKKeiuGJ4XS/Qudp/Jq6ieiP/A9dFKpOwdB04t89/1O/w1cDnyilFU="
EOF

echo "🔓 [4/5] 正在強制寫入專屬網址 Origin 白名單 (解 1008 錯誤)..."
node -e "
const fs = require('fs');
const path1 = '/root/.openclaw/openclaw.json';
const configPath = fs.existsSync(path1) ? path1 : null;
if(configPath) {
  let config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  
  if(!config.gateway) config.gateway = {};
  if(!config.gateway.controlUi) config.gateway.controlUi = {};
  if(!config.gateway.auth) config.gateway.auth = { mode: 'password' };
  
  config.gateway.controlUi.allowedOrigins = ['${NEW_URL}'];
  config.gateway.trustedProxies = ['127.0.0.1', '::1', 'loopback'];
  
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  console.log('✅ 已成功將 ' + '${NEW_URL}' + ' 寫入白名單！');
} else {
  console.log('⚠️ 找不到設定檔，略過白名單設定');
}
"

echo "🚀 [5/5] 正在確保背景啟動並套用新設定..."
nohup npx openclaw gateway --config-path /root/.openclaw/openclaw.json --allow-unconfigured > /tmp/openclaw.log 2>&1 &

echo "=========================================================="
echo "🎉 恭喜！機器人已經吃下無敵星星重新復活啦！"
echo "👉 您的最新網頁控制台網址是: $NEW_URL"
echo "👉 如果你要接 LINE，請到 LINE 後台更改 Webhook 為:"
echo "   $NEW_URL/line/webhook"
echo "=========================================================="
```

---

## 🚑 🆘 緊急救援：設定檔遺失 / 全部重置 怎麼辦？

如果您發現重啟後外掛 (Extensions)、模型設定都不見了，**不要緊張！OpenClaw 有自動化備份機制。**

請在伺服器上執行以下整段指令來**「時光倒流」**：

```bash
# 1. 煞車停止
pkill -f openclaw
pkill -f node

# 2. 自動找尋最新的備份檔並還原
node -e "
const fs = require('fs');
const dir = '/root/.openclaw/backups';
if (fs.existsSync(dir)) {
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.json')).sort();
  if (files.length > 0) {
    const latest = dir + '/' + files[files.length - 1];
    console.log('🔄 找到最新備份：' + latest);
    fs.copyFileSync(latest, '/root/.openclaw/openclaw.json');
    console.log('✅ 時光倒流成功！已恢復到最完美的設定。');
  } else {
    console.log('❌ 找不到備份檔。');
  }
} else {
  console.log('❌ 找不到備份資料夾。');
}
"

# 3. 重新啟動
cd "$HOME/openclaw"
nohup npm start -- gateway --allow-unconfigured > /tmp/openclaw.log 2>&1 &
echo "🚀 機器人已經帶著您的舊設定重新復活！"
```



## 🔍 3. 常用的控制台連線指令

1. **忘記密碼？印出 Web UI 登入用的 Token：**
```bash
node -p "const fs=require('fs'); const p1='/root/.openclaw/openclaw.json'; const p2=require('os').homedir()+'/.openclaw/openclaw.json'; const p=fs.existsSync(p1)?p1:p2; let c=require(p); c.gateway && c.gateway.auth ? c.gateway.auth.token : '尚未產生 token'"
```

2. **Web UI 要求裝置配對 (Pairing Required) (一鍵核准版)：**
```bash
cd "$HOME/openclaw"
node -e "const { execSync } = require('child_process'); try { console.log('🔍 尋找待核准裝置...'); const out = execSync('npx openclaw devices list').toString(); const lines = out.split('\n'); let pendingSection = false; let reqId = ''; for(let line of lines) { if(line.includes('Pending')) pendingSection = true; else if(line.includes('Paired')) pendingSection = false; if(pendingSection && line.includes('│')) { const parts = line.split('│'); if(parts.length > 2) { const idPart = parts[1].replace(/\\s+/g, ''); if(/^[a-f0-9\\-]+$/.test(idPart)) reqId += idPart; } } } if(reqId && reqId.length >= 32) { console.log('✅ 找到完整代碼: '+reqId); execSync('npx openclaw devices approve '+reqId, {stdio:'inherit'}); console.log('🎉 核准成功！請重整網頁。'); } else console.log('⚠️ 沒找到待核准的裝置'); } catch(e) { console.error('錯誤:', e.message); }"
```

3. **如果未來更新 OpenClaw，LINE 機器人又開始當機？(一鍵修復 Promise Bug)：**
```bash
node -e "
const fs = require('fs');
const os = require('os');
const file = os.homedir() + '/openclaw/extensions/line/src/channel.ts';
if (!fs.existsSync(file)) { console.log('找不到 line extension，略過修復。'); process.exit(0); }
let code = fs.readFileSync(file, 'utf8');
if(!code.includes('if (ctx.abortSignal?.aborted) return resolve(res);')) {
  code = code.replace(/webhookPath: account\.config\.webhookPath,\s+\}\);/, 'webhookPath: account.config.webhookPath, }).then((res) => new Promise((resolve) => { if (ctx.abortSignal?.aborted) return resolve(res); ctx.abortSignal?.addEventListener(\"abort\", () => resolve(res)); }));');
  fs.writeFileSync(file, code);
  console.log('✅ 成功修復 Promise Bug！');
} else {
  console.log('已經修復過了，無須再執行');
}
"
```

---

## 🩺 4. 系統連線異常：三分鐘快速診斷指南

如果有一天您發現「整個系統完全連不上線」，網頁打不開、LINE 機器人也裝死，請直接照著以下 3 步來查案：

### 第一步：檢查大腦 (OpenClaw) 還活著嗎？
在終端機貼上這行：
```bash
ps aux | grep node
```
* **診斷：** 如果印出來的結果只有一行 `grep node`，代表機器人大腦已經死機了。
* **解法：** 直接去執行 **【🚀 1. 終極一鍵修復與啟動腳本】**，把它整個叫醒重新投胎。

### 第二步：檢查通道 (Cloudflare) 斷線了嗎？
如果大腦還活著，但 LINE 機器人就是不理人，代表極大可能是 Cloudflare 隧道斷了。
貼上這行查看 Cloudflare 的最新日誌：
```bash
tail -n 10 /tmp/cloudflare.log
```
* **診斷：** 如果裡面出現 `connection lost`、`ERR` 等字眼，或者根本沒有網址，代表隧道已經坍方。
* **解法：** 一樣，直接去執行 **【🚀 1. 終極一鍵修復與啟動腳本】**，它會自動把壞掉的隧道挖掉重建。

### 第三步：看看到底是哪裡在報錯？(抓戰犯)
如果大腦和隧道看起來都在運作，代表可能是模型或網路出了問題。請看大雷達紀錄：
```bash
tail -n 30 /tmp/openclaw.log
```
* **診斷：** 這裡會印出 OpenClaw 臨死前或生病時講的最後幾句話 (通常會出現 Error 或 Exception 等英文字)。把這段紅字複製起來貼給 AI (我)，我們就能馬上抓出戰犯對症下藥！
