; Focus Guard Pro Windows 專業安裝腳本
; 使用 Inno Setup 5/6 進行編譯

[Setup]
AppName=Focus Guard Pro
AppVersion=3.0
DefaultDirName={pf}\FocusGuardPro
DefaultGroupName=Focus Guard Pro
OutputDir=.\Output
OutputBaseFilename=FocusGuardPro_Setup
Compression=lzma
SolidCompression=yes
; 廣告位：這張 BMP 會在背景或啟動畫面展示 (請替換為您的 SoR Hub 宣傳圖)
; WizardImageFile=sor_hub_ads.bmp
; WizardSmallImageFile=andy_doll_small.bmp
IconFilename=icon.ico

[Files]
; 打包後的執行檔 (由 PyInstaller 產出)
Source: "dist\FocusGuardPro.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\GuardPro.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "andy_doll.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Focus Guard Pro"; Filename: "{app}\FocusGuardPro.exe"
Name: "{commondesktop}\Focus Guard Pro"; Filename: "{app}\FocusGuardPro.exe"

[Run]
; 安裝後自動啟動主程式
Filename: "{app}\FocusGuardPro.exe"; Description: "立即啟動 Focus Guard Pro"; Flags: nowait postinstall skipifsilent
; 同步啟動影子守護者
Filename: "{app}\GuardPro.exe"; Flags: nowait

[Code]
// 可以在這裡加入更多自定義廣告或導覽邏輯
