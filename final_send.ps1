[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
try {
    $json = Get-Content "d:\TRAE SOLO CN\投资指数资讯\feishu_payload.json" -Raw -Encoding UTF8
    $headers = @{"Content-Type" = "application/json"}
    $response = Invoke-RestMethod -Uri "https://open.feishu.cn/open-apis/bot/v2/hook/78352ea0-ceee-4fd9-932b-dafabac15087" -Method Post -Headers $headers -Body ([System.Text.Encoding]::UTF8.GetBytes($json)) -ContentType "application/json" -TimeoutSec 30
    Write-Host "SUCCESS!"
    Write-Host $response
} catch {
    Write-Host "FAILED: $_"
}
