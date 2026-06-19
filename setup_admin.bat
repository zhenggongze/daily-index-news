@echo off
cd /d "D:\TRAE SOLO CN\投资指数资讯"
schtasks /delete /tn "Trae每日指数投资资讯" /f >nul 2>&1

schtasks /create /tn "Trae每日指数投资资讯" /tr "D:\TRAE SOLO CN\投资指数资讯\run_daily_report.bat" /sc daily /st 08:00 /f

schtasks /create /tn "Trae每日指数投资资讯-开机补发" /tr "D:\TRAE SOLO CN\投资指数资讯\run_daily_report.bat" /sc onstart /delay 0001:00 /f

echo.
echo ========================================================
echo  OK: 两个任务注册成功
echo ========================================================
echo  1. Trae每日指数投资资讯       每天 08:00 触发
echo  2. Trae每日指数投资资讯-开机补发  电脑开机1分钟后触发
echo.
echo  (开机补发任务由 daily_report.py 内部自动判断是否已推送)
echo.
echo  To remove:
echo    schtasks /delete /tn "Trae每日指数投资资讯" /f
echo    schtasks /delete /tn "Trae每日指数投资资讯-开机补发" /f
pause
