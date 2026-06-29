"""检查调度器仓库的运行状态"""
import json, urllib.request, os

token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
req = urllib.request.Request(
    "https://api.github.com/repos/zhenggongze/daily-news-scheduler/actions/runs?per_page=5",
    headers={"Accept": "application/vnd.github+json", "User-Agent": "python", "Authorization": f"Bearer {token}"},
)
with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read())
    runs = data.get("workflow_runs", [])
    print(f"调度器仓库最近 {len(runs)} 次运行：")
    for run in runs[:5]:
        print(f"  {run['run_number']}#{run['id']} | {run['event']} | {run['status']}/{run.get('conclusion')} | {run['created_at']}")
        # 取 jobs
        req2 = urllib.request.Request(
            f"https://api.github.com/repos/zhenggongze/daily-news-scheduler/actions/runs/{run['id']}/jobs",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "python", "Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(req2, timeout=15) as r2:
            jobs = json.loads(r2.read())
            for job in jobs.get("jobs", []):
                print(f"    job: {job['name']} | {job['status']}/{job.get('conclusion')}")
                for step in job.get("steps", []):
                    print(f"      {step['status']}/{step.get('conclusion')} | {step['name']}")
