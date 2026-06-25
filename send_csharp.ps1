Add-Type -TypeDefinition @"
using System;
using System.IO;
using System.Net;
using System.Text;

public class FeishuSender
{
    public static string Send(string url, string jsonFilePath)
    {
        try
        {
            string json = File.ReadAllText(jsonFilePath, Encoding.UTF8);
            byte[] data = Encoding.UTF8.GetBytes(json);
            
            ServicePointManager.ServerCertificateValidationCallback = (s, certificate, chain, sslPolicyErrors) => true;
            
            HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
            request.Method = "POST";
            request.ContentType = "application/json";
            request.ContentLength = data.Length;
            request.ServicePoint.Expect100Continue = false;
            
            using (Stream stream = request.GetRequestStream())
            {
                stream.Write(data, 0, data.Length);
            }
            
            using (WebResponse response = request.GetResponse())
            using (StreamReader reader = new StreamReader(response.GetResponseStream()))
            {
                return reader.ReadToEnd();
            }
        }
        catch (Exception ex)
        {
            return "Error: " + ex.Message;
        }
    }
}
"@

$jsonPath = Join-Path $PSScriptRoot "feishu_daily_report.json"
$result = [FeishuSender]::Send("https://open.feishu.cn/open-apis/bot/v2/hook/78352ea0-ceee-4fd9-932b-dafabac15087", $jsonPath)
Write-Output $result