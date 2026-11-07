@echo off
title PARAR AI BRASIL CHAT
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8580" ^| findstr "LISTENING"') do (
    echo Encerrando PID %%a (porta 8580 - AI BRASIL CHAT)...
    taskkill /f /pid %%a
)
echo AI BRASIL CHAT parado.
pause
