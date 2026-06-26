#!/usr/bin/env python3
"""检查 Run #6 状态"""
import json, urllib.request, sys

run_id = sys.argv[1] if len(sys.argv) > 1 else "28209338924"
url = "https://api.github.com/repos/zhenggongze/daily-index-news/actions/runs/" + run_id + "/jobs"
req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "python"})
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read())

for j in data.get("jobs", []):
    print(f"Job: {j['name']} | conclusion: {j.get('conclusion', '?')}")
    for step in j.get("steps", []):
        c = step.get("conclusion") or "pending"
        ic = "X" if c == "failure" else "V" if c == "success" else "-"
        print(f"  {ic} {step['name']:45s} | {c}")
