$REPORTS_DIR = "d:\TRAE SOLO CN\投资指数资讯\reports"
$ONEDRIVE_DIR = "C:\Users\11328817\OneDrive\InvestmentReports"

if (-not (Test-Path $ONEDRIVE_DIR)) { New-Item -ItemType Directory -Path $ONEDRIVE_DIR -Force | Out-Null }

$today = Get-Date -Format "yyyy-MM-dd"
$todayReport = Join-Path $REPORTS_DIR "report_$today.html"

if (Test-Path $todayReport) {
    # 同步到OneDrive（手机端可访问）
    Copy-Item $todayReport $ONEDRIVE_DIR -Force
    Start-Process $todayReport
} else {
    $latest = Get-ChildItem $REPORTS_DIR -Filter "report_*.html" | Sort-Object Name -Descending | Select-Object -First 1
    if ($latest) {
        Copy-Item $latest.FullName $ONEDRIVE_DIR -Force
        $dateStr = $latest.Name -replace "report_", "" -replace "\.html", ""
        $wshell = New-Object -ComObject Wscript.Shell
        $null = $wshell.Popup("郑公泽指数日报 - $dateStr`n`n今日($today)报告尚未生成，将打开最近一期`n已同步到OneDrive/InvestmentReports", 0, "每日指数日报", 0x40)
        Start-Process $latest.FullName
    } else {
        $wshell = New-Object -ComObject Wscript.Shell
        $null = $wshell.Popup("郑公泽指数日报`n`n暂无任何报告文件，请检查SOLO是否正常运行。", 0, "每日指数日报", 0x30)
    }
}
