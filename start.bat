@echo off
cd /d "%~dp0"

:: Запускаем основные серверы в фоновом режиме
start /B pythonw app_server.py > logs/app_server.log 2>&1
start /B pythonw server.py > logs/server.log 2>&1

:: Запускаем дополнительные компоненты
start /B pythonw scripts/scenario_manager.py > logs/scenario.log 2>&1

:: Запускаем Electron приложение
npx electron .
