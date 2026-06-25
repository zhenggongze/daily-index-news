#!/usr/bin/env python3
"""检查 GitHub Actions 最近运行状态"""
import json, urllib.request

req = urllib.request.Request(
    "https://api.github.com/repos/zhenggongze/daily-index-news/actions/runs?per_page=3&branch=main",
    headers={"Accept": "application/vnd.github+json", "User-Agent": "python"}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read())

for r in data.get("workflow_runs", []):
    rid = r["id"]
    c = r.get("conclusion") or "running"
    icon = "✅" if c == "success" else "❌" if c == "failure" else "⏳"
    ht = r["head_commit"]["message"][:60] if r.get("head_commit") else "?"
    print(f"{icon} Run #{r['run_number']} (ID={rid}) | {c} | {r['created_at'][:19]}")
    print(f"   commit: {ht}")

    # Fetch job details
    url2 = f"https://api.github.com/repos/zhenggongze/daily-index-news/actions/runs/{rid}/jobs"
    req2 = urllib.request.Request(url2, headers={"Accept": "application/vnd.github+json", "User-Agent": "python"})
    with urllib.request.urlopen(req2, timeout=15) as resp2:
        jobs = json.loads(resp2.read())
    for j in jobs.get("jobs", []):
        s = j["status"]
        jc = j.get("conclusion") or "..."
        jicon = "✅" if jc == "success" else "❌" if jc == "failure" else "⏳"
        print(f"   {jicon} {j['name']} | {s} | {jc}")
        for step in j.get("steps", []):
            sc = step.get("conclusion") or step["status"]
            sic = "✅" if sc == "success" else "❌" if sc == "failure" else "⏳"
            print(f"       {sic} {step['name'][:50]:50s} | {sc}")
    print()
