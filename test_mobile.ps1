$htmlPath = "d:\TRAE SOLO CN\投资指数资讯\report_mobile.html"
$fileUrl = "file:///" + ($htmlPath -replace '\\', '/')
$edgePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

Write-Host "=== Mobile Design Test ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Opening in Edge with iPhone 14 Plus dimensions (428x926)..." -ForegroundColor Yellow
& $edgePath --window-size=428,926 "$fileUrl"

Write-Host ""
Write-Host "Please also test in browser devtools:" -ForegroundColor Yellow
Write-Host "1. Press F12 to open devtools"
Write-Host "2. Toggle device toolbar (Ctrl+Shift+M)"
Write-Host "3. Select iPhone 14 Plus or set custom to 428x926"
