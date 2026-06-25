$json = Get-Content "d:/TRAE SOLO CN/投资指数资讯/feishu_payload.json" -Raw
$bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
$request = [System.Net.WebRequest]::CreateHttp("https://open.feishu.cn/open-apis/bot/v2/hook/78352ea0-ceee-4fd9-932b-dafabac15087")
$request.Method = "POST"
$request.ContentType = "application/json"
$request.ContentLength = $bytes.Length
$request.Proxy = $null
$stream = $request.GetRequestStream()
$stream.Write($bytes, 0, $bytes.Length)
$stream.Close()
$response = $request.GetResponse()
$streamReader = New-Object System.IO.StreamReader($response.GetResponseStream())
$responseText = $streamReader.ReadToEnd()
$streamReader.Close()
Write-Host "Status Code:" $response.StatusCode
Write-Host "Response:" $responseText
