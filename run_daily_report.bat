@echo off
cd /d "D:\TRAE SOLO CN\投资指数资讯"
C:\Users\11328817\AppData\Local\Programs\Python\Python312\python.exe daily_report.py > "%TEMP%\daily_report_stdout.log" 2>&1
echo [%DATE% %TIME%] Exit code: %ERRORLEVEL% >> "%TEMP%\daily_report_stdout.log"
copy "%TEMP%\daily_report_stdout.log" "D:\TRAE SOLO CN\投资指数资讯\logs\task_runner.log" /Y >nul
