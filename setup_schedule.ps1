[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$taskName = "Trae每日指数投资资讯"
$batPath = "D:\TRAE SOLO CN\投资指数资讯\run_daily_report.bat"

# Remove if exists
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batPath`"" -WorkingDirectory "D:\TRAE SOLO CN\投资指数资讯"
$trigger = New-ScheduledTaskTrigger -Daily -At "08:00"
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Trae每日指数投资资讯" -Force

Write-Host ""
Write-Host "OK: Task '$taskName' registered, runs daily at 08:00"
Write-Host "To remove: Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
