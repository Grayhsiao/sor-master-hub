import psutil
import subprocess
import threading
import os
import json
import core.config as config

class Enforcer:
    @staticmethod
    def _fix_chrome_permissions():
        """自動修改 Chrome 的 Local State 檔案，開啟 AppleScript JS 權限 (備援用)"""
        if not config.IS_MAC: return
        local_state_path = os.path.expanduser("~/Library/Application Support/Google/Chrome/Local State")
        if not os.path.exists(local_state_path): return
        
        try:
            with open(local_state_path, "r") as f:
                data = json.load(f)
            
            changed = False
            if data.get("apple_events_allowed_javascript_injection") is not True:
                data["apple_events_allowed_javascript_injection"] = True
                changed = True
            
            if changed:
                with open(local_state_path, "w") as f:
                    json.dump(data, f)
                print("🛡️ Focus Guard 已自動優化 Chrome 權限設定")
        except Exception as e:
            print(f"🛡️ 權限優化失敗: {e}")

    @staticmethod
    def redirect_current_tab(tab_id=None, url="https://www.youtube.com"):
        """透過 CDP 將特定的分頁導向首頁，完全避開 macOS 權限限制"""
        if tab_id:
            try:
                import socket as _socket, base64 as _base64, json as _json, struct as _struct, time as _time
                sock = _socket.create_connection(('127.0.0.1', 9222), timeout=3)
                key = _base64.b64encode(b'FGRedirectUrl').decode()
                hs = (f'GET /devtools/page/{tab_id} HTTP/1.1\r\nHost: 127.0.0.1:9222\r\n'
                      f'Upgrade: websocket\r\nConnection: Upgrade\r\n'
                      f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n')
                sock.sendall(hs.encode())
                sock.recv(4096)
                
                # 使用 Page.navigate 將特定的 tab 重新導向
                cmd = _json.dumps({'id': 2, 'method': 'Page.navigate', 'params': {'url': url}})
                data = cmd.encode('utf-8')
                length = len(data)
                header = _struct.pack('BB', 0x81, 0x80 | length) if length < 126 else _struct.pack('!BBH', 0x81, 0xFE, length)
                sock.sendall(header + b'\x00\x00\x00\x00' + data)
                _time.sleep(0.1) # 給 Chrome 一點時間接收指令
                sock.close()
                return True
            except Exception as e:
                print(f"CDP Navigate 失敗: {e}")
                
        # 如果沒有 tab_id（例如 Safari 或是 AppleScript 抓到的），退回原始做法
        if config.IS_MAC:
            scripts = [
                f'tell application "Google Chrome" to set URL of active tab of window 1 to "{url}"',
                f'tell application "Safari" to set URL of current tab of window 1 to "{url}"',
                f'tell application "Arc" to set URL of active tab of window 1 to "{url}"'
            ]
            for script in scripts:
                try:
                    app_name = script.split('"')[1]
                    if subprocess.run(["pgrep", "-f", app_name], capture_output=True).returncode == 0:
                        subprocess.run(["osascript", "-e", script], timeout=2, check=False, capture_output=True)
                except:
                    pass
        return True

    _ANTI_HOVER_JS = r"""
(function() {
    // 移除舊的 style (確保更新後也能重新套用)
    var old = document.getElementById('fg-anti-hover');
    if (old) old.remove();
    window.__fg_ah = false;

    if (window.__fg_ah) return 'already';
    window.__fg_ah = true;

    // 修正版 CSS：#inline-preview-player 是 ID，需加 # 前綴
    var s = document.createElement('style');
    s.id = 'fg-anti-hover';
    s.textContent = [
        'ytd-video-preview { display:none!important; pointer-events:none!important; }',
        'ytd-video-preview-loader { display:none!important; pointer-events:none!important; }',
        '#inline-preview-player { display:none!important; pointer-events:none!important; }',
        'ytd-thumbnail-overlay-video-preview-renderer { display:none!important; pointer-events:none!important; }'
    ].join('\n');
    document.head.appendChild(s);

    // 暴力清除：每 200ms 確認並殺掉預覽影片
    setInterval(function(){
        var player = document.getElementById('inline-preview-player');
        if (player) {
            player.style.setProperty('display', 'none', 'important');
            player.querySelectorAll('video').forEach(function(v){ v.pause(); v.src=''; v.load(); });
        }
        document.querySelectorAll('ytd-video-preview video, ytd-video-preview-loader video').forEach(function(v){
            v.pause(); v.src=''; v.load();
        });
    }, 200);

    return 'activated_v2';
})()
"""

    @staticmethod
    def _cdp_inject(tab_id, js_code):
        """透過 CDP WebSocket 直接注入 JS 到指定分頁"""
        import struct, socket as _socket, base64 as _base64, json as _json
        try:
            sock = _socket.create_connection(('127.0.0.1', 9222), timeout=2)
            key = _base64.b64encode(b'FocusGuardAntiHov').decode()
            hs = (f'GET /devtools/page/{tab_id} HTTP/1.1\r\nHost: 127.0.0.1:9222\r\n'
                  f'Upgrade: websocket\r\nConnection: Upgrade\r\n'
                  f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n')
            sock.sendall(hs.encode())
            resp = sock.recv(4096)
            if b'101' not in resp:
                sock.close(); return False
            data = _json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression': js_code, 'returnByValue': True}}).encode('utf-8')
            length = len(data)
            header = struct.pack('BB', 0x81, 0x80 | length) if length < 126 else struct.pack('!BBH', 0x81, 0xFE, length)
            sock.sendall(header + b'\x00\x00\x00\x00' + data)
            import time as _time; _time.sleep(0.3)
            sock.recv(65536)
            sock.close()
            return True
        except:
            return False

    @staticmethod
    def inject_anti_hover_via_cdp():
        """取得所有 YouTube 分頁並注入防懸停腳本（立即生效）"""
        try:
            import requests as _req
            r = _req.get('http://127.0.0.1:9222/json/list', timeout=0.5)
            if not r.ok: return
            for tab in r.json():
                if tab.get('type') == 'page' and 'youtube.com' in tab.get('url', ''):
                    Enforcer._cdp_inject(tab['id'], Enforcer._ANTI_HOVER_JS)
        except:
            pass

    @staticmethod
    def setup_persistent_anti_hover():
        """使用 Page.addScriptToEvaluateOnNewDocument 讓防懸停腳本在每次頁面載入時自動執行"""
        import struct as _struct, socket as _socket, base64 as _base64, json as _json, time as _time
        try:
            import requests as _req
            r = _req.get('http://127.0.0.1:9222/json/list', timeout=1)
            if not r.ok: return False
            tabs = [t for t in r.json() if t.get('type') == 'page' and 'youtube.com' in t.get('url', '')]
            if not tabs:
                # 試第一個 page 分頁
                tabs = [t for t in r.json() if t.get('type') == 'page']
            if not tabs: return False

            tab_id = tabs[0]['id']
            sock = _socket.create_connection(('127.0.0.1', 9222), timeout=3)
            key = _base64.b64encode(b'FGPersistAntiHovr').decode()
            hs = (f'GET /devtools/page/{tab_id} HTTP/1.1\r\nHost: 127.0.0.1:9222\r\n'
                  f'Upgrade: websocket\r\nConnection: Upgrade\r\n'
                  f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n')
            sock.sendall(hs.encode())
            sock.recv(4096)

            cmd = _json.dumps({'id': 1, 'method': 'Page.addScriptToEvaluateOnNewDocument',
                               'params': {'source': Enforcer._ANTI_HOVER_JS}})
            data = cmd.encode('utf-8')
            length = len(data)
            header = _struct.pack('BB', 0x81, 0x80 | length) if length < 126 else _struct.pack('!BBH', 0x81, 0xFE, length)
            sock.sendall(header + b'\x00\x00\x00\x00' + data)
            _time.sleep(0.5)
            sock.recv(65536)
            sock.close()
            print("🛡️ 持久防懸停腳本已登記（重整頁面也有效）")
            return True
        except Exception as e:
            print(f"⚠️ 持久腳本登記失敗: {e}")
            return False

    @staticmethod
    def kill_game_process():
        """關閉遊戲進程"""
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name'].lower()
                if any(game in name for game in ["roblox", "minecraft", "steam"]):
                    proc.kill()
                    return True
            except: pass
        return False

# 啟動時自動檢查一次權限
Enforcer._fix_chrome_permissions()
