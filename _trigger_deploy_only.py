"""通过 GitHub API 触发 workflow_dispatch，带 skip_pipeline 参数"""
import json, urllib.request, os

token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
if token:
    data = json.dumps({"ref": "main", "inputs": {"skip_pipeline": True}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/repos/zhenggongze/daily-index-news/actions/workflows/daily_news.yml/dispatches",
        data=data,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "python",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        print(f"触发结果: {resp.status}")
    print("✅ 工作流已触发（skip_pipeline=true）")
else:
    print("⚠️ 未找到 GH_TOKEN 环境变量，无法通过 API 触发")
