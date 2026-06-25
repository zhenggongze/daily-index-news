cd "D:\TRAE SOLO CN\投资指数资讯"
python production_pipeline.py
if ($LASTEXITCODE -ne 0) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path "logs\pipeline\pipeline_error.log" -Value "[$ts] 流水线执行失败"
    exit 1
}
