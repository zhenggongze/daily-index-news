Add-Type -AssemblyName System.Net.Http
$handler = New-Object System.Net.Http.HttpClientHandler
$handler.Proxy = $null
$client = New-Object System.Net.Http.HttpClient($handler)
$client.Timeout = [TimeSpan]::FromSeconds(30)
$content = New-Object System.Net.Http.StringContent([System.IO.File]::ReadAllText("feishu_daily_report.json"), [System.Text.Encoding]::UTF8, "application/json")
try {
    $result = $client.PostAsync("https://open.feishu.cn/open-apis/bot/v2/hook/78352ea0-ceee-4fd9-932b-dafabac15087", $content)
    $response = $result.Result
    $output = $response.Content.ReadAsStringAsync().Result
    Write-Output $output
} catch {
    Write-Output "Error: $_"
} finally {
    $client.Dispose()
}