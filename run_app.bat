@echo off
chcp 65001 > nul
title LifeCheck (화이트-하늘색 모던 UI)
echo ==============================================
echo       LifeCheck 프로그램을 실행합니다.
echo ==============================================

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python app.py
    goto end
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py app.py
    goto end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" app.py
    goto end
)

echo [오류] Python 실행 파일을 찾을 수 없습니다.
pause

:end
