import pygame
import pyaudio
import numpy as np
import threading
import time

# ==========================================
# 1. 核心常數與設定
# ==========================================
WIDTH, HEIGHT = 1000, 500
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (200, 200, 200)
RED = (255, 80, 80)
GREEN = (80, 255, 80)
BLUE = (80, 80, 255)
HIGHLIGHT = (230, 240, 255)

# 聲音參數
CHUNK = 4096  # 增加緩衝區大小以提高頻率解析度
RATE = 44100
THRESHOLD = 1000 

# 音符頻率 (C4 - B4)
NOTES_FREQ = {
    'C4': 261.63, 'C#4': 277.18, 'D4': 293.66, 'D#4': 311.13,
    'E4': 329.63, 'F4': 349.23, 'F#4': 369.99, 'G4': 392.00,
    'G#4': 415.30, 'A4': 440.00, 'A#4': 466.16, 'B4': 493.88
}
SHEET_MUSIC = ['C4', 'C4', 'G4', 'G4', 'A4', 'A4', 'G4']

# ==========================================
# 2. 模組化組件
# ==========================================

class AudioEngine:
    """負責音訊輸入與頻率分析"""
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.current_note = None
        self.is_running = False
        self.window = np.hanning(CHUNK) # 減少 FFT 的邊緣效應

    def start(self, callback):
        self.is_running = True
        t = threading.Thread(target=self._listen, args=(callback,), daemon=True)
        t.start()

    def _listen(self, callback):
        try:
            self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=RATE, 
                                     input=True, frames_per_buffer=CHUNK)
            while self.is_running:
                data = np.frombuffer(self.stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
                volume = np.sqrt(np.mean(data**2))
                
                if volume > THRESHOLD:
                    # 應用 Hanning Window 並執行 FFT
                    windowed_data = data * self.window
                    fft_data = np.fft.rfft(windowed_data)
                    fft_freq = np.fft.rfftfreq(CHUNK, 1.0/RATE)
                    magnitude = np.abs(fft_data)
                    peak_freq = fft_freq[np.argmax(magnitude)]
                    
                    note = self._get_note_from_freq(peak_freq)
                    if note:
                        self.current_note = note
                        callback(note)
                        time.sleep(0.1) # 簡單防抖
                else:
                    self.current_note = None
        except Exception as e:
            print(f"Audio Error: {e}")

    def _get_note_from_freq(self, freq):
        if freq < 200: return None
        min_dist = float('inf')
        closest = None
        for note, f in NOTES_FREQ.items():
            dist = abs(freq - f)
            if dist < min_dist:
                min_dist = dist
                closest = note
        return closest if min_dist < 10 else None

    def stop(self):
        self.is_running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

class GameLogic:
    """負責追蹤樂譜、分數與遊戲狀態"""
    def __init__(self, sheet):
        self.sheet = sheet
        self.target_index = 0
        self.score = 0
        self.feedback = "Ready to start! Play C4"
        self.feedback_color = BLACK

    def check_note(self, note):
        if self.target_index >= len(self.sheet): return

        target = self.sheet[self.target_index]
        if note == target:
            self.target_index += 1
            self.score += 10
            self.feedback = f"✅ 讚啦！彈對了 {note}"
            self.feedback_color = GREEN
            if self.target_index >= len(self.sheet):
                self.feedback = f"🎉 太厲害了！全曲完成！最終得分: {self.score}"
                self.feedback_color = BLUE
        else:
            self.feedback = f"❌ 哎呀！聽到的是 {note}，要彈的是 {target}"
            self.feedback_color = RED

class PianoUI:
    """負責 Pygame 介面呈現"""
    def __init__(self, width, height):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("大叔鋼琴教練 V2")
        self.font_main = pygame.font.SysFont(['microsoftjhengheimbold', 'arial'], 32)
        self.font_big = pygame.font.SysFont(['microsoftjhengheimbold', 'arial'], 48)
        self.key_w = 100
        self.start_x = (width - 7 * self.key_w) // 2

    def draw(self, game, current_note):
        self.screen.fill(WHITE)
        
        # 繪製題目資訊
        score_surface = self.font_main.render(f"得分: {game.score}", True, BLACK)
        self.screen.blit(score_surface, (50, 30))

        if game.target_index < len(game.sheet):
            target_note = game.sheet[game.target_index]
            hint_text = f"目前目標: {target_note}"
            hint_surface = self.font_big.render(hint_text, True, BLUE)
            self.screen.blit(hint_surface, (350, 20))
        
        # 繪製鋼琴鍵
        notes = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4']
        for i, note in enumerate(notes):
            rect = pygame.Rect(self.start_x + i * self.key_w, 150, self.key_w - 2, 250)
            color = WHITE
            
            # 提示音藍色
            if game.target_index < len(game.sheet):
                if game.sheet[game.target_index] == note:
                    color = HIGHLIGHT
            
            # 正在彈奏黃色
            if current_note == note:
                color = (255, 255, 100)

            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, BLACK, rect, 2)
            
            # 音名
            text_color = BLACK if current_note != note else RED
            label = self.font_main.render(note, True, text_color)
            self.screen.blit(label, (rect.centerx - 20, rect.bottom - 40))

        # 繪製黑鍵 (僅供裝飾)
        black_indices = [0.7, 1.7, 3.7, 4.7, 5.7]
        for idx in black_indices:
            rect = pygame.Rect(self.start_x + idx * self.key_w, 150, self.key_w * 0.6, 150)
            pygame.draw.rect(self.screen, BLACK, rect)

        # 繪製回饋訊息
        fb_surface = self.font_main.render(game.feedback, True, game.feedback_color)
        self.screen.blit(fb_surface, (50, 430))

        pygame.display.flip()

# ==========================================
# 3. 主程式流程
# ==========================================
def main():
    audio = AudioEngine()
    game = GameLogic(SHEET_MUSIC)
    ui = PianoUI(WIDTH, HEIGHT)
    
    # 啟動音訊監聽
    audio.start(game.check_note)
    
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        ui.draw(game, audio.current_note)
        clock.tick(30)

    audio.stop()
    pygame.quit()

if __name__ == "__main__":
    main()