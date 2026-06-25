$webClient = New-Object System.Net.WebClient
$webClient.Headers.Add("Content-Type", "application/json")
$json = [System.IO.File]::ReadAllText("D:\TRAE SOLO CN\投资指数资讯\feishu_daily_report.json")
$result = $webClient.UploadString("https://open.feishu.cn/open-apis/bot/v2/hook/78352ea0-ceee-4fd9-932b-dafabac15087", "POST", $json)
Write-Output $result