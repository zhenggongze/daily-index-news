Add-Type -AssemblyName System
Add-Type -AssemblyName System.IO
Add-Type -AssemblyName System.Net

[System.Net.ServicePointManager]::UseNagleAlgorithm = $false
[System.Net.ServicePointManager]::Expect100Continue = $false

$jsonPath = "d:\TRAE SOLO CN\投资指数资讯\feishu_report.json"
$json = [System.IO.File]::ReadAllText($jsonPath)

$url = "https://open.feishu.cn/open-apis/bot/v2/hook/78352ea0-ceee-4fd9-932b-dafabac15087"
$request = [System.Net.WebRequest]::Create($url)
$request.Method = "POST"
$request.ContentType = "application/json"
$request.KeepAlive = $false

try {
    $proxyProperty = $request.GetType().GetProperty("Proxy", [System.Reflection.BindingFlags]::NonPublic -bor [System.Reflection.BindingFlags]::Instance)
    if ($proxyProperty) {
        $proxyProperty.SetValue($request, $null)
    }
} catch {}

$data = [System.Text.Encoding]::UTF8.GetBytes($json)
$request.ContentLength = $data.Length

$reqStream = $request.GetRequestStream()
$reqStream.Write($data, 0, $data.Length)
$reqStream.Close()

try {
    $response = $request.GetResponse()
    $respStream = $response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($respStream)
    $result = $reader.ReadToEnd()
    $reader.Close()
    $respStream.Close()
    $response.Close()
    Write-Host "Success: $result"
} catch {
    Write-Host "Error: $($_.Exception.Message)"
}