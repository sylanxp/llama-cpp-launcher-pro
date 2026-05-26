@echo off
chcp 65001 >nul
echo ==============================================
echo  Llama.cpp Launcher Pro - 一键打包脚本
echo ==============================================
echo.

REM 检查 PyInstaller 是否已安装
python -m pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] 正在安装 PyInstaller...
    python -m pip install pyinstaller
)

echo [*] 正在打包，请稍候...
python -m PyInstaller --noconfirm --onefile --windowed ^
    --name "Llama.cpp-Launcher-Pro" ^
    --add-data "core;core" ^
    --add-data "ui;ui" ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtWidgets ^
    --hidden-import PySide6.QtGui ^
    main.py

if %errorlevel% equ 0 (
    echo.
    echo ==============================================
    echo  ✅ 打包成功！
    echo  输出路径: dist\Llama.cpp-Launcher-Pro.exe
    echo ==============================================
) else (
    echo.
    echo  ❌ 打包失败，请检查错误信息。
)

pause