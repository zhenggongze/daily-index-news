Add-Type @"
using System;
using System.Net;
using System.IO;
using System.Text;

public class FeishuSender
{
    public static string SendPostRequest(string url, string jsonBody)
    {
        ServicePointManager.UseNagleAlgorithm = false;
        ServicePointManager.Expect100Continue = false;

        HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
        request.Method = "POST";
        request.ContentType = "application/json";
        request.KeepAlive = false;
        request.Proxy = null;

        byte[] data = Encoding.UTF8.GetBytes(jsonBody);
        request.ContentLength = data.Length;

        using (Stream stream = request.GetRequestStream())
        {
            stream.Write(data, 0, data.Length);
        }

        using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
        using (StreamReader reader = new StreamReader(response.GetResponseStream()))
        {
            return reader.ReadToEnd();
        }
    }
}
"@ -ReferencedAssemblies @("System.Net.Http", "System.IO");

$jsonPath = "d:\TRAE SOLO CN\投资指数资讯\feishu_report.json";
$json = [System.IO.File]::ReadAllText($jsonPath);
$result = [FeishuSender]::SendPostRequest("https://open.feishu.cn/open-apis/bot/v2/hook/78352ea0-ceee-4fd9-932b-dafabac15087", $json);
Write-Host $result