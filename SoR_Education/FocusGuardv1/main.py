import sys
import os
import traceback
from datetime import datetime
import uuid
import requests

# [Diagnostic] 最優先：一啟動就寫入檔案，確認程式碼有被執行
CRASH_LOG = os.path.join(os.path.expanduser("~"), "focus_guard_crash.log")
try:
    with open(CRASH_LOG, "a", encoding='utf-8') as f:
        f.write(f"\n--- [{datetime.now()}] 程式嘗試啟動 ---\n")
except:
    pass

import logging
import tkinter as tk
from tkinter import messagebox, simpledialog
import psutil
import time
import threading
import platform

try:
    global_skills_path = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..', 'Global_Skills', 'remote_control'))
    if global_skills_path not in sys.path:
        sys.path.insert(0, global_skills_path)
except Exception:
    pass

try:
    from remote_control import RemoteControl
except Exception as e:
    try:
        with open(CRASH_LOG, "a", encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] 匯入 remote_control 失敗: {e}\n")
    except: pass
    RemoteControl = None


# 嘗試匯入 Pillow
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("警告: 找不到 Pillow，將使用原生 PhotoImage (可能不支援透明度)")

# 嘗試匯入 pygame (用於播放音效)
try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False
    print("警告: 找不到 pygame，將無法播放音效")
    
# --- 設定 ---
PIN_CODE = "1234"
BLACKLIST = [
    "minecraft", "roblox", "steam", 
    # "safari", "chrome", "google chrome", "microsoft edge", "msedge", "firefox", "brave", "opera", # 測試期間暫不阻擋瀏覽器
    "discord", "spotify",
    "fortnite", "league of legends", "valorant",
    "atlauncher", "curseforge", "gdlauncher", "multimc", "prismlauncher", "technic", "lunar",
    "overwolf", "javaw", "java"
]
FIREBASE_URL = "https://studybuddy-a2dcc-default-rtdb.asia-southeast1.firebasedatabase.app/"

# [Fix] 將 Log 檔存放在使用者的家目錄下，避免因為權限不足導致 App 閃退
LOG_FILE = os.path.join(os.path.expanduser("~"), "focus_activity.log")

def resource_path(relative_path):
    """ 取得資源的絕對路徑 """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class FocusGuardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Andy Doll Focus")
        
        # 設定 Logging
        logging.basicConfig(filename=LOG_FILE, level=logging.INFO, 
                            format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
        # 初始化 Pygame Mixer
        if HAS_PYGAME:
            try:
                pygame.mixer.init()
            except Exception as e:
                print(f"Pygame init failed: {e}")

        # 1. 移除標題列 (舊方法: overrideredirect)
        # self.root.overrideredirect(True)
        # [Fix] 改用 Windows API 去除邊框，保留 Alt+Tab 功能
        if platform.system() == "Windows":
             self.root.overrideredirect(False) # 保持為標準視窗
        else:
             self.root.overrideredirect(True)
        
        
        # 2. 處理透明背景 (平台差異)
        # [System Check] Windows 需要使用特定的透明顏色鍵值
        self.os_type = platform.system()
        # [Fix] 使用特定顏色作為透明鍵值，而非粉紅色本身
        self.transparent_key = '#000001' # 幾乎全黑，作為透明色鍵
        self.doll_bg_color = '#FFD1DC' # 安迪粉色 (實體顏色)

        if self.os_type == "Windows":
             # Windows: 設定視窗背景為透明鍵值，並設定該鍵值為透明
             self.root.config(bg=self.transparent_key)
             self.root.wm_attributes('-transparentcolor', self.transparent_key)
             # [Fix] 呼叫設定函式去除邊框
             self.root.after(100, self.set_app_window)
        elif self.os_type == "Darwin":
             # Mac: 使用系統透明
             self.root.wm_attributes("-transparent", True)
             self.root.config(bg='systemTransparent')

        # 變數初始化
        self.is_running = False
        self.time_left = 60 
        self.bg_image = None
        self.canvas_windows = []
        self.widgets_to_destroy = [] # [New] 強制追蹤並銷毀所有元件物件
        self.remote_ctrl = None
        self.classroom_code = ""

        self.student_id = self.get_or_create_student_id()
        self.student_name = self.get_or_create_student_name()
        self.coins = 0
        self.load_coins_async()

        # 載入背景
        self.setup_ui()
        
    def get_or_create_student_id(self):
        id_file = os.path.join(os.path.expanduser("~"), ".andy_student_id")
        if os.path.exists(id_file):
            with open(id_file, "r") as f:
                return f.read().strip()
        new_id = str(uuid.uuid4())[:8] # 取前8碼當作學生匿名ID
        with open(id_file, "w") as f:
            f.write(new_id)
        return new_id

    def get_or_create_student_name(self):
        name_file = os.path.join(os.path.expanduser("~"), ".andy_student_name")
        if os.path.exists(name_file):
            with open(name_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        return ""

    def save_student_name(self, name):
        self.student_name = name
        name_file = os.path.join(os.path.expanduser("~"), ".andy_student_name")
        with open(name_file, "w", encoding="utf-8") as f:
            f.write(name)

    def load_coins_async(self):
        def fetch():
            try:
                url = f"{FIREBASE_URL}/students/{self.student_id}/coins.json"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200 and resp.json() is not None:
                    self.coins = int(resp.json())
                self.root.after(0, self.update_coin_display)
            except:
                pass
        threading.Thread(target=fetch, daemon=True).start()

    def save_coins_async(self):
        def push():
            try:
                url = f"{FIREBASE_URL}/students/{self.student_id}/coins.json"
                requests.put(url, json=self.coins, timeout=5)
            except:
                pass
        threading.Thread(target=push, daemon=True).start()

    def update_coin_display(self):
        if hasattr(self, 'lbl_coins') and self.lbl_coins.winfo_exists():
            self.lbl_coins.config(text=f"💰 我的安迪幣: {self.coins}")
        # 當點數更新時，如果已經在教室內，順便更新排行榜上的點數
        if self.classroom_code:
            self.update_presence()

    def update_presence(self):
        if not self.classroom_code: return
        def push():
            try:
                url = f"{FIREBASE_URL}/classrooms/{self.classroom_code}/students/{self.student_id}.json"
                data = {
                    "name": self.student_name,
                    "coins": self.coins,
                    "last_active": time.time()
                }
                requests.put(url, json=data, timeout=5)
            except Exception as e:
                print(f"Presence update error: {e}")
        threading.Thread(target=push, daemon=True).start()

    def log_activity(self, message):
        """ 記錄活動到 Log 檔案 """
        try:
            print(f"[LOG] {message}")
            logging.info(message)
        except Exception as e:
            print(f"Logging failed: {e}")

    def play_start_sound(self):
        """ 播放開始音效 """
        if not HAS_PYGAME: return
        try:
            sound_path = resource_path("start_sound.mp3") # 預設尋找 start_sound.mp3
            if os.path.exists(sound_path):
                pygame.mixer.music.load(sound_path)
                pygame.mixer.music.play()
            else:
                print("找不到音效檔: start_sound.mp3")
        except Exception as e:
            print(f"播放音效失敗: {e}")

    def setup_ui(self):
        # 嘗試載入圖片
        img_path = resource_path("andy_doll.png")
        if os.path.exists(img_path):
            try:
                if HAS_PIL:
                    pil_image = Image.open(img_path)
                    
                    # [Fix] 縮小圖片尺寸 (0.35 => 約 336x336)
                    scale_factor = 0.35
                    new_w = int(pil_image.width * scale_factor)
                    new_h = int(pil_image.height * scale_factor)
                    pil_image = pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    
                    self.bg_image = ImageTk.PhotoImage(pil_image)
                    w = new_w
                    h = new_h
                else:
                    self.bg_image = tk.PhotoImage(file=img_path)
                    w = self.bg_image.width()
                    h = self.bg_image.height()
                
                # 設定視窗大小與位置
                ws = self.root.winfo_screenwidth()
                hs = self.root.winfo_screenheight()
                x = int((ws/2) - (w/2))
                y = int((hs/2) - (h/2))
                self.root.geometry(f'{w}x{h}+{x}+{y}')
                
                # [Design] 改回 "systemTransparent" 讓四個角落變透明
                # [Fix] 設定 Canvas 背景
                if self.os_type == "Darwin":
                    canvas_bg = 'systemTransparent'
                else:
                    # Windows: Canvas 背景設為透明鍵值，這樣 Canvas 沒畫東西的地方就會透視過去
                    canvas_bg = self.transparent_key
                
                self.canvas = tk.Canvas(self.root, width=w, height=h, bg=canvas_bg, highlightthickness=0)
                self.canvas.pack(fill='both', expand=True)
                
                # [Draw] 手動繪製娃娃形狀 (粉色底)
                # 使用 self.doll_bg_color 畫出實體形狀
                self.canvas.create_oval(10, 10, w-10, h-10, fill=self.doll_bg_color, outline='')
                
                # [Draw] 繪製背景圖 (安迪娃娃)
                # 再次大幅上移，為底部按鈕預留絕對安全區
                self.canvas.create_image(w/2, h*0.37, image=self.bg_image, anchor='center')
                
                # 綁定拖曳
                self.canvas.bind("<Button-1>", self.start_move)
                self.canvas.bind("<B1-Motion>", self.do_move)
                
            except Exception as e:
                print(f"Error loading image: {e}")
                self.fallback_ui(str(e))
        else:
            self.fallback_ui("Image not found")
            
        self.show_input_mode()
    
    # ... (Keep existing methods: fallback_ui, start_move, do_move, clear_canvas_widgets, etc.) ...

    def fallback_ui(self, error_msg):
        self.root.geometry("400x500")
        self.root.configure(bg="#FFD1DC")
        lbl = tk.Label(self.root, text=f"Andy Doll Missing\n{error_msg}", bg="#FFD1DC")
        lbl.pack(expand=True)
        self.canvas = None

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def clear_canvas_widgets(self):
        """ 徹底銷毀畫面上所有的 Tkinter 元件物件與畫布窗口 """
        # 1. 銷毀實體物件
        for widget in self.widgets_to_destroy:
            try:
                widget.destroy()
            except:
                pass
        self.widgets_to_destroy = []

        # 2. 刪除畫布窗口 (Canvas Window IDs)
        if self.canvas:
            for win_id in self.canvas_windows:
                try:
                    self.canvas.delete(win_id)
                except:
                    pass
            self.canvas_windows = []

    def add_common_ui_elements(self):
        """ 在畫面上加入通用的關閉按鈕與版本標記 (確保都能被銷毀) """
        w = self.bg_image.width()
        h = self.bg_image.height()
        cx = w / 2

        # 1. 物理電燈開關 (矩形搖臂式)
        self.switch_frame = tk.Canvas(self.canvas, width=40, height=50, bg=self.doll_bg_color, 
                                     highlightthickness=0, cursor="hand2")
        self.switch_on = True 
        
        # 繪製開關底座
        self.switch_frame.create_rectangle(2, 2, 38, 48, fill="#e2e8f0", outline="#cbd5e1")
        # 繪製搖臂 (ON 狀態：上方壓平，下方突起)
        self.sw_top = self.switch_frame.create_polygon(5, 5, 35, 5, 35, 25, 5, 25, fill="#f8fafc", outline="#94a3b8")
        self.sw_btm = self.switch_frame.create_polygon(5, 25, 35, 25, 35, 45, 5, 45, fill="#cbd5e1", outline="#94a3b8")
        # 狀態燈 (綠色)
        self.sw_light = self.switch_frame.create_oval(17, 22, 23, 28, fill="#4ade80", outline="")

        self.switch_frame.bind("<Button-1>", lambda e: self.toggle_close())
        
        # 放置在娃娃右側 (同步上移)
        win_id = self.canvas.create_window(w * 0.88, h * 0.37, window=self.switch_frame, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(self.switch_frame)

        # 2. 版本標記 (底部上移，避免被圓邊切掉)
        lbl_v = tk.Label(self.canvas, text="v2.8 (Full Safe Mode)", font=("Arial", 7), bg=self.doll_bg_color, fg="#cbd5e1")
        win_id = self.canvas.create_window(cx, h - 35, window=lbl_v, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(lbl_v)

    def show_input_mode(self):
        if not self.canvas: return
        self.clear_canvas_widgets()
        
        # 取得中心點
        w = self.bg_image.width()
        h = self.bg_image.height()
        cx = w / 2
        # 將 UI 再次上移至 58% 處，騰出約 40% 的底部安全地帶
        ui_base_y = h * 0.58 
        
        # 0. 安迪幣顯示
        self.lbl_coins = tk.Label(self.canvas, text=f"💰 我的安迪幣: {self.coins}", font=("Microsoft JhengHei", 10, "bold"), 
                                  bg=self.doll_bg_color, fg="#b45309")
        win_id = self.canvas.create_window(cx, ui_base_y - 60, window=self.lbl_coins, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(self.lbl_coins)

        # 1. 標籤
        lbl = tk.Label(self.canvas, text="設定專注時間 (分鐘)", font=("Microsoft JhengHei", 10, "bold"), 
                       bg=self.doll_bg_color, fg="#334155")
        win_id = self.canvas.create_window(cx, ui_base_y - 28, window=lbl, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(lbl)
        
        # 2. 輸入框
        self.entry_duration = tk.Entry(self.canvas, font=("Inter", 14, "bold"), width=3, 
                                       justify='center', bd=0, highlightthickness=1,
                                       highlightbackground="#cbd5e1", highlightcolor="#10b981")
        self.entry_duration.insert(0, "30")
        win_id = self.canvas.create_window(cx, ui_base_y, window=self.entry_duration, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(self.entry_duration)
        
        # 3. 按鈕 (縮小尺寸並改為深色文字以提升視覺對比)
        btn = tk.Button(self.canvas, text=" 🚀 啟動專注計時 ", command=self.start_focus,
                        bg="#10b981", fg="black", font=("Microsoft JhengHei", 10, "bold"),
                        relief="flat", cursor="hand2", padx=8, pady=3)
        win_id = self.canvas.create_window(cx, ui_base_y + 40, window=btn, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(btn)

        # 5. 遠端教室模式按鈕
        btn_remote = tk.Button(self.canvas, text=" 🏫 進入遠端教室 ", command=self.show_classroom_mode,
                               bg="#3b82f6", fg="black", font=("Microsoft JhengHei", 10, "bold"),
                               relief="flat", cursor="hand2", padx=8, pady=3)
        win_id = self.canvas.create_window(cx, ui_base_y + 75, window=btn_remote, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(btn_remote)

        # 4. [New] 顯示最近的紀錄 (罪證確鑿區)
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r", encoding='utf-8') as f:
                    lines = f.readlines()
                    last_3 = lines[-3:] if len(lines) > 3 else lines
                
                log_text = "最近紀錄:\n"
                for line in last_3:
                    parts = line.split(" - ")
                    if len(parts) >= 2:
                        time_str = parts[0].split(" ")[1] 
                        msg = parts[1].strip()
                        if "Stopped" in msg or "Unlock" in msg:
                            icon = "❌"; display_msg = "中斷"
                        elif "Completed" in msg:
                            icon = "✅"; display_msg = "完成"
                        else: continue
                        log_text += f"{time_str} {icon} {display_msg}\n"
                
                lbl_log = tk.Label(self.canvas, text=log_text, font=("Microsoft JhengHei", 8), 
                                   bg=self.doll_bg_color, fg="#94a3b8", justify="left")
                win_id = self.canvas.create_window(cx, ui_base_y + 90, window=lbl_log, anchor='center')
                self.canvas_windows.append(win_id)
                self.widgets_to_destroy.append(lbl_log)
        except Exception as e:
            print(f"Read log failed: {e}")

        # 加入通用元件
        self.add_common_ui_elements()

    def show_timer_mode(self):
        if not self.canvas: return
        self.clear_canvas_widgets()
        
        w = self.bg_image.width()
        h = self.bg_image.height()
        cx = w / 2
        cy = h * 0.55
        
        self.lbl_timer = tk.Label(self.canvas, text=" ⌛ 剩餘時間 \n00:00:00", 
                                 font=("Inter", 18, "bold"), bg="white", fg="#1e293b")
        win_id = self.canvas.create_window(cx, cy - 15, window=self.lbl_timer, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(self.lbl_timer)
        
        btn_unlock = tk.Button(self.canvas, text=" 🔓 解鎖 (Unlock) ", command=self.unlock_focus,
                               bg="#f87171", fg="white", font=("Microsoft JhengHei", 10, "bold"),
                               relief="flat", cursor="hand2", padx=10, pady=5)
        win_id = self.canvas.create_window(cx, cy + 50, window=btn_unlock, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(btn_unlock)

        self.add_common_ui_elements()

    def start_focus(self):
        try:
            minutes = int(self.entry_duration.get())
            if minutes <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的分鐘數")
            return
            
        self.time_left = minutes * 60
        self.is_running = True
        
        self.log_activity(f"Start Focus: {minutes} minutes")
        self.play_start_sound()
        
        self.show_timer_mode()
        
        # 啟動監控線程
        self.monitor_thread = threading.Thread(target=self.monitor_processes)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.update_timer()

    def update_timer(self):
        if self.is_running and self.time_left > 0:
            m, s = divmod(self.time_left, 60)
            h, m = divmod(m, 60)
            if hasattr(self, 'lbl_timer'):
                self.lbl_timer.config(text=f"剩餘時間:\n{h:02}:{m:02}:{s:02}")
            self.time_left -= 1
            self.root.after(1000, self.update_timer)
        elif self.time_left <= 0 and self.is_running:
            self.timer_completed()
            
    def timer_completed(self):
        self.log_activity("Focus Completed Successfully")
        self.is_running = False
        self.stop_focus()
        messagebox.showinfo("完成", "專注時間結束！")

    def unlock_focus(self):
        pin = simpledialog.askstring("解鎖", "輸入 PIN 碼:", show="*", parent=self.root)
        if pin == PIN_CODE:
            self.log_activity("Focus Stopped: Unlocked by PIN")
            self.stop_focus()
        else:
            if pin is not None: 
                self.log_activity("Unlock Failed: Wrong PIN")
                messagebox.showerror("錯誤", "PIN 碼錯誤")

    def stop_focus(self):
        self.is_running = False
        if self.remote_ctrl:
            self.remote_ctrl.stop()
            self.remote_ctrl = None
        self.show_input_mode()

    def show_classroom_mode(self):
        if not self.canvas: return
        self.clear_canvas_widgets()
        
        w = self.bg_image.width()
        h = self.bg_image.height()
        cx = w / 2
        ui_base_y = h * 0.53

        # 姓名輸入
        lbl_name = tk.Label(self.canvas, text="輸入你的英文名字 (簽到用)", font=("Microsoft JhengHei", 10, "bold"), 
                       bg=self.doll_bg_color, fg="#1e40af")
        win_id = self.canvas.create_window(cx, ui_base_y - 28, window=lbl_name, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(lbl_name)
        
        self.entry_student_name = tk.Entry(self.canvas, font=("Inter", 12, "bold"), width=12, 
                                           justify='center', bd=0, highlightthickness=1)
        self.entry_student_name.insert(0, self.student_name)
        win_id = self.canvas.create_window(cx, ui_base_y, window=self.entry_student_name, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(self.entry_student_name)

        # 教室代碼輸入
        lbl = tk.Label(self.canvas, text="輸入教室代碼", font=("Microsoft JhengHei", 10, "bold"), 
                       bg=self.doll_bg_color, fg="#1e40af")
        win_id = self.canvas.create_window(cx, ui_base_y + 35, window=lbl, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(lbl)
        
        self.entry_class_code = tk.Entry(self.canvas, font=("Inter", 14, "bold"), width=8, 
                                         justify='center', bd=0, highlightthickness=1,
                                         highlightbackground="#cbd5e1", highlightcolor="#3b82f6")
        win_id = self.canvas.create_window(cx, ui_base_y + 60, window=self.entry_class_code, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(self.entry_class_code)
        
        # [Fix] 解決 Mac 上 Entry 無法輸入的問題
        self.root.after(100, lambda: self.entry_student_name.focus_force())
        
        btn_join = tk.Button(self.canvas, text=" 🚀 立即加入教室 ", command=self.join_classroom,
                             bg="#3b82f6", fg="black", font=("Microsoft JhengHei", 10, "bold"),
                             relief="flat", cursor="hand2", padx=10, pady=4)
        win_id = self.canvas.create_window(cx, ui_base_y + 100, window=btn_join, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(btn_join)
        
        btn_back = tk.Button(self.canvas, text=" ⬅ 返回主選單 ", command=self.show_input_mode, 
                             bg=self.doll_bg_color, fg="#1e293b", font=("Microsoft JhengHei", 9), 
                             relief="flat", cursor="hand2")
        win_id = self.canvas.create_window(cx, ui_base_y + 135, window=btn_back, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(btn_back)

        self.add_common_ui_elements()

    def join_classroom(self):
        name = self.entry_student_name.get().strip()
        if not name:
            messagebox.showerror("錯誤", "請先輸入你的英文名字！")
            return
        
        code = self.entry_class_code.get().strip().upper()
        if not code:
            messagebox.showerror("錯誤", "請輸入教室代碼")
            return
        
        self.save_student_name(name)
        self.classroom_code = code
        self.log_activity(f"Joining Classroom: {code} as {name}")
        
        # 報到
        self.update_presence()
        
        # 初始化遠端控制，加入全班名單回呼
        self.remote_ctrl = RemoteControl(FIREBASE_URL, self.classroom_code)
        self.remote_ctrl.start(self.on_remote_status_change, self.on_remote_event, self.on_students_update)
        
        self.show_remote_waiting_mode()

    def show_remote_waiting_mode(self):
        self.clear_canvas_widgets()
        cx = self.bg_image.width() / 2
        cy = self.bg_image.height() * 0.55
        
        lbl = tk.Label(self.canvas, text=f"已連線教室: {self.classroom_code}\n等待老師指令...", 
                       font=("Microsoft JhengHei", 12, "bold"), bg="white")
        win_id = self.canvas.create_window(cx, cy, window=lbl, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(lbl)
        
        btn_exit = tk.Button(self.canvas, text="退出教室", command=self.stop_focus, 
                             font=("Microsoft JhengHei", 9))
        win_id = self.canvas.create_window(cx, cy + 60, window=btn_exit, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(btn_exit)

        # 排行榜標籤預留位置
        self.lbl_leaderboard = tk.Label(self.canvas, text="線上名單載入中...", justify="left",
                                        font=("Microsoft JhengHei", 9), bg=self.doll_bg_color, fg="#334155")
        win_id = self.canvas.create_window(cx, cy + 105, window=self.lbl_leaderboard, anchor='n')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(self.lbl_leaderboard)

        self.add_common_ui_elements()

    def on_students_update(self, students_dict):
        """ 處理老師面板傳來的在線學生排行榜更新 """
        if not hasattr(self, 'lbl_leaderboard') or not self.lbl_leaderboard.winfo_exists(): return
        if not students_dict: return
        
        # 依照安迪幣排序
        sorted_students = sorted(students_dict.items(), key=lambda x: x[1].get('coins', 0), reverse=True)
        
        # 只取前 3 名
        lb_text = "🏆 全班金幣排行榜 🏆\n"
        for i, (sid, data) in enumerate(sorted_students[:3]):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
            coins = data.get('coins', 0)
            name = data.get('name', 'Unknown')
            lb_text += f"{medal} {name}: {coins} 幣\n"
            
        self.root.after(0, lambda: self.lbl_leaderboard.config(text=lb_text))

    def on_remote_status_change(self, status):
        """ 當雲端狀態改變時觸發 """
        self.log_activity(f"Remote Status Change: {status}")
        
        if status == "LOCKED":
            if not self.is_running:
                # 由老師發起的鎖定
                self.root.after(0, self.start_remote_lock)
        else:
            if self.is_running:
                # 由老師發起的解鎖
                self.root.after(0, self.stop_remote_lock)

    def on_remote_event(self, event_type, payload, target="ALL", target_display="全班"):
        """ 處理老師廣播的事件 """
        # [New] 過濾目標：如果 target 不是發給所有人，也不是發給自己，就忽略
        if target != 'ALL' and target != self.student_id:
            return
            
        label = "👨‍🏫 老師廣播給" + target_display
        self.log_activity(f"Remote Event: {event_type} - {payload} (Target: {target})")
        if event_type == "MESSAGE":
            self.root.after(0, lambda: messagebox.showinfo(label, payload))
        elif event_type == "COIN":
            self.coins += 50
            self.save_coins_async()
            self.root.after(0, lambda: messagebox.showinfo("🎉 專屬獎勵！", f"{payload}\n\n目前總計: {self.coins} 安迪幣"))
            self.root.after(0, self.update_coin_display)

    def start_remote_lock(self):
        self.is_running = True
        self.play_start_sound()
        
        # 顯示鎖定畫面 (老師控制中)
        self.clear_canvas_widgets()
        cx = self.bg_image.width() / 2
        cy = self.bg_image.height() * 0.55
        
        lbl = tk.Label(self.canvas, text="⚠️ 老師已開啟專注模式\n請認真上課", 
                       font=("Microsoft JhengHei", 14, "bold"), fg="red", bg="white")
        win_id = self.canvas.create_window(cx, cy, window=lbl, anchor='center')
        self.canvas_windows.append(win_id)
        self.widgets_to_destroy.append(lbl)

        self.add_common_ui_elements()
        
        # 啟動監控
        self.monitor_thread = threading.Thread(target=self.monitor_processes)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_remote_lock(self):
        self.is_running = False
        messagebox.showinfo("下課", "老師已解除鎖定，下課休息囉！")
        self.show_remote_waiting_mode()

    def monitor_processes(self):
        while self.is_running:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # 取得小寫的程序名稱 (例如 "chrome.exe")
                    p_name = proc.info['name'].lower()
                    
                    # [Fix] 檢查 BLACKLIST 中的關鍵字是否出現在程序名稱中
                    # 例如: BLACKLIST 有 "chrome"，則 "chrome.exe" 會被匹配到
                    for blocked_keyword in BLACKLIST:
                        if blocked_keyword in p_name:
                             # self.log_activity(f"Blocked Process: {p_name}") 
                             try:
                                 proc.kill()
                             except (psutil.NoSuchProcess, psutil.AccessDenied):
                                 # 忽略無法存取或已經結束的程序
                                 pass
                             break # 只要命中一個關鍵字就阻擋，跳出內層迴圈檢查下一個 process
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                except Exception:
                    pass
            time.sleep(3)

    def toggle_close(self):
        """ 處理開關切換視覺效果並觸發關閉 (物理電燈開關版) """
        if not self.switch_on: return 
        
        # 1. 執行切換視覺感：下方壓入，上方翹起
        self.switch_frame.itemconfig(self.sw_top, fill="#cbd5e1") # 上方變暗
        self.switch_frame.itemconfig(self.sw_btm, fill="#f8fafc") # 下方變亮
        self.switch_frame.itemconfig(self.sw_light, fill="#94a3b8") # 燈滅
        self.switch_on = False
        
        self.root.after(300, self.on_closing)

    def on_closing(self):
        if self.is_running:
            pin = simpledialog.askstring("關閉確認", "目前正在專注中！\n請輸入 PIN 碼以切換開關:", show="*", parent=self.root)
            if pin == PIN_CODE:
                 self.log_activity("App Closed: Unlocked by Light Switch")
                 self.root.destroy()
            else:
                 # 復原開關狀態 (ON)
                 self.switch_frame.itemconfig(self.sw_top, fill="#f8fafc")
                 self.switch_frame.itemconfig(self.sw_btm, fill="#cbd5e1")
                 self.switch_frame.itemconfig(self.sw_light, fill="#4ade80")
                 self.switch_on = True
                 if pin is not None: 
                      messagebox.showerror("錯誤", "PIN 碼錯誤，開關已彈回")
                 return
        else:
             if messagebox.askokcancel("關閉", "確定要關閉 FocusGuard 嗎？"):
                 self.root.destroy()
             else:
                 # 復原
                 self.switch_frame.itemconfig(self.sw_top, fill="#f8fafc")
                 self.switch_frame.itemconfig(self.sw_btm, fill="#cbd5e1")
                 self.switch_frame.itemconfig(self.sw_light, fill="#4ade80")
                 self.switch_on = True

    # [Fix] 設定視窗屬性 (去除標題列但保留 Taskbar)
    def set_app_window(self):
        if self.os_type != "Windows": return
        try:
             import ctypes
             # 取得視窗句柄
             hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
             
             # 取得目前樣式
             GWL_STYLE = -16
             style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
             
             # 移除標題列 (WS_CAPTION) 和 厚邊框 (WS_THICKFRAME)
             WS_CAPTION = 0x00C00000
             WS_THICKFRAME = 0x00040000
             
             style = style & ~WS_CAPTION
             style = style & ~WS_THICKFRAME
             
             ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style)
             
             # 強制刷新
             # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
             SWP_FLAGS = 0x0001 | 0x0002 | 0x0004 | 0x0020
             ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_FLAGS)
             
        except Exception as e:
             self.log_activity(f"Failed to set window style: {e}")

if __name__ == "__main__":
    try:
        if sys.platform.startswith('win'):
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass

        root = tk.Tk()
        app = FocusGuardApp(root)
        root.mainloop()
    except Exception as e:
        with open(CRASH_LOG, "a") as f:
            f.write(f"{datetime.now()} - GLOBAL CRASH: {e}\n{traceback.format_exc()}\n")
        # 如果是圖形介面，嘗試彈出錯誤
        try:
            import tkinter.messagebox as mb
            mb.showerror("程式啟動失敗", f"遭遇嚴重錯誤，請檢查日誌: {CRASH_LOG}\n錯誤內容: {e}")
        except:
            pass
