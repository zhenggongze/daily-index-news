[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[System.Net.ServicePointManager]::DefaultWebProxy = $null
[System.Net.ServicePointManager]::Expect100Continue = $false

$jsonPath = Join-Path $PSScriptRoot "feishu_daily_report.json"
$json = [System.IO.File]::ReadAllText($jsonPath, [System.Text.Encoding]::UTF8)

$uri = New-Object System.Uri("https://open.feishu.cn/open-apis/bot/v2/hook/78352ea0-ceee-4fd9-932b-dafabac15087")
$request = [System.Net.HttpWebRequest]::CreateHttp($uri)
$request.Method = "POST"
$request.ContentType = "application/json"
$request.Proxy = $null
$request.ServicePoint.Expect100Continue = $false

$bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
$request.ContentLength = $bytes.Length

$stream = $request.GetRequestStream()
$stream.Write($bytes, 0, $bytes.Length)
$stream.Close()

try {
    $response = $request.GetResponse()
    $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
    $result = $reader.ReadToEnd()
    $reader.Close()
    $response.Close()
    Write-Output $result
} catch {
    Write-Output "Error: $($_.Exception.Message)"
}