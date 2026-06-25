Add-Type -AssemblyName System.Net.Http
$client = New-Object System.Net.Http.HttpClient
$client.Timeout = [System.TimeSpan]::FromSeconds(30)
$jsonText = [System.IO.File]::ReadAllText("feishu_daily_report.json")
$content = New-Object System.Net.Http.StringContent($jsonText, [System.Text.Encoding]::UTF8, "application/json")
try {
    $response = $client.PostAsync("https://open.feishu.cn/open-apis/bot/v2/hook/78352ea0-ceee-4fd9-932b-dafabac15087", $content).Result
    $output = $response.Content.ReadAsStringAsync().Result
    Write-Output $output
} catch {
    Write-Output "Error: $_"
} finally {
    $client.Dispose()
}