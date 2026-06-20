@echo off
cd /d "D:\TRAE SOLO CN\投资指数资讯"
"C:\Users\11328817\AppData\Local\Programs\Python\Python312\python.exe" "D:\TRAE SOLO CN\投资指数资讯\daily_report.py" 1>"D:\TRAE SOLO CN\投资指数资讯\logs\task_runner.log" 2>&1
echo [%DATE% %TIME%] Exit code: %ERRORLEVEL% >> "D:\TRAE SOLO CN\投资指数资讯\logs\task_runner.log"
