@echo off
title Smart Grid AI — Stop
color 0C

echo.
echo  Stopping Smart Grid AI...
echo.

docker-compose down 2>nul

echo  Smart Grid AI stopped.
echo.
timeout /t 2 /nobreak >nul
