#!/usr/bin/env python3
"""
GitHub Actions 工作流日志系统 v1
功能：收集步骤日志 → 上传OSS归档 → PushDeer通知
模式：
  --record <step_name> <status> [detail]   记录步骤状态
  --finish <run_id>                         汇总并上报
"""
import os, sys, json, time, hashlib, hmac, base64, uuid
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE, "logs", "workflow")
os.makedirs(LOGS_DIR, exist_ok=True)

PUSHDEER_KEY = os.environ.get("PUSHDEER_KEY", "")
PUSHDEER_URL = "https://api2.pushdeer.com/message/push"

OSS_AK_ID = os.environ.get("OSS_AK_ID", "")
OSS_AK_SECRET = os.environ.get("OSS_AK_SECRET", "")
OSS_BUCKET = "portfolio-analysis-hosting"
OSS_REGION = "oss-cn-hangzhou"


def log_path(run_id):
    return os.path.join(LOGS_DIR, f"{run_id}.jsonl")


def cmd_record():
    """--record <step_name> <status> [detail]"""
    if len(sys.argv) < 4:
        print("用法: workflow_logger.py --record <step_name> <status> [detail]")
        sys.exit(1)
    run_id = os.environ.get("RUN_ID", "unknown")
    step_name = sys.argv[2]
    status = sys.argv[3]
    detail = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""

    record = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_id": run_id,
        "step": step_name,
        "status": status,
        "detail": detail[:1000],
    }
    with open(log_path(run_id), "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"[LOG] {step_name} → {status}")


def upload_to_oss(data, oss_key):
    if not OSS_AK_ID or not OSS_AK_SECRET:
        print("[OSS] 跳过：未配置 OSS_AK_ID/OSS_AK_SECRET")
        return False
    import requests
    url = f"https://{OSS_BUCKET}.{OSS_REGION}.aliyuncs.com/{oss_key}"
    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    md5 = base64.b64encode(hashlib.md5(body).digest()).decode()
    date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    ct = "application/json; charset=utf-8"
    resource = f"/{OSS_BUCKET}/{oss_key}"
    sts = f"PUT\n{md5}\n{ct}\n{date}\n{resource}"
    sig = base64.b64encode(hmac.new(OSS_AK_SECRET.encode(), sts.encode(), hashlib.sha1).digest()).decode()
    headers = {
        "Content-Type": ct, "Content-MD5": md5, "Date": date,
        "Authorization": f"OSS {OSS_AK_ID}:{sig}",
    }
    r = requests.put(url, data=body, headers=headers)
    ok = r.status_code in (200, 201, 204)
    print(f"[OSS] {'✅' if ok else '❌'} news/logs/{oss_key} ({r.status_code})")
    return ok


def push_notification(title, body, success):
    if not PUSHDEER_KEY:
        print("[PUSH] 跳过：未配置 PUSHDEER_KEY")
        return
    import requests
    icon = "✅" if success else "❌"
    text = f"{icon} {title}"
    for attempt in range(1, 4):
        try:
            r = requests.post(PUSHDEER_URL, data={
                "pushkey": PUSHDEER_KEY, "text": text,
                "type": "markdown", "desp": body,
            }, timeout=30)
            j = r.json()
            if j.get("code") == 0:
                print("[PUSH] ✅ 通知发送成功")
                return True
            print(f"[PUSH] 失败({attempt}): {j.get('error', 'unknown')}")
        except Exception as e:
            print(f"[PUSH] 异常({attempt}): {e}")
        if attempt < 3:
            time.sleep(2)
    print("[PUSH] ❌ 通知发送失败（已达最大重试次数）")
    return False


def cmd_finish():
    """--finish <run_id> 汇总并上报"""
    if len(sys.argv) < 3:
        print("用法: workflow_logger.py --finish <run_id>")
        sys.exit(1)
    run_id = sys.argv[2]

    now = datetime.now(timezone.utc)
    records = []
    lp = log_path(run_id)
    if os.path.exists(lp):
        with open(lp, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

    steps = []
    for r in records:
        steps.append({
            "step": r.get("step", "?"),
            "status": r.get("status", "unknown"),
            "detail": r.get("detail", ""),
        })

    success_count = sum(1 for s in steps if s["status"] == "success")
    failure_count = sum(1 for s in steps if s["status"] == "failure")
    final_status = "success" if failure_count == 0 else "failure"

    report = {
        "run_id": run_id,
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "workflow": os.environ.get("GITHUB_WORKFLOW", "AI算力产业链每日资讯"),
        "run_number": os.environ.get("GITHUB_RUN_NUMBER", "?"),
        "repository": os.environ.get("GITHUB_REPOSITORY", ""),
        "branch": os.environ.get("GITHUB_REF", "").replace("refs/heads/", ""),
        "commit": os.environ.get("GITHUB_SHA", "")[:8] if os.environ.get("GITHUB_SHA") else "",
        "final_status": final_status,
        "total_steps": len(steps),
        "success_count": success_count,
        "failure_count": failure_count,
        "steps": steps,
    }

    print("\n" + "=" * 50)
    print(f"  📊 工作流执行报告")
    print(f"  Run ID:     {run_id}")
    print(f"  最终状态:   {'✅ 成功' if final_status == 'success' else '❌ 失败'}")
    print(f"  总步骤:     {len(steps)}")
    print(f"  成功:       {success_count}")
    print(f"  失败:       {failure_count}")
    print("=" * 50 + "\n")

    for s in steps:
        icon = "✅" if s["status"] == "success" else "❌" if s["status"] == "failure" else "⏳"
        print(f"  {icon} {s['step']}")

    oss_key = f"workflow_logs/{run_id}.json"
    upload_to_oss(report, oss_key)

    if failure_count > 0:
        failed = [s for s in steps if s["status"] == "failure"]
        error_detail = "\n".join(f"❌ **{s['step']}**: {s['detail'][:200]}" for s in failed)
        body = (
            f"### ❌ AI算力每日资讯 - 执行失败\n\n"
            f"| 项目 | 值 |\n"
            f"|------|------|\n"
            f"| Run ID | `{run_id}` |\n"
            f"| 总步骤 | {len(steps)} |\n"
            f"| 成功 | {success_count} |\n"
            f"| 失败 | {failure_count} |\n\n"
            f"**失败步骤：**\n{error_detail}\n\n"
            f"📋 详细日志: https://portfolio-analysis.top/news/logs/workflow_logs/{run_id}.json"
        )
    else:
        news_count = "?"
        for r in records:
            if r.get("step") == "运行数据流水线" and r.get("status") == "success":
                d = r.get("detail", "")
                if "条" in d:
                    news_count = d.split("共 ")[-1].split(" 条")[0] if "共 " in d else "?"
        body = (
            f"### ✅ AI算力每日资讯 - 执行成功\n\n"
            f"| 项目 | 值 |\n"
            f"|------|------|\n"
            f"| Run ID | `{run_id}` |\n"
            f"| 新闻数 | {news_count} 条 |\n"
            f"| 步骤数 | {len(steps)} |\n\n"
            f"🌐 访问: https://portfolio-analysis.top/news/index.html"
        )

    push_notification("AI算力每日资讯 工作流报告", body, final_status == "success")

    with open(lp, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    sys.exit(0 if final_status == "success" else 1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"用法: python {sys.argv[0]} --record|--finish ...")
        sys.exit(1)
    mode = sys.argv[1]
    if mode == "--record":
        cmd_record()
    elif mode == "--finish":
        cmd_finish()
    else:
        print(f"未知模式: {mode}")
        sys.exit(1)
