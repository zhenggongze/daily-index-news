
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
$url = Get-Content "$env:TEMP\todays_url.txt" -Raw
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
