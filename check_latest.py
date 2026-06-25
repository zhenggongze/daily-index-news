import os
import requests, json
TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO = 'zhenggongze/daily-index-news'
headers = {'Authorization': f'token {TOKEN}'}

# 获取最新的run
resp = requests.get(f'https://api.github.com/repos/{REPO}/actions/runs?per_page=1', headers=headers)
run = resp.json()['workflow_runs'][0]
run_id = run['id']
print(f'Latest run #{run["run_number"]}: conclusion={run["conclusion"]}')

# 获取job logs
resp2 = requests.get(f'https://api.github.com/repos/{REPO}/actions/runs/{run_id}/jobs', headers=headers)
job_id = resp2.json()['jobs'][0]['id']

resp3 = requests.get(f'https://api.github.com/repos/{REPO}/actions/jobs/{job_id}/logs', headers=headers)
logs = resp3.text

# 找INFO日志（含中文）
seen = set()
for line in logs.split('\n'):
    if '[INFO]' in line:
        cleaned = line.split('[INFO] ')[-1].strip() if '[INFO] ' in line else line
        if cleaned not in seen:
            seen.add(cleaned)
            print(cleaned)
