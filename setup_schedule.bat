@echo off
cd /d "D:\TRAE SOLO CN\投资指数资讯"
schtasks /create /tn "Trae每日指数投资资讯" /tr "cmd.exe /c \"D:\TRAE SOLO CN\投资指数资讯\run_daily_report.bat\"" /sc daily /st 08:00 /f
echo.
echo Done. Task created: Trae每日指数投资资讯
echo Runs daily at 08:00
echo.
echo To remove: schtasks /delete /tn "Trae每日指数投资资讯" /f
echo To run now: schtasks /run /tn "Trae每日指数投资资讯"
pause
