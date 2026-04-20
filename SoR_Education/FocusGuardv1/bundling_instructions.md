# 如何將 FocusGuard 打包成執行檔 (Mac 與 Windows)

本指南說明如何將您的 Python 程式碼 (`main.py`) 轉換為無需按照 Pyhon 即可執行的獨立應用程式。

## 事前準備

1.  **安裝 Python**: 確保您的電腦上已安裝 Python。
2.  **安裝必要套件**:
    開啟終端機 (Terminal) 或命令提示字元 (Command Prompt)，執行以下指令：
    ```bash
    pip install -r requirements.txt
    pip install pyinstaller
    ```
    *(備註：因應您的需求，我們只安裝運作與打包所必需的套件)*

## 建立執行檔

### 在 Windows 上

1.  開啟命令提示字元 (cmd) 或 PowerShell。
2.  移動到專案資料夾：
    ```bash
    cd "path\to\FocusGuard"
    ```
3.  執行打包指令：
    ```bash
    pyinstaller --noconfirm --onefile --windowed --name "FocusGuard" main.py
    ```
    *   `--onefile`: 將所有檔案打包成單一 `.exe` 檔。
    *   `--windowed`: 隱藏黑色的主控台視窗。

4.  **尋找應用程式**:
    前往專案目錄下的 `dist` 資料夾，您會看到 `FocusGuard.exe`。這就是可以分享給其他家長的檔案。

### 在 macOS 上

1.  開啟終端機 (Terminal)。
2.  移動到專案資料夾：
    ```bash
    cd "/Users/gray/Documents/python project/FocusGuard"
    ```
3.  執行打包指令：
    ```bash
    pyinstaller --noconfirm --onefile --windowed --name "FocusGuard" main.py
    ```
    *   注意：在 macOS 上，這會在 `dist` 資料夾中產生一個 UNIX 執行檔，通常也會產生一個 `.app` 應用程式 (視 PyInstaller 版本而定)。
    *   請尋找 `dist/FocusGuard.app` 或 `dist/FocusGuard`。

4.  **權限說明**:
    FocusGuard 需要權限才能偵測並關閉其他程式。第一次在 Mac 上執行時，系統可能會要求 **輔助使用 (Accessibility)** 或 **自動化 (Automation)** 權限。請務必允許，否則封鎖功能將無法運作。

## 疑難排解

-   **"存取被拒" (Access Denied)**:
    在 Windows 上，若要關閉某些系統層級程式，可能需要「以管理員身分執行」。
    在 Mac 上，請確保已在 `系統設定 > 隱私權與安全性 > 自動化` 或 `輔助使用` 中允許此程式。

-   **防毒軟體誤判**:
    有些防毒軟體可能會將 PyInstaller 產生的 `.exe` 檔誤判為可疑檔案，因為它沒有數位簽章。這是正常現象 (False Positive)，您可以暫時加入例外清單。
