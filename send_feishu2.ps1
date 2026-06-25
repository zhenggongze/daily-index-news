$json = Get-Content -Path "D:\TRAE SOLO CN\投资指数资讯\feishu_daily_report.json" -Raw
$url = "https://open.feishu.cn/open-apis/bot/v2/hook/78352ea0-ceee-4fd9-932b-dafabac15087"
$headers = @{"Content-Type" = "application/json"}
Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $json