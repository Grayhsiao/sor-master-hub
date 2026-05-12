#!/bin/bash
# Focus Guard Pro 安裝助手
# 作用：自動解除 macOS 對 App 的安全隔離標籤

# 獲取指令檔所在的目錄
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_PATH="$DIR/FocusGuardPro.app"

echo "------------------------------------------------"
echo "🛡️ Focus Guard Pro 安裝助手"
echo "------------------------------------------------"

if [ -d "$APP_PATH" ]; then
    echo "📦 偵測到程式，正在進行安全授權..."
    
    # 解除隔離標籤
    sudo xattr -cr "$APP_PATH"
    
    echo "✅ 授權完成！現在您可以直接開啟 Focus Guard Pro 了。"
    echo "程式將在 3 秒後為您開啟..."
    sleep 3
    open "$APP_PATH"
else
    echo "❌ 錯誤：找不到 FocusGuardPro.app"
    echo "請確保助手檔案與程式放在同一個資料夾內。"
fi

# 執行完畢後自動關閉視窗
exit
