$jsonString = Get-Content -Path "feishu_daily_report.json" -Raw
$bytes = [System.Text.Encoding]::UTF8.GetBytes($jsonString)
$body = [System.Convert]::ToBase64String($bytes)
$decoded = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($body))
$url = "https://open.feishu.cn/open-apis/bot/v2/hook/78352ea0-ceee-4fd9-932b-dafabac15087"
try {
    $result = Invoke-WebRequest -Uri $url -Method Post -ContentType "application/json" -Body $decoded -Proxy $null -ProxyUseDefaultCredentials -TimeoutSec 30
    Write-Output $result.Content
} catch {
    Write-Output "Error: $_"
}