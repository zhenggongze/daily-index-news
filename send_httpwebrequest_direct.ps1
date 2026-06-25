[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$jsonPath = Join-Path $PSScriptRoot "feishu_daily_report.json"
$json = [System.IO.File]::ReadAllText($jsonPath, [System.Text.Encoding]::UTF8)
$bytes = [System.Text.Encoding]::UTF8.GetBytes($json)

$req = [System.Net.HttpWebRequest]::Create("https://open.feishu.cn/open-apis/bot/v2/hook/78352ea0-ceee-4fd9-932b-dafabac15087")
$req.Method = "POST"
$req.ContentType = "application/json"
$req.ContentLength = $bytes.Length
$req.ServicePoint.Expect100Continue = $false

$reqStream = $req.GetRequestStream()
$reqStream.Write($bytes, 0, $bytes.Length)
$reqStream.Close()

try {
    $resp = $req.GetResponse()
    $stream = $resp.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
    $responseBody = $reader.ReadToEnd()
    $reader.Close()
    $stream.Close()
    $resp.Close()
    Write-Output $responseBody
} catch {
    Write-Output "Error: $($_.Exception.Message)"
}