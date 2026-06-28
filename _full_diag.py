"""全流程诊断 — 遍历每个环节，定位真正根因"""
import os, json, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
REPO = "zhenggongze/daily-index-news"
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "full-diag",
}

def api(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_msg": e.read().decode()[:300]}

print("=" * 70)
print("  全流程诊断 —", datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S 北京"))
print("=" * 70)

# ============ 1. 仓库基础信息 ============
print("\n[1] 仓库基础信息")
repo = api(f"https://api.github.com/repos/{REPO}")
print(f"  full_name: {repo.get('full_name')}")
print(f"  private: {repo.get('private')}")
print(f"  default_branch: {repo.get('default_branch')}")
print(f"  pushed_at: {repo.get('pushed_at')}")
print(f"  updated_at: {repo.get('updated_at')}")
print(f"  archived: {repo.get('archived')}")
print(f"  disabled: {repo.get('disabled')}")
print(f"  size: {repo.get('size')} KB")

# ============ 2. Actions 权限 ============
print("\n[2] Actions 权限")
perms = api(f"https://api.github.com/repos/{REPO}/actions/permissions")
print(f"  allowed: {perms.get('enabled')}")
print(f"  allowed_actions: {perms.get('allowed_actions')}")
if perms.get("_error"):
    print(f"  ⚠️ {perms}")

# ============ 3. 工作流状态 ============
print("\n[3] 工作流状态")
wfs = api(f"https://api.github.com/repos/{REPO}/actions/workflows")
for wf in wfs.get("workflows", []):
    print(f"  id={wf.get('id')} name={wf.get('name')} state={wf.get('state')} path={wf.get('path')}")
    print(f"    created_at={wf.get('created_at')} updated_at={wf.get('updated_at')}")

# ============ 4. 最近 20 次运行（全部 event）============
print("\n[4] 最近 20 次运行（全部事件类型）")
runs = api(f"https://api.github.com/repos/{REPO}/actions/runs?per_page=20")
for run in runs.get("workflow_runs", []):
    print(f"  #{run['run_number']:3d} | {run['event']:18s} | {run['created_at']} | {run['status']:12s} | {run['conclusion']} | {(run.get('head_commit') or {}).get('message','')[:40]}")

# ============ 5. schedule 触发的运行 ============
print("\n[5] schedule 触发的运行（最近 10 次）")
sched = api(f"https://api.github.com/repos/{REPO}/actions/runs?per_page=10&event=schedule")
sched_list = sched.get("workflow_runs", [])
if not sched_list:
    print("  ⚠️⚠️⚠️ 完全没有 schedule 触发的运行记录！")
else:
    for run in sched_list:
        print(f"  #{run['run_number']:3d} | {run['created_at']} | {run['conclusion']}")

# ============ 6. 当前默认分支的工作流文件 ============
print("\n[6] 默认分支(main)上的工作流文件内容（前30行）")
contents = api(f"https://api.github.com/repos/{REPO}/contents/.github/workflows")
if isinstance(contents, list):
    for c in contents:
        print(f"  - {c.get('name')} ({c.get('path')})")
else:
    print(f"  ⚠️ {contents}")

# ============ 7. 最近一次 commit ============
print("\n[7] 最近一次 commit")
commits = api(f"https://api.github.com/repos/{REPO}/commits?per_page=3")
for c in commits[:3]:
    print(f"  {c['sha'][:7]} | {c['commit']['author']['date']} | {c['commit']['message'][:60]}")

# ============ 8. 远端 OSS 数据日期 ============
print("\n[8] 远端 OSS 数据日期")
try:
    r = urllib.request.urlopen("https://portfolio-analysis.top/news/data/index.json", timeout=15)
    idx = json.loads(r.read())
    print(f"  dates: {idx.get('dates')}")
    print(f"  最新日期: {idx.get('dates', [None])[-1] if idx.get('dates') else None}")
except Exception as e:
    print(f"  ❌ {e}")

# ============ 9. 检查今天的数据文件是否存在 ============
today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
print(f"\n[9] 检查今天({today})的数据文件")
try:
    r = urllib.request.urlopen(f"https://portfolio-analysis.top/news/data/{today}.json", timeout=15)
    d = json.loads(r.read())
    print(f"  ✅ 存在，{d.get('count')} 条新闻")
except urllib.error.HTTPError as e:
    print(f"  ❌ HTTP {e.code} — 今天数据未生成")
except Exception as e:
    print(f"  ❌ {e}")

# ============ 10. GitHub 仓库 scheduled runs 限制文档提示 ============
print("\n[10] GitHub Actions schedule 限制提示")
print("  - 公开仓库 schedule 可被延迟到整点后一小时才运行")
print("  - 高负载时段(整点) schedule 可能被丢弃")
print("  - 私有仓库每月有限额(2000分钟)")
print(f"  - 仓库可见性: {'private' if repo.get('private') else 'public'}")
