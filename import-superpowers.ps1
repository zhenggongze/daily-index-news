$src = "d:\TRAE SOLO CN\投资指数资讯\skills\superpowers"
$dst = "C:\Users\11328817\.trae-cn\builtin\code\default\skills"

Write-Host "正在导入 Superpowers 技能到 SOLO..." -ForegroundColor Green
Copy-Item -Path "$src\*" -Destination $dst -Recurse -Force
Write-Host "导入完成！" -ForegroundColor Green

Write-Host "`n已导入的技能:" -ForegroundColor Yellow
Get-ChildItem $dst | Where-Object { $_.PSIsContainer } | ForEach-Object { Write-Host "  - $($_.Name)" }

Write-Host "`n按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")