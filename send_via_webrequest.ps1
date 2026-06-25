
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
[System.Net.ServicePointManager]::Expect100Continue = $false

$url = Get-Content "d:\TRAE SOLO CN\投资指数资讯\todays_url.txt" -Raw

Write-Host "URL length: $($url.Length)"

$request = [System.Net.WebRequest]::Create($url)
$request.Proxy = $null
$request.Timeout = 30000

try {
    $response = $request.GetResponse()
    $stream = $response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($stream)
    $body = $reader.ReadToEnd()
    $reader.Close()
    $response.Close()
    Write-Host "SUCCESS: $body"
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
}
