@echo off
chcp 65001 > nul
title LifeCheck 실행기
echo ==============================================
echo       LifeCheck 프로그램을 실행합니다.
echo ==============================================

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python main.py
    goto end
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py main.py
    goto end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" main.py
    goto end
)

echo [오류] Python 실행 파일을 찾을 수 없습니다.
pause

:end
