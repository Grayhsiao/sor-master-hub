@echo off
setlocal

:: Check if PyInstaller is installed
echo Checking for PyInstaller...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
) else (
    echo PyInstaller is already installed.
)

:: Check if icon.ico exists, if not, generate it from andy_doll.png
if not exist "icon.ico" (
    echo icon.ico not found. Attempting to generate from andy_doll.png...
    if exist "andy_doll.png" (
        python -c "from PIL import Image; img = Image.open('andy_doll.png'); img.save('icon.ico', format='ICO', sizes=[(256, 256)])"
        if exist "icon.ico" (
            echo Successfully generated icon.ico.
        ) else (
            echo Failed to generate icon.ico. PyInstaller might fail or use default icon.
        )
    ) else (
        echo andy_doll.png not found. Cannot generate icon.ico.
    )
)

:: Run PyInstaller
echo Building SOR_Study_Buddy...
:: Note: --name "SOR_Study_Buddy" automatically creates SOR_Study_Buddy.exe on Windows
pyinstaller --noconsole --onefile --icon=icon.ico --add-data "andy_doll.png;." --name "SOR_Study_Buddy" main.py

if %errorlevel% equ 0 (
    echo.
    echo Build successful! Executable is in the dist folder.
) else (
    echo.
    echo Build failed. Please check the errors above.
)

pause
