@echo off
cd /d "D:\TRAE SOLO CN\投资指数资讯"

:: ========== 自修复：检查08:00任务是否存在，丢失则重建 ==========
schtasks /query /tn "Trae每日指数投资资讯" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [%DATE% %TIME%] 任务丢失，正在重建...
    schtasks /create /tn "Trae每日指数投资资讯" /tr "C:\Users\11328817\AppData\Local\Programs\Python\Python312\python.exe \"D:\TRAE SOLO CN\投资指数资讯\daily_report.py\"" /sc daily /st 08:00 /f >> "logs\self_heal.log" 2>&1
    echo [%DATE% %TIME%] 任务重建完成 >> "logs\self_heal.log"
)

:: ========== 运行日报 ==========
"C:\Users\11328817\AppData\Local\Programs\Python\Python312\python.exe" "D:\TRAE SOLO CN\投资指数资讯\daily_report.py" 1>"D:\TRAE SOLO CN\投资指数资讯\logs\task_runner.log" 2>&1
echo [%DATE% %TIME%] Exit code: %ERRORLEVEL% >> "D:\TRAE SOLO CN\投资指数资讯\logs\task_runner.log"
