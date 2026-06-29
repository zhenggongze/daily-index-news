"""检查 Run #26 的 jobs 状态"""
import json, urllib.request, os
token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
req = urllib.request.Request(
    "https://api.github.com/repos/zhenggongze/daily-index-news/actions/runs/28355363474/jobs",
    headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}", "User-Agent": "python"},
)
with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read())
    for job in data.get("jobs", []):
        print(f'Job: {job["name"]} | {job["status"]}/{job.get("conclusion")}')
        for step in job.get("steps", []):
            print(f'  Step: {step["name"]} | {step["status"]}/{step.get("conclusion")}')
